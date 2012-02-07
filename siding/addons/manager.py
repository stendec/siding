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
This module contains the core of the add-ons system. It handles discovery,
dependencies, loading, keeping track of available add-ons, and querying the
system to get an :class:`AddonInfo` instance.
"""

###############################################################################
# Imports
###############################################################################

from PySide.QtCore import QObject, Signal, Slot

from siding.addons.base import AddonInfo
from siding import path

###############################################################################
# Log
###############################################################################

import logging
log = logging.getLogger('siding.addons')

###############################################################################
# The Add-on Manager
###############################################################################

class AddonManager(QObject):
    """
    This class is in charge of the entire add-on system. It discovers add-ons,
    handles dependencies and inheritance, loads add-ons, stores references to
    all the loaded add-ons, and allows you to easily fetch an add-on's info
    instance if you know its type and name.
    """
    pass

# Now, instance the manager.
manager = AddonManager()