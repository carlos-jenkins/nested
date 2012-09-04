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
from nested.utils import show_error, get_builder

import os
import logging
import gettext

import gtk
import gobject

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

APIS = [{
            'id'     :  '1.0',
            'name'   : _('API v1.0 - September 2012'),
            'module' : 'api1_0',
        }]

class Checker(object):
    """
    Specialized GUI to handle API Checker data.
    """

    def __init__(self):
        """
        The object constructor.
        """

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'checker.glade')

        # Get the main objects
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
            parent = self.window_checker
        show_error(msg, parent)

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
            self._show_error(_('Please select a plugin file.'))
            return False

        # Load verification module
        selected = self.compat.get_active()
        if selected < 0:
            return
        try:
            module = self.compat_model[selected][2]
            api = __import__(module)
        except ImportError:
            self._show_error(
                _('Unable to load module {}. No test will be run.').format(module))
            return False

        # Run tests
        logger.debug('Perfoming checks to {}.'.format(plugin_path))
        api.run(plugin_path, self._test_cb)

    def _test_cb(self, result):
        print(result)
