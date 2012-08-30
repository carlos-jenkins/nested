# -*- coding:utf-8 -*-
#
# Copyright (C) 2011, 2012 Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Utilities for Nested.
"""

import time
import hashlib
import unicodedata
import subprocess
import webbrowser

def transliterate_string(string):
    """
    Transliterate given string.
    """
    nkfd_form = unicodedata.normalize('NFKD', unicode(string))
    normalized = u''.join([c for c in nkfd_form if not unicodedata.combining(c)])
    return normalized


def safe_string(string):
    """
    Transform any string to a safer representation:
        e.g: 'Quién sabe caño' -> 'quien_sabe_cano'
    """

    string = string.strip()
    normalized = transliterate_string(string)
    normalized = normalized.lower()
    normalized = normalized.replace(' ', '_')
    normalized = normalized.replace('-', '_')
    clean = []
    for c in normalized:
        if c.isalnum() or c == '_':
            clean.append(c)
    return ''.join(clean)


def time_hash(lenght=10):
    """
    Generates a hash based on current time.
    """
    if lenght < 1:
        lenght = 10
    result = hashlib.sha1()
    result.update(str(time.time()))
    return result.hexdigest()[:lenght]


def default_open(something_to_open):
    """
    Open given file with default user program.
    """

    # Check if URL
    if something_to_open.startswith('http') or something_to_open.endswith('.html'):
        webbrowser.open(something_to_open)
        return 0

    ret_code = 0

    if sys.platform.startswith('linux'):
        ret_code = subprocess.call(['xdg-open', something_to_open])

    elif sys.platform.startswith('darwin'):
        ret_code = subprocess.call(['open', something_to_open])  # Untested

    elif sys.platform.startswith('win'):
        logger.debug(something_to_open)
        ret_code = subprocess.call(['start', something_to_open], shell=True)

    return ret_code


def check_prefix(prefix, string):
    """
    Check that everyline in the given string begins with given prefix.
    """
    lines = string.splitlines()
    result = []
    for line in lines:
        line = line.strip()
        if line.startswith(prefix):
            result.append(line)
    return ('\n').join(result)
