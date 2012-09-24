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

        self.description = go('description')
        self.authors = go('authors')
        self.website = go('website')
        self.configure = go('configure')

        # Plugin map
        self.plugins = {}
        self.requested = {}

        # Configure interface
        if hasattr(nested, 'main') and nested.main is not None:
            self.plugins_dialog.set_transient_for(nested.main)

        # Connect signals
        self.builder.connect_signals(self)

    def _format_description(self, plugin):
        """
        Pretty print a plugin GUI description.
        """
        formatted = '<span weight="bold">{}</span> ({}) \n{}'.format(
                        plugin.name, plugin.version, plugin.short_description)
        return formatted

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
        self.plugins[plugin.uid] = {'class': plugin,
                                    'instance': None,
                                    }

        # FIXME load plugin if requested
        loaded = False

        # Load to the GUI
        self.plugins_view.get_model().append([plugin.uid, loaded,
                self._format_description(plugin), ''])
        return True

    def _on_select_cb(self, treeview):
        """
        Change the description widgets to the information of the currently
        selected plugin.
        """
        # Clean interface
        self.description.set_text('')
        self.authors.set_text('')
        self.website.set_label('')
        self.website.set_uri('')
        self.website.set_sensitive(False)
        self.configure.set_sensitive(False)

        selection = treeview.get_selection().get_selected()[1]
        if not selection:
            return False

        model = treeview.get_model()
        uid = model.get_value(selection, 0)

        if not self.plugins.has_key(uid):
            return False

        loaded = self.plugins[uid]['instance']
        if loaded:
            self.configure.set_sensitive(True)

        plugin = self.plugins[uid]['class']

        self.description.set_text(plugin.large_description)
        self.authors.set_text(plugin.authors)
        self.website.set_label(plugin.website)
        self.website.set_uri(plugin.website)
        self.website.set_sensitive(True)

        return False

    def _enable_disable_cb(self, cellrenderertoggle, path):
        """
        Enable or disable a plugin
        FIXME: Better sandbox and messages.
        """
        # Get uid
        if path < 0:
            return False
        model = self.plugins_view.get_model()
        iterobj = model.get_iter(path)
        if not iterobj:
            return False
        uid = model.get_value(iterobj, 0)

        # Get instance
        loaded = self.plugins[uid]['instance']
        if loaded:

            # Disabling was requested
            try:
                loaded.on_disable()
            except Exception as e:
                pass

            self.plugins[uid]['instance'] = None
            self.configure.set_sensitive(False)
            model[path][1] = False

        else:

            # Enabling was requested
            try:
                loaded = self.plugins[uid]['class'](self.nested)
                loaded.on_enable()
            except Exception as e:
                pass

            self.plugins[uid]['instance'] = loaded
            self.configure.set_sensitive(True)
            model[path][1] = True

        return False

    def _configure_cb(self, widget=None):
        """
        Try to configure the selected plugin.
        FIXME: Better sandbox and messages.
        """

        selection = self.plugins_view.get_selection().get_selected()[1]
        if not selection:
            return False

        uid = self.plugins_view.get_model().get_value(selection, 0)

        if not self.plugins.has_key(uid):
            return False

        loaded = self.plugins[uid]['instance']
        plugin = self.plugins[uid]['class']
        if loaded and plugin.can_configure():
            try:
                loaded.do_configure()
            except Exception as e:
                pass

        return False

    def _close_cb(self, widget=None):
        """
        Close the dialog.
        """
        self.plugins_dialog.hide()

    def admin(self, widget=None):
        """
        Runs the plugins management dialog.
        """
        self.plugins_view.set_cursor((0, ))
        self.plugins_view.grab_focus()
        self.plugins_dialog.run()
        return False
