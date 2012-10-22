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
Utility to create plugins for Nested.
"""

from nested import *
from nested.utils import show_error, ask_user, get_builder, default_open
from nested.core.api import base_plugin

import os
import sys
import gtk
import logging
import gettext

from os.path import isfile, isdir

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

APIS = [{
            'id'     :  '1.0',
            'name'   : _('API v1.0 - September 2012'),
            'module' : 'api1_0',
        }]

class Creator(object):
    """
    Specialized GUI to handle API Checker data.
    """

    def __init__(self):
        """
        The object constructor.
        """

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'creator.glade')

        # Get the main objects
        self.window = go('window')
        self.plugin = go('plugin')
        self.plugin_filter = go('plugin_filter')
        self.compat = go('compat')
        self.compat_model = go('compat_model')

        # Metadata
        self.path = go('path')
        self.name = go('name')
        self.version = go('version')
        self.short = go('short')
        self.website = go('website')
        self.authors = go('authors').get_buffer()
        self.longd = go('long').get_buffer()

        # Config filters
        self.plugin_filter.set_name('Python plugin (*.py)')
        self.plugin_filter.add_mime_type('text/x-python')
        self.plugin_filter.add_pattern('*.py')
        self.plugin.add_filter(self.plugin_filter)

        # Load compatibilities
        for api in APIS:
            self.compat_model.append([api['id'], api['name'], api['module']])
        self.compat.set_active(0)

        # Connect signals
        self.builder.connect_signals(self)

    def _show_error(self, msg='', parent=None):
        """
        Show an error message to the user.
        """
        if parent is None:
            parent = self.window
        show_error(msg, parent)

    def _ask_user(self, msg='', parent=None):
        """
        Show an error message to the user.
        """
        if parent is None:
            parent = self.window
        return ask_user(msg, parent)

    def _close_cb(self, widget, what=''): # 'what' is required for delete-event
        """
        Quit the application.
        """
        gtk.main_quit()

    def _create_cb(self, widget):
        """
        Create the plugin.
        """

        # Check file is selected
        plugin_path = self.plugin.get_filename()
        if plugin_path is None:
            self._show_error(_('Please select a plugin file.'))
            return False

        for m in [self.path, self.name, self.version]:
            if m.get_text() == '':
                self._show_error(_('Please fill all the required data.'))
                return False
        # Open base plugin
        print(self.get_base_plugin_path())

    def _select_filename_cb(self, widget):
        """
        Select a filename.
        """
        # Run dialog
        response = self.plugin.run()
        if response < 0:
            self.plugin.hide()
            return False

        # Set filename
        path = self.plugin.get_filename()
        if path is None:
            self._show_error(_('Please select a plugin file.'))
            self._select_filename_cb(widget)
            return False

        if isdir(path):
            self.plugin.set_current_folder(path)
            self._select_filename_cb(widget)
            return False

        if not path.endswith('.py'):
            path = path + '.py'
            self.plugin.select_filename(path)

        if isfile(path):
            override = self._ask_user(
                "The currently selected file already exists. "
                "Do you want to override it?")
            if not override:
                self._select_filename_cb(widget)
                return False

        self.path.set_text(path)
        self.plugin.hide()

        return False

    def _documentation_cb(self, widget):
        """
        Show base plugin for reference.
        """
        default_open(self.get_base_plugin_path())

    def get_base_plugin_path(self):
        """
        Get the base plugin path.
        """
        return base_plugin.__file__.replace('file://', '', 1)[:-1]

    def _clear_cb(self, widget):

        for e in [self.path, self.name, self.version, self.short,
                  self.website, self.authors, self.longd]:
            e.set_text('')
