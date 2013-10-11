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

import os
import sys
import time
import hashlib
import unicodedata
import subprocess
import webbrowser
import gtk

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


def sha1sum(filepath):
    """
    SHA1 of a file.
    """
    sha1 = hashlib.sha1()
    f = open(filepath, 'rb')
    try:
        sha1.update(f.read())
    finally:
        f.close()
    return sha1.hexdigest()


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


def show_info(msg='', parent=None):
    """
    Show an information message to the user.
    """
    info = gtk.MessageDialog(parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_INFO,
                            gtk.BUTTONS_CLOSE, msg)
    info.run()
    info.destroy()


def show_error(msg='', parent=None):
    """
    Show an error message to the user.
    """
    error = gtk.MessageDialog(parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR,
                            gtk.BUTTONS_CLOSE, msg)
    error.run()
    error.destroy()


def ask_user(msg='', parent=None):
    """
    Show a question message to the user.
    """
    message = gtk.MessageDialog(parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_YES_NO, msg)
    response = message.run()
    message.destroy()
    return response == gtk.RESPONSE_YES


def get_builder(base, glade_file):
    """
    Get a GtkBuilder object ready to use.
    """
    builder = gtk.Builder()
    builder.set_translation_domain('nested')
    glade_path = os.path.join(base, glade_file)
    builder.add_from_file(glade_path)
    return builder, builder.get_object
