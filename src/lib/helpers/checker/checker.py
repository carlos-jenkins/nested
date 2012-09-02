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
API Checker Module for Python and PyGtk.
"""

from nested import *

import os
import logging
import gettext

import gtk

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

class Checker(object):
    """
    Specialized GUI to handle API Checker data.
    """

    def __init__(self):
        """
        The object constructor.
        """

        # Create the interface
        self.builder = gtk.Builder()
        self.builder.set_translation_domain('nested')
        glade_file = os.path.join(WHERE_AM_I, 'checker.glade')
        self.builder.add_from_file(glade_file)

        # Get the main objects
        go = self.builder.get_object
        self.window_checker = go('window_checker')
        self.plugin = go('plugin')
        self.plugin_filter = go('plugin_filter')
        self.results = go('results')
        self.results_model = go('results_model')
        self.compat = go('compat')
        self.compat_model = go('compat_model')

        # Config filters
        self.plugin_filter.set_name('Python plugin (*.py)')
        self.plugin_filter.add_mime_type('text/x-python')
        self.plugin_filter.add_pattern('*.py')
        self.plugin.add_filter(self.plugin_filter)

        # Load compatibilities
        self.compat_model.append(['1.0', _('API v1.0 - September 2012')])
        self.compat.set_active(0)

        # Connect signals
        self.builder.connect_signals(self)

    def _show_error(self, msg='', parent=None):
        """
        Show an error message to the user.
        """
        if parent is None:
            parent = self.window_checker
        error = gtk.MessageDialog(parent,
                                  gtk.DIALOG_DESTROY_WITH_PARENT,
                                  gtk.MESSAGE_ERROR,
                                  gtk.BUTTONS_CLOSE, msg)
        error.run()
        error.destroy()

    def _close_cb(self, widget, what=''): # 'what' is required for delete-event
        """
        Quit the application.
        """
        gtk.main_quit()

    def _validate_cb(self, widget):
        """
        Validate the selected plugin.
        """
        self.results_model.clear()

        # Check file is selected
        plugin_path = self.plugin.get_filename()
        if plugin_path is None:
            self._show_error('Please select a plugin file.')
            return False

        print('Perfoming checks to {}.'.format(plugin_path))
