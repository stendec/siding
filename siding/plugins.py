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
import functools
import inspect
import sys

from PySide.QtCore import QObject, Signal
import imp

from siding import addons

###############################################################################
# Logging
###############################################################################

import logging
log = logging.getLogger('siding.plugins')

###############################################################################
# Internal Helper Functions
###############################################################################

def issignal(signal):
    """ Return True if signal is an instance of QtCore.Signal. """
    return isinstance(signal, Signal)

###############################################################################
# Plugin Interface
###############################################################################

class IPlugin(QObject):
    """
    The most basic plugin interface to be inherited. This class is a subclass
    of :class:`PySide.QtCore.QObject`, and interacts with the rest of the
    application via Slots and Signals.

    Simply define slots and signals in subclasses of IPlugin, and they will
    be automatically connected and disconnected when the plugin is enabled or
    disabled. As a simple example::

        from PySide.QtCore import Signal, Slot
        from siding.plugins import IPlugin

        class Communicate(IPlugin):
            speak = Signal(str)

            @Slot()
            def triggered(self):
                self.speak.emit('Hello, everybody!')

    """

    def __init__(self, manager, info):
        """ Perform minimal plugin initialization. """
        QObject.__init__(self)

        self._manager = manager
        self._info = info
        self._name = info.name
        self._is_active = False

    ##### Plugin Information ##################################################

    @property
    def manager(self):
        """ The :class:`PluginManager` controlling this plugin instance. """
        return self._manager

    @property
    def info(self):
        """ The :class:`PluginInfo` instance representing this plugin. """
        return self._info

    @property
    def name(self):
        """ The plugin's name. """
        return self._name

    ##### Plugin Activation ###################################################

    @property
    def is_active(self):
        """
        Whether or not the plugin is currently active.

        This property performs the brunt of the work involved in activating or
        deactivating a plugin, and changing the value os ``is_active`` is all
        you have to do to activate or deactivate a plugin.

        Internally, the change ensures that other plugins as necessary are
        activated or deactivated, that the plugin's signals and slots are
        connected or disconnected, and that the plugin manager is notified of
        the change.
        """
        return self._is_active

    @is_active.setter
    def is_active(self, val):
        """ Enable or disable the plugin. """
        val = bool(val)
        if val == self._is_active:
            return

        # Don't set _is_active just yet.
        if val:
            # Check our dependencies first.
            addons.check_dependencies(self._info)

            # Make sure those dependencies are loaded.
            self._activate_dependencies()

            # Connect our signals.
            self._connect_signals()

            # Finally, set ourselves active and update any UI elements for
            # this plugin.
            self._is_active = True
            self._info.update_ui()

            log.info('Activated plugin %r.' % self._info.data['name'])

        else:
            # If we're already on, we can assume we don't need to check our
            # dependencies. We *do* have to deactivate the plugins that depend
            # on us though.
            self._deactivate_dependants()

            # Disconnect the signals and slots.
            self._disconnect_signals()

            # And finally, set us as inactive and update UI.
            self._is_active = False
            self._info.update_ui()

            log.info('Deactivated plugin %r.' % self._info.data['name'])

    ##### Activation Helpers ##################################################

    def _activate_dependencies(self):
        """ Make sure all our dependencies are active. """
        for name in self._info.requires.iterkeys():
            if name == '__app__' or (':' in name and not
                    name.startswith('plugin:')):
                continue
            dep = addons.get('plugin', name)

            # Make sure we're needed.
            if not self._name in dep.needed_by:
                dep.needed_by.append(self._name)

            # If it's active, just continue.
            if dep.is_active:
                continue

            # Not active? Make sure it's loaded.
            if not dep.is_loaded:
                dep.load()

            # Now activate it.
            dep.plugin.activate()

    def _deactivate_dependants(self):
        """ Make sure all our dependants are deactivated. """
        for name in self._info.needed_by:
            dep = addons.get('plugin', name)
            if not dep.is_active:
                continue
            dep.plugin.deactivate()

    def _connect_signals(self):
        """ Connect to all the available slots and signals. """
        for signame in self._manager._signals:
            slot = getattr(self, signame, None)
            if not slot or not hasattr(slot, '_slots'):
                continue

            for signal in self._manager._signals[signame]:
                signal.connect(slot)

        for signame in self._manager._slots:
            signal = getattr(self, signame, None)
            if not signal or not isinstance(signal, Signal):
                continue

            for slot in self._manager._slots[signame]:
                signal.connect(slot)

    def _disconnect_signals(self):
        """ Disconnect all of our signals and slots. """
        for signame in self._manager._signals:
            slot = getattr(self, signame, None)
            if not slot or not hasattr(slot, '_slots'):
                continue

            for signal in self._manager._signals[signame]:
                signal.disconnect(slot)

        for signame in self._manager._slots:
            signal = getattr(self, signame, None)
            if not signal or not isinstance(signal, Signal):
                continue

            for slot in self._manager._slots[signame]:
                signal.disconnect(slot)

    ##### Public Methods ######################################################

    def activate(self):
        """
        Activate the plugin. By default, this merely sets :attr:`is_active` to
        True.
        """
        self.is_active = True

    def deactivate(self):
        """
        Deactivate the plugin. By default, this merely sets :attr:`is_active`
        to False.
        """
        self.is_active = False

###############################################################################
# PluginInfo Class
###############################################################################

class PluginInfo(addons.AddonInfo):
    """
    This class stores all the information for any given plugin, references to
    the plugins, and actions to make working with plugins easy for the end
    user.
    """

    CORE_VALUES = ('module',)

    # Defaults
    module = None
    _plugin = None

    ##### Properties ##########################################################

    @property
    def plugin(self):
        """
        Returns the plugin this :class:`PluginInfo` represents, or None if the
        plugin isn't yet loaded.
        """
        return self._plugin

    @property
    def is_loaded(self):
        """ Whether or not the plugin has been loaded. """
        return self._plugin is not None

    @property
    def is_active(self):
        """ Whether or not the plugin is currently active. """
        return getattr(self._plugin, 'is_active', False)

    ##### Actions #############################################################

    @addons.action('&Options', default=True)
    def options(self):
        """ Display the plugin's options dialog. """
        self.configure()

    @options.is_enabled
    def is_enabled(self):
        return hasattr(self._plugin, 'configure')

    @addons.action("&Enable", checkable=True)
    def enable(self):
        """ Enable or disable the plugin. """
        # TODO: Make this do stuff.
        pass

    @enable.is_checked
    def is_checked(self):
        if self.is_active:
            self.enable.text = '&Disable'
            return True
        else:
            self.enable.text = '&Enable'
            return False

    ##### Plugin Loading ######################################################

    def load(self, ignore_blacklist=False):
        """ Attempt to load the plugin we represent. """
        if self.is_loaded:
            log.warning('Trying to load already loaded plugin %r.' %
                        self.data['name'])
            return

        if not ignore_blacklist and self.is_blacklisted:
            raise addons.DependencyError('Plugin %r is blacklisted.' % 
                                         self.data['name'])

        # Check our dependencies for safety.
        addons.check_dependencies(self)

        # Load our dependencies.
        for name in self.requires.iterkeys():
            if name == '__app__' or (':' in name and not
                    name.startswith('plugin:')):
                continue
            dep = addons.get('plugin', name)

            # Make sure we're needed.
            if not self.name in dep.needed_by:
                dep.needed_by.append(self.name)

            # If it's loaded, just continue.
            if dep.is_loaded:
                continue
            dep.load()

        # Okay, now load!
        self._do_load()

    def _do_load(self):
        """ Find our module and load it. """
        # Figure out what to load.
        modname = self.module if self.module else self.name

        # Depending on whether our source is using ``pkg_resources`` or not,
        # fork here.
        if (isinstance(self.path_source, basestring) and not
                self.path_source.startswith('py:')):
            # It's a filesystem. Just do things the easy way.
            path = self.path.abspath('.')
            file = None
            try:
                file, pathname, description = imp.find_module(modname, [path])
                module = imp.load_module(modname, file, pathname, description)
            finally:
                if file:
                    file.close()

        else:
            # TODO: Fancy, pkg_resource importer code here.
            # Until then, a copy paste of the previous!
            path = self.path.abspath('.')
            file = None
            try:
                file, pathname, description = imp.find_module(modname, [path])
                module = imp.load_module(modname, file, pathname, description)
            finally:
                if file:
                    file.close()

        # We've got a module! Now, what to do with it? Store its plugin, of
        # course! Find the first IPlugin subclass and instance it.
        for key in dir(module):
            val = getattr(module, key)
            if inspect.isclass(val) and issubclass(val, IPlugin):
                try:
                    self._plugin = val(manager, self)
                    break
                except Exception:
                    log.exception('Unable to instance plugin %r.' %
                                  self.data['name'])
                    raise ImportError
        else:
            log.exception('Cannot find subclass of IPlugin in plugin %r.' %
                          self.data['name'])
            raise ImportError

        # Log how happy we are.
        log.info('Loaded plugin %r.' % self.data['name'])

# Registration
addons.add_type(
    'plugin',
    PluginInfo,
    search_paths=['plugins'],
    text="Plugins",
    icon='plugins'
)

###############################################################################
# PluginManager Class
###############################################################################

class PluginManager(object):
    """
    This class handles the loading of plugins, as well as the connection of
    signals and slots between the plugins and the rest of the application.
    """

    def __init__(self):
        # Storage
        self._signals = {}
        self._slots = {}

    def add_signal(self, name, signal):
        """
        Register a new signal with the plugin manager. All active plugins with
        slots matching the given name will be automatically connected to the
        signal.

        Additionally, this function returns a method that, when called, will
        remove the signal from the system.
        """
        if not name in self._signals:
            self._signals[name] = []

        # Build the remover.
        remover = functools.partial(self.remove_signal, name, signal)

        # If we already have it, just return now.
        if signal in self._signals[name]:
            return remover

        # Store the signal in the list.
        self._signals[name].append(signal)

        # Now, iterate through our plugins and connect the signal to every
        # plugin that's currently active.
        for info in addons.find('plugin', lambda info: info.is_active):
            slot = getattr(info.plugin, name, None)
            if not hasattr(slot, '_slots'):
                continue
            signal.connect(slot)

        return remover

    def run_signal(self, name, *args):
        """
        Process a signal immediately with all active plugins with slots
        matching the given name. Any provided arguments will be sent along
        to those slots.
        """
        for info in addons.find('plugin', lambda info: info.is_active):
            slot = getattr(info.plugin, name, None)
            if not hasattr(slot, '_slots'):
                continue
            try:
                slot(*args)
            except Exception:
                log.exception('Error running signal through plugin %r.' %
                              info.data['name'])

    def remove_signal(self, name, signal=None):
        """
        Remove a signal from the plugin manager and disconnect it from any
        plugins currently connected to it.

        If no ``signal`` is provided, *all* signals with the given name will be
        disconnected and removed from the plugin manager.
        """
        if (not name in self._signals or
            (signal and not signal in self._signals[name])):
            return

        if isinstance(signal, (list, tuple)):
            signals = signal
        else:
            signals = [signal] if signal else self._signals[name].itervalues()

        for signal in signals:
            self._signals[name].remove(signal)
            for info in addons.find('plugin', lambda info: info.is_active):
                slot = getattr(info.plugin, name, None)
                if not hasattr(slot, '_slots'):
                    continue
                signal.disconnect(slot)

    def add_slot(self, name, slot):
        """
        Register a new slot with the plugin manager. All active plugins with
        signals matching the given name will be automatically connected to
        the slot.

        Additionally, this function returns a method that, when called, will
        remove the slot from the system.
        """
        if not name in self._slots:
            self._slots[name] = []

        # Build the remover.
        remover = functools.partial(self.remove_slot, name, slot)

        if slot in self._slots[name]:
            return remover
        self._slots[name].append(slot)

        # Now, iterate through our plugins and connect the slot to every
        # plugin that's currently active.
        for info in addons.find('plugin', lambda info: info.is_active):
            signal = getattr(info.plugin, name, None)
            if not isinstance(signal, Signal):
                continue
            signal.connect(slot)

        return remover

    def remove_slot(self, name, slot=None):
        """
        Remove a slot from the plugin manager and disconnect it from any
        plugins currently connected to it.

        If no ``slot`` is provided, *all* slots with the given name will be
        disconnected and removed from the plugin manager.
        """
        log.debug("remove_slot(%r, %r)" % (name, slot))

        if (not name in self._slots or
            (slot and not slot in self._slots[name])):
            return

        if isinstance(slot, (tuple,list)):
            slots = slot
        else:
            slots = [slot] if slot else self._slots[name].itervalues()

        for slot in slots:
            self._slots[name].remove(slot)
            for info in addons.find('plugin', lambda info: info.is_active):
                signal = getattr(info.plugin, name, None)
                if not isinstance(signal, Signal):
                    continue
                signal.disconnect(slot)

manager = PluginManager()

add_signal = manager.add_signal
remove_signal = manager.remove_signal
add_slot = manager.add_slot
remove_slot = manager.remove_slot

run_signal = manager.run_signal

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
    discover        ``True``        If this is True, we'll search for plugins immediately.
    load            ``True``        If this is True, plugins will be loaded automatically after discovery.
    activate        ``True``        If this is True, plugins will be activated automatically after loading.
    paths           ``[]``          A list of paths to search for plugins.
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

    # First, get the paths in case we need it.
    paths = addons.manager._types['plugin'][2]

    if kwargs.has_key('paths'):
        # Clear out paths. But don't delete it, because we'd just lose our
        # reference.
        del paths[:]
        paths.extend(kwargs.get('paths'))

    # Now, parse our options.
    if args:
        if args is True:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--safe-mode', action='store_true')
        parser.add_argument('--plugin-path', action='append')

        options = parser.parse_known_args(args)[0]

        # Do stuff.
        if options.safe_mode:
            addons.safe_mode = True

        if options.plugin_path:
            for path in reversed(options.plugin_path):
                paths.insert(0, path)

    # Now, for the discovery.
    if kwargs.get('discover', True):
        addons.discover('plugin')

    # And loading...
    if addons.safe_mode:
        log.info('Not loading plugins due to safe-mode.')
        return

    if kwargs.get('load', True):
        for info in addons.find('plugin', lambda info: not info.is_loaded):
            try:
                info.load()
            except (addons.DependencyError, ImportError), err:
                log.error('Error loading plugin %r: %s' %
                          (info.data['name'], err))

    # And activation...
    if kwargs.get('activate', True):
        for info in addons.find('plugin', lambda info: info.is_loaded):
            if info.is_active:
                continue
            try:
                info.plugin.activate()
            except Exception:
                log.exception('Error activating plugin %r.' %
                              info.data['name'])
