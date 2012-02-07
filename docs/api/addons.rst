``siding.addons``
*****************

.. automodule:: siding.addons

Functions
=========

.. autofunction:: action

AddonInfo
=========

.. autoclass:: AddonInfo

    .. autoattribute:: CORE_VALUES

    .. attribute:: name

        The add-on's name.

    .. attribute:: version

        The add-on's version.

    .. attribute:: file

        The name of the add-on's information file.

    .. attribute:: path

        The add-on's root path.

    .. attribute:: path_source

        The source the add-on was found in.

        .. seealso:: :doc:`/api/path`

    .. attribute:: data

        A dictionary of miscellaneous data about the add-on, potentially
        including a formatted name, description, author name, author link,
        website, and other such descriptive data.

    .. attribute:: requires

        An :class:`~collections.OrderedDict` of add-ons this add-on requires to
        load and function properly.

        .. seealso:: `Add-on Requirements`

    .. automethod:: load_information
    .. automethod:: update_ui
