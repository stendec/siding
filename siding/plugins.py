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
TODO: Write this docstring.
"""

###############################################################################
# Imports
###############################################################################

import argparse

from siding.addons import action, AddonInfo

###############################################################################
# Initialization
###############################################################################

def initialize(args=None, **kwargs):
    """
    Initialize the plugin system. You may use the following arguments to
    configure the plugin system:

    ==============  ==============  ============
    Argument        Default         Description
    ==============  ==============  ============
    nothing         to see          here
    ==============  ==============  ============

    In addition, you can provide a list of command line arguments to have
    siding load them automatically. Example::

        siding.plugins.initialize(sys.argv[1:])

    The following command line arguments are supported:

    ==================  ============
    Argument            Description
    ==================  ============
    ``--safe-mode``     When safe mode is enabled, add-ons, including styles, won't be loaded automatically.
    ``--plugin-path``   Add the given path to the plugin search paths. This may be used more than once.
    ==================  ============
    """
    pass
