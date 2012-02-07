###############################################################################
#
# Copyright 2012 Siding Developers (see AUTHORS.txt)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
"""
A profile system that provides both a :class:`PySide.QtCore.QSettings` instance
for storing and retrieving settings values, as well as functions for
determining file locations between the profile directory and the application
root.
"""

###############################################################################
# Imports
###############################################################################

import os
import argparse
import sys

from PySide.QtCore import QCoreApplication, QSettings
from PySide.QtGui import QDesktopServices

from siding import path

###############################################################################
# Logging
###############################################################################

import logging
log = logging.getLogger("siding.profile")

###############################################################################
# Constants and Storage
###############################################################################

name = 'default'
settings = None

portable = False

profile_path = None
root_path = None

###############################################################################
# Internal Functions
###############################################################################

def assert_profile():
    """ Raise an exception if a profile hasn't been loaded. """
    if settings is None:
        raise RuntimeError("A profile hasn't been loaded.")

def ensure_paths():
    """ Ensure profile_path is set, and that it's registered with path. """
    global profile_path
    global root_path

    # If we don't have root path, don't worry about it.
    if not root_path:
        root_path = path.root()
        path.add_source(root_path)

    # If we don't have profile_path, make it.
    if not profile_path:
        if portable:
            profile_path = root_path
        else:
            profile_path = path.appdata()

        # Add the "Profiles/<profile>" bit to the profile path and ensure it
        # exists.
        profile_path = os.path.join(profile_path, 'Profiles', name)
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)

        path.add_source(profile_path)

###############################################################################
# Settings Getters / Setters
###############################################################################

def contains(key):
    """
    Returns true if key exists in the loaded profile, or false if it does not.
    """
    assert_profile()
    return settings.contains(key)


def keys():
    """ Return a list of all the keys in the loaded profile. """
    assert_profile()
    return settings.allKeys()


def set(key, value):
    """
    Sets the value of key to value in the loaded profile. If the key already
    exists, the existing value is overwritten.
    """
    assert_profile()
    settings.setValue(key, value)


def get(key, default=None):
    """
    Returns the value of key in the loaded profile. If the key doesn't exist,
    the provided default will be returned.
    """
    assert_profile()
    return settings.value(key, default)


def remove(key):
    """ Delete the key from the loaded profile. """
    assert_profile()
    settings.remove(key)

###############################################################################
# Initialization
###############################################################################

def initialize(args=None, **kwargs):
    """
    Initialize the profile system. You may use the following arguments to
    configure the profile system:

    =============  ============  ============
    Argument       Default       Description
    =============  ============  ============
    portable       ``False``     If True, the profile system will create a profile path within the root folder, allowing the application to work as a portable app.
    profile        ``default``   The name of the profile to load.
    sources        ``[]``        A list of additional sources for the path system to use.
    profile_path                 Load the profile from this path.
    root_path                    The application root directory. This is always the last path to be checked by the path system.
    =============  ============  ============

    .. warning::
        ``root_path`` will *probably* not work as expected after your
        application is frozen into an executable, so be sure to test that it's
        working properly before distributing your application.

    In addition, you can provide a list of command line arguments to have
    siding load them automatically. Example::

        siding.profile.initialize(sys.argv[1:])

    The following command line arguments are supported:

    ===================  ============
    Argument             Description
    ===================  ============
    ``--portable``       If True, the profile system will create a profile path within the root folder, allowing the application to work as a portable app.
    ``--profile``        The name of the profile to load.
    ``--profile-path``   The path to load the profile from.
    ``--root-path``      The application root directory.
    ``--source``         An additional source for the path system. This can be used multiple times.
    ===================  ============
    """
    global name
    global portable
    global profile_path
    global root_path
    global settings

    # Set the defaults now.
    portable = kwargs.get('portable', False)
    name = kwargs.get('profile', 'default')

    # And load the paths if we've got them.
    root_path = kwargs.get('root_path', root_path)
    profile_path = kwargs.get('profile_path', profile_path)

    # Get the source list.
    sources = kwargs.get('sources', [])

    # Now, parse the options we've got.
    if args:
        if args is True:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--portable', action='store_true', default=None)
        parser.add_argument('--profile')
        parser.add_argument('--profile-path')
        parser.add_argument('--root-path')
        parser.add_argument('--source', action='append')

        options = parser.parse_known_args(args)[0]

        # Let's set stuff up then.
        if options.portable is not None:
            portable = options.portable

        if options.profile:
            name = options.profile

        if options.profile_path:
            profile_path = options.profile_path
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)

        if options.root_path:
            root_path = options.root_path
            if not os.path.exists(root_path):
                parser.error("The specified root path doesn't exist.")

        if options.source:
            for source in options.source:
                if not source in sources:
                    if not os.path.exists(source):
                        parser.error("The source %r doesn't exist." % source)
                    sources.append(source)

    # Now, do the path stuff.
    for source in sources:
        path.add_source(source)

    # Do we already have our paths?
    if profile_path or root_path:
        path.add_source(profile_path)

    # Make sure.
    ensure_paths()

    # Now, open the settings file with QSettings and we're done.
    file = os.path.join(profile_path, 'settings.ini')
    settings = QSettings(file, QSettings.IniFormat)

    log.info(u'Using profile: %s (%s)' % (name, profile_path))
    log.debug(u'settings.ini contains %d keys across %d groups.' % (
        len(settings.allKeys()), len(settings.childGroups())))
