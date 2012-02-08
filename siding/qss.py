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
The Qt stylesheet pre-processor used by the style system.
"""

###############################################################################
# Imports
###############################################################################

import base64
import hashlib
import os
import urllib
import re

from PySide.QtCore import QUrl

from siding import addons, path, style as style_module

try:
    from siding import _aeroglass
except ImportError:
    _aeroglass = None

###############################################################################
# Constants
###############################################################################

QSS_IMPORT = re.compile(r"@import\s+(.*?)\s*(?:;|$)")
QSS_URL = re.compile(r"url\((.*?)\)", re.DOTALL)
QSS_AERO = re.compile(r"#IFAERO\s*(.*?)\s*(?:#ELSE\s*(.*?)\s*)?#END", re.DOTALL)

###############################################################################
# Entry Point
###############################################################################

def qss_preprocessor(name, data, style):
    """ Process the Qt stylesheet and return the processed style. """

    # Chop off the path for use with relative URLs.
    path = os.path.dirname(name)

    # Process the poorly thought out Aero things.
    data = QSS_AERO.sub(do_aero, data)

    # Now, process the import statements.
    data = QSS_IMPORT.sub(lambda match: do_import(path, style, match), data)

    # And, finally, the rest of the URLs.
    data = QSS_URL.sub(lambda match: do_url(path, style, match), data)

    return data

###############################################################################
# Aero Checks
###############################################################################

def do_aero(match):
    if _aeroglass and _aeroglass.manager.status:
        return match.group(1)
    return match.group(2)

###############################################################################
# @import Expansion
###############################################################################

def do_import(path, style, match, _always_return=True):
    """ Parse and expand an @import statement. """
    url = match.group(1)
    if url.startswith('url('):
        if not url.endswith(')'):
            return match.group(0)
        url = url[4:-1]

    # Try parsing the URL.
    url = handle_url(path, style, url, True)
    if not url or not style.path.exists(url):
        if style.inherits:
            for parent in style.inherits:
                result = do_import(path, addons.get('style', parent),
                                   match, False)
                if isinstance(result, basestring):
                    return result
            if _always_return:
                return ''
            return

    # Alright, we've got a URL. Load it.
    return style_module.load_qss(url, style)

###############################################################################
# url() Handling
###############################################################################

def do_url(path, style, match):
    """
    Process a url(), handling relative URLs and returning absolute paths.
    """
    url = handle_url(path, style, match.group(1))
    if not url:
        return match.group(0)

    url = style.path.normpath(style.path.abspath(url))
    return 'url("%s")' % url.encode('unicode_escape')

###############################################################################
# The Actual URL Processing
###############################################################################

def handle_url(path, style, url, for_import=False):
    if ((url.startswith('"') and url.endswith('"')) or
            (url.startswith("'") and url.endswith("'"))):
        url = url[1:-1]

    # Make a QUrl.
    url = QUrl(url.decode('unicode_escape'))

    if url.scheme() == 'data':
        return data_url(url)

    # If it's relative, build an absolute URL. If not, return.
    if not url.isRelative():
        return

    url = url.toLocalFile()
    if url.startswith('/'):
        url = url[1:]
    else:
        url = style.path.join(path, url)

    if for_import:
        return url

    return find_url(style, url)

def find_url(style, url):
    if style.path.exists(url):
        return style.path.abspath(url)

    elif style.inherits:
        for parent in style.inherits:
            result = find_url(addons.get('style', parent), url)
            if result:
                return result

def data_url(url):
    # Extract the useful information from the URL's path.
    format, sep, data = url.path().partition(',')
    if not sep and not data:
        data = format
        format = ''

    mimetype, _, format = format.partition(';')
    if not mimetype:
        ext = 'txt'
    else:
        _, _, ext = mimetype.rpartition('/')
    if not format:
        format = 'charset=US-ASCII'

    # Build the filename.
    filename = path.join(path.cache(), 'data-uris', '%s.%s' %
                                          (hashlib.md5(data).hexdigest(), ext))

    # Ensure the path exists and write the file.
    try:
        if not os.path.exists(filename):
            os.makedirs(filename)
        with open(filename, 'wb') as f:
            if format == 'base64':
                f.write(base64.b64decode(data))
            elif format.startswith('charset='):
                data = urllib.unquote(data).encode('latin1')
                cs = format[8:]
                if cs and cs.lower() not in ('utf-8', 'utf8'):
                    data = data.decode(cs).encode('utf-8')
                f.write(data)
            else:
                return
    except (ValueError, OSError, IOError, TypeError):
        return

    return path.normpath(filename)

###############################################################################
# Initialization
###############################################################################

style_module.qss_preprocessor = qss_preprocessor
