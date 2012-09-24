# -*- coding:utf-8 -*-
#
# Copyright (C) 2012, Carlos Jenkins <carlos@jenkins.co.cr>
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
Nested interface for plugin administration.
"""

from nested import *
from nested.utils import show_info, show_error, get_builder

from .base_plugin import NestedPlugin

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

class PluginsMM(object):
    """
    Plugin management interface.
    """

    def __init__(self, nested):
        """
        The object constructor.
        """

        self.nested = nested

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'pluginsmm.glade')

        # Get the main objects
        self.plugins_dialog = go('plugins_dialog')
        self.plugins_view = go('plugins_view')

        # Plugin map
        self.plugins = {}
        self.load_requested = {}

        # Configure interface
        if hasattr(nested, 'main') and nested.main is not None:
            self.plugins_dialog.set_transient_for(nested.main)

    def _format_description(self, plugin):
        """
        Pretty print a plugin GUI description.
        """
        return 'Foo'

    def _load(self, plugin):
        """
        Load a plugin to Nested.
        """
        # Check type
        if not hasattr(plugin, '__bases__'):
            return False

        # Check ancestors
        bases = plugin.__bases__
        found = False
        for b in bases:
            if b == NestedPlugin:
                found = True
                break
        if not found:
            return False

        # Check if plugin is registrable
        if plugin.uid == '' or plugin.uid in self.plugins.keys():
            return False

        # Register plugin
        self.plugins[plugin.uid] = plugin

        # FIXME load plugin if requested
        loaded = False

        # Load to the GUI
        self.plugins_view.get_model().append([plugin.uid, loaded,
                self._format_description(plugin), ''])
        return True

    def _on_select_cb(self, widget=None):
        pass

    def _enable_disable_cb(self, widget=None):
        pass

    def _configure_cb(self, widget=None):
        pass

    def admin(self, widget=None):
        """
        Runs the plugins management dialog.
        """
        self.plugins_view.set_cursor((0, ))
        self.plugins_view.grab_focus()
        response = self.plugins_dialog.run()
        if response == 0:
            self.plugins_dialog.hide()
            return False

        return self.admin()
