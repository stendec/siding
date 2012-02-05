``siding.style``
****************

.. automodule:: siding.style

Style
=====

.. autoclass:: Style
    :members:
        active,
        apply, reload, style_widget,
        load_qss, icon,
        has_file, get_file, get_path

NullStyle
=========

.. autoclass:: NullStyle

Styling Functions
=================

.. autofunction:: enable_aero
.. autofunction:: disable_aero

.. autofunction:: icon

.. autofunction:: list_stylesheets
.. autofunction:: apply_stylesheet
.. autofunction:: remove_stylesheet

Signals
=======

.. autodata:: style_reloaded


Style Loading
=============

.. autofunction:: active
.. autofunction:: list_styles
.. autofunction:: load
.. autofunction:: reload

Initialization
==============

.. autofunction:: initialize
