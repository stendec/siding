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
A flexible add-ons system that's easy to extend with new types of add-ons,
provides a nice pre-built user interface for use in your applications, and that
has an easy-to-customize in-app update system.
"""

###############################################################################
# Imports
###############################################################################

from siding.addons.base import action, AddonInfo

safe_mode = False

###############################################################################
# Exports
###############################################################################

__all__ = [
    action,  # Decorators

    AddonInfo,  # Classes
]
