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
An easy to use style system that inherits from :doc:`/api/addons`, with support
for style inheritance, easy icon loading, Aero Glass when using Windows Vista
or later, and relatively easy hot reloads.

Style also pre-processes Qt stylesheets, allowing you to use relative URLs and
@import to include other stylesheets.
"""

###############################################################################
# Imports
###############################################################################

import argparse
import sys
import weakref

from PySide import QtGui
from PySide.QtCore import Signal, QObject
from PySide.QtGui import QApplication, QIcon, QWidget, QPixmap, QImageReader

from siding import addons, path, profile

try:
    from siding import _aeroglass
except ImportError:
    _aeroglass = None

###############################################################################
# Logging
###############################################################################

import logging
log = logging.getLogger('siding.style')

###############################################################################
# Constants and Storage
###############################################################################

STYLE_KEYS = {
    'QMotifStyle': 'motif',
    'QCDEStyle': 'cde',
    'QCleanlooksStyle': 'cleanlooks',
    'QGtkStyle': 'gtk',
    'QMacStyle': 'mac',
    'QPlastiqueStyle': 'plastique',
    'QWindowsStyle': 'windows',
    'QWindowsXPStyle': 'windowsxp',
    'QWindowsVistaStyle': 'windowsvista'
}

##### Storage #################################################################

_current_style = None
qss_preprocessor = None

###############################################################################
# Internal Helper Functions
###############################################################################

def _widget_style(value):
    val = value.lower()
    for key in STYLE_KEYS:
        if STYLE_KEYS[key].lower() == val:
            return key

    if not hasattr(QtGui, value):
        raise ValueError("No such widget style %r." % value)
    return value

###############################################################################
# StyleInfo Class
###############################################################################

class StyleInfo(addons.AddonInfo):
    """
    This class stores all the information on any given style, and has a few
    actions to make working with styles easy for the end user.
    """

    CORE_VALUES = (
        ('aero', bool),
        'inherits',
        ('ui', _widget_style),
        )

    # Defaults
    aero = False
    inherits = None
    ui = None

    ##### Inheritance Nonsense ################################################

    def on_inheritance_issue(self):
        """ If there's a problem with inheritance, just clear it. """
        log.debug('Disabling inheritance for style %r.' % self.data['name'])
        self.inherits = None

    ##### Actions #############################################################

    @addons.action("Use &Style", default=True)
    def use(self):
        """ Make this the active style. """
        activate_style(self)

    @use.is_enabled
    def is_enabled(self):
        return _current_style is self

# Registration
addons.add_type(
    'style',
    StyleInfo,
    "{name}/style.ini",
    ['styles'],
    text="Styles",
    icon='styles'
)

###############################################################################
# Style Application - Where the Magic Happens!
###############################################################################

def load_qss(name, style=None, use_inheritance=True, _always_return=True):
    if not style:
        style = _current_style
    if not style:
        if _always_return:
            return ''
        return

    # Try finding our file.
    if not style.path.exists(name):
        if use_inheritance and style.inherits:
            for parent in style.inherits:
                result = load_qss(name, parent, _always_return=False)
                if isinstance(result, basestring):
                    return result
        
        log.warning('Cannot find %r in style %r.' % (name, style.data['name']))
        if _always_return:
            return ''
        return

    # We have a file. Read it.
    with style.path.open(name) as f:
        data = f.read()

    log.debug('Begin loading Qt Style Sheet: %s' % name)
    log.debug('---- Before ----')
    log.debug(data)

    # QSS Pre-processing
    if qss_preprocessor:
        try:
            data = qss_preprocessor(name, data, style)
        except Exception:
            log.exception('Error pre-processing Qt Style Sheet %r for ' \
                          'style %r.' % (name, style.data['name']))

    log.debug('---- After ----')
    log.debug(data)
    log.debug('End loading Qt Style Sheet: %s' % name)

    return data

def _apply_style():
    """ Apply the current style to the application. """
    # Rebind for easier use and log.
    style = _current_style
    log.info('Applying style %r.' % style.data['name'])

    # Get the app.
    app = QApplication.instance()
    if not app:
        raise RuntimeError("You can't apply a style without a QApplication.")

    # Enable or disable Aero.
    if _aeroglass:
        if style.aero:
            _aeroglass.enable()
        else:
            _aeroglass.disable()

    # Set the widget style.
    app.setStyle(style.ui if style.ui else profile.get('siding/widget-style'))

    # Load the main stylesheet.
    app.setStyleSheet(load_qss('application.qss'))

    # Restyle every styled widget.
    for ref in _managed_widgets.keys():
        _style_widget(ref)

def _style_widget(ref):
    widget = ref()
    if not widget:
        del _managed_widgets[ref]
        return

    # Get the list of styles and makes a list to store the stylesheet while
    # we're building it.
    widget_styles = _managed_widgets[ref]
    qss = []

    # Log and start building.
    log.debug('Begin rebuilding styles on widget %r.' % widget)
    for style in widget_styles:
        # If it starts with "data:", just chop that off and add it, otherwise
        # load it with load_qss.
        if style.startswith('data:'):
            qss.append(style[5:])
            continue

        qss.append(load_qss(style))

    # Now, apply the styles.
    log.debug('Applying new styles to widget %r.' % widget)
    widget.setStyleSheet('\n'.join(qss))
    log.debug('End rebuilding styles on widget %r.' % widget)

###############################################################################
# Widget Management
###############################################################################

_managed_widgets = {}

def _find_widget(widget):
    """
    Find the widget in our list of tracked widgets and return the weak
    reference.
    """
    for ref in _managed_widgets.keys():
        wid = ref()
        if not wid:
            del _managed_widgets[ref]
            continue
        if wid is widget:
            return ref

###############################################################################
# Styling Functions
###############################################################################

def enable_aero(widget, margin=(-1, -1, -1, -1)):
    """
    Enable Aero Glass for the provided widget. This only functions on Windows
    and when Aero Glass is enabled system-wide.
    """
    if _aeroglass:
        _aeroglass.add(widget, margin)

def disable_aero(widget):
    """ Disable Aero Glass for the provided widget. """
    if _aeroglass:
        _aeroglass.remove(widget)

def icon(name, extension=None, style=None, use_inheritance=True,
         allow_theme=True, _always_return=True):
    """
    Find an icon with the given ``name`` and ``extension`` and return a
    :class:`PySide.QtGui.QIcon` for that icon.

    ================  ===========  ============
    Argument          Default      Description
    ================  ===========  ============
    name                           The name of the icon to load.
    extension                      The desired filename extension of the icon to load. If this isn't set, a list of supported formats will be used.
    style                          The style to load the icon from. If this isn't set, the current style will be assumed.
    use_inheritance   ``True``     Whether or not to search the parent style if the given style doesn't contain an icon.
    allow_theme       ``True``     Whether or not to fall back on Qt icon themes if an icon cannot be found.
    ================  ===========  ============
    """
    if style:
        if isinstance(style, basestring):
            style = addons.get('style', style)
        elif not isinstance(style, StyleInfo):
            raise TypeError("Can only activate StyleInfo instances!")
    else:
        style = _current_style

    # If we don't have a style, return a null icon now.
    if not style:
        return QIcon()

    # Right, time to find the icon.
    if isinstance(extension, (tuple, list)):
        extensions = extension
    elif extension:
        extensions = [extension]
    else:
        extensions = (str(ext) for ext in QImageReader.supportedImageFormats())

    # Iteration powers, activate!
    for ext in extensions:
        filename = '%s.%s' % (name, ext)
        icon_path = path.join('images', filename)
        if style.path.exists(icon_path):
            # We've got it, but what is it?
            if (not isinstance(style.path_source, basestring) or
                    style.path_source.startswith('py:')):
                # pkg_resource! Do things the fun and interesting way.
                with style.path.open(icon_path) as f:
                    pixmap = QPixmap()
                    pixmap.loadFromData(f.read())
                    return QIcon(pixmap)

            # Just a regular file. Open normally.
            return QIcon(style.path.abspath(icon_path))

    # Still here? We didn't find our icon then. If we're inheriting, then call
    # icon again for the style we inherit from.
    if use_inheritance and style.inherits:
        for parent in style.inherits:
            result = icon(name, extension, parent, True, False, False)
            if result:
                return result

    # For one last try, see if we can use the theme icons.
    if allow_theme and QIcon.hasThemeIcon(name):
        return QIcon.fromTheme(name)

    # We don't have an icon. Return a null QIcon.
    if _always_return:
        return QIcon()

def apply_stylesheet(widget, *paths):
    """
    Apply the stylesheet at the provided path(s) to the
    :class:`~PySide.QtGui.QWidget` ``widget``. More than one path can be
    supplied to apply more than one stylesheet to a widget.

    The stylesheet will be processed with the :func:`~Style.load_qss` function
    of the active style whenever it's reloaded, allowing for the use of the
    ``@import`` statement as well as relative URLs.

    In addition, this function will remember the widget and restyle it
    whenever the current style is reloaded or a new style is activated.

    If you want to include a raw Qt style sheet, rather than loading from a
    file, prefix the string with ``"data:"``. Example::

        siding.style.apply_stylesheet(my_widget, "data:* { color: red; }")

    Any pre-set styles on a widget will be saved as such an entry the first
    time this function is used on any given widget to preserve those styles.
    """
    if not isinstance(widget, QWidget):
        raise TypeError("widget not a QWidget.")

    ref = _find_widget(widget)
    if not ref:
        # Make a new entry for our new widget.
        ref = weakref.ref(widget)
        _managed_widgets[ref] = []

        # If there are existing styles, store them.
        qss = widget.styleSheet()
        if qss:
            _managed_widgets[ref].append('data:%s' % qss)

    # Extend the list of styles with the new paths.
    _managed_widgets[ref].extend(paths)

    # Now, restyle the widget.
    _style_widget(ref)

def list_stylesheets(widget):
    """ List all the Qt stylesheets being applied to ``widget``. """
    if not isinstance(widget, QWidget):
        raise TypeError("widget not a QWidget.")

    ref = _find_widget(widget)
    if not ref:
        return []

    return _managed_widgets[ref][:]

def remove_stylesheet(widget, *paths):
    """
    Remove the stylesheet at the provided path(s) from the ``widget``. More
    than one path can be supplied to remove more than one stylesheet from a
    widget.

    If no paths are provided, all styles will be cleared from the widget.
    """
    if not isinstance(widget, QWidget):
        raise TypeError("widget not a QWidget.")

    ref = _find_widget(widget)
    if not ref:
        return

    widget_styles = _managed_widgets[ref]

    if not paths:
        del widget_styles[:]
    else:
        for path in paths:
            try:
                widget_styles.remove(path)
            except ValueError:
                continue

    # Now, restyle the widget.
    _style_widget(ref)

    # If we don't have any more styles, remove it from the list for efficiency.
    if not widget_styles:
        del _managed_widgets[ref]

###############################################################################
# Signal Helper
###############################################################################

class Helper(QObject):
    """
    This class's sole purpose in life is providing a QObject to host the
    style_reloaded signal that's exposed as siding.style.style_reloaded
    """

    style_reloaded = Signal()

_helper = Helper()
style_reloaded = _helper.style_reloaded
"""
This signal is emitted whenever the active style is reloaded, or a new
style is loaded. It is recommended that you use this signal to reload
icons and other images for your application. Example::

    class MyWindow(QMainWindow):
        def __init__(self, parent=None):
            ...

            # Connect to the style system, and go ahead and load the icons
            # immediately too.
            siding.style.style_reloaded.connect(self.reload_icons)

        def reload_icons(self):
            self.some_action.setIcon(siding.style.icon('icon-name'))
            self.other_action.setIcon(siding.style.icon('other-icon'))
            self.setWindowIcon(siding.style.icon('window-icon'))
"""

###############################################################################
# Style Loading Functions
###############################################################################

def active():
    """ Return the currently active style. """
    return _current_style

def activate_style(style):
    """
    Activate the given style, or reapply it if it's already the active style at
    this time.
    """
    global _current_style

    if isinstance(style, basestring):
        style = addons.get('style', style)
    elif not isinstance(style, StyleInfo):
        raise TypeError("Can only activate StyleInfo instances!")

    # Check our inheritance.
    addons.check_inheritance(style)

    # Now that we have our style, activate it.
    _current_style = style
    _apply_style()

    # Now, sent out a signal.
    style_reloaded.emit()

def reload(style=None):
    """ Reload the active style, or the provided style. """
    if style:
        addons.get('style', style).load_information()
    elif _current_style:
        _current_style.load_information()

    # Now, to be safe, reapply the style.
    if _current_style:
        activate_style(_current_style)

###############################################################################
# Initialization
###############################################################################

def initialize(args=None, **kwargs):
    """
    Initialize the style system. You may use the following arguments to
    configure the style system:

    ==============  ==============  ============
    Argument        Default         Description
    ==============  ==============  ============
    style                           The name of the style to load. If this isn't specified, the set style will be loaded from the current profile.
    default_style   ``"default"``   The name of the default style, to be used if a style isn't specified here, in the profile, or in the command line.
    ==============  ==============  ============

    In addition, you can provide a list of command line arguments to have
    siding load them automatically. Example::

        siding.style.initialize(sys.argv[1:])

    The following command line arguments are supported:

    ================  ============
    Argument          Description
    ================  ============
    ``--safe-mode``   When safe mode is enabled, add-ons, including styles, won't be loaded automatically.
    ``--style``       The name of the style to load.
    ================  ============
    """

    # Get the default style and start our list.
    default_style = kwargs.get('default_style', 'default')
    styles = [default_style]

    # Add the profile's current style to the list.
    style = profile.get('siding/style/current-style')
    if style:
        styles.insert(0, style)

    # Add the passed style to the list.
    style = kwargs.get('style')
    if style:
        styles.insert(0, style)

    # Parse any options we've got.
    if args:
        if args is True:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--safe-mode', action='store_true')
        parser.add_argument('--style')
        options = parser.parse_known_args(args)[0]

        # Store those results.
        if options.safe_mode:
            addons.safe_mode = True

        if options.style:
            # Add the CLI style to the list.
            styles.insert(0, options.style)

    # Save the current widget style.
    widget_style = QApplication.instance().style().metaObject().className()
    widget_style = STYLE_KEYS.get(widget_style)
    if widget_style:
        profile.set('siding/style/widget-style', widget_style)

    # If safe-mode is enabled, just quit now.
    if addons.safe_mode:
        log.info('Not loading a style due to safe-mode.')
        return

    # Do it!
    addons.discover('style')

    # Get the style.
    for style in styles:
        try:
            activate_style(addons.get('style', style))
            break
        except KeyError:
            log.error('No such style: %s' % style)
