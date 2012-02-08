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
siding is a lightweight framework to assist in the creation of PySide
applications with support for multiple-instance detection, multiple profiles,
easy to use styles, and a flexible plugins system.
"""

###############################################################################
# Imports
###############################################################################

import logging

from siding import addons, path, profile
from siding import style, plugins
from siding.singleinstance import QSingleApplication

from siding import qss

###############################################################################
# Exports
###############################################################################

__authors__ = ["Stendec"]
__version__ = "0.1.0"

__all__ = [
    "__authors__", "__version__",  # Metadata

    addons, path, profile,  # Modules

    style,  # Secondary Modules

    QSingleApplication,  # Classes
    ]

###############################################################################
# Logging
###############################################################################

logging.getLogger("siding").addHandler(logging.NullHandler())

###############################################################################
# Initialize
###############################################################################

def initialize(organization_name=None, application_name=None, version=None):
    """
    If you're feeling particularly lazy, this function will handle all the
    initialization for you and return a :class:`QSingleApplication` instance.
    """

    # Make the app.
    app = QSingleApplication()

    # Store our info.
    if organization_name:
        app.setOrganizationName(organization_name)
    if application_name:
        app.setApplicationName(application_name)
    if version:
        app.setApplicationVersion(version)
    
    # Do the initialization.
    profile.initialize(True)
    app.ensure_single()
    plugins.initialize(True)
    style.initialize(True)

    return app
