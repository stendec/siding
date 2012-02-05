``siding.plugins``
******************

.. automodule:: siding.plugins

Exceptions
==========

.. autoexception:: VersionError
.. autoexception:: DependencyError

IPlugin
=======

.. autoclass:: IPlugin
    :members: info, is_active, activate, deactivate

PluginInfo
==========

.. autoclass:: PluginInfo
    :members: is_active, is_loaded, nice_name, plugin, load

PluginManager
=============

.. autoclass:: PluginManager
    :members:
        info_class, info_extension, update_class,
        list_plugins, get_info, get_plugin,
        discover_plugins, load_plugins,
        activate_plugins, deactivate_plugins,
        run_signal, add_signal, remove_signal,
        add_slot, remove_slot

Helper Functions
================

These may be replaced easilly to decouple ``siding.plugins`` from its
dependency on ``siding.profile``.

.. autofunction:: app_version
.. autofunction:: isblacklisted

Initialization
==============

.. autofunction:: add_search_path
.. autofunction:: initialize
