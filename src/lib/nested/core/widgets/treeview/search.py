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
Control object that links some widgets to add search capabilities of different
types (filter and search) to a TreeView.
WARNING: Currently this was only tested with a TreeView using a ListStore model
and not swapping it's model.
"""

from nested import *

import os
import logging
import gettext

import gtk

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext


class TreeViewSearch(object):
    """
    Simple control widget to add search capabilities to a TreeView.
    """

    def __init__(self, treeview, entry, filtermode=True, column=0):
        """
        The object constructor.
        """
        self.treeview = treeview
        self.entry = entry
        self.filtermode = filtermode
        self.model = treeview.get_model()

        # Configure
        self.treeview.set_enable_search(not filtermode)
        if filtermode:
            # Configure filter model
            self.filter_model = self.model.filter_new()
            self.filter_model.set_visible_func(self._visible_func)
            self.model = gtk.TreeModelSort(self.filter_model)
            self.treeview.set_model(self.model)
            # Request a new filtering on entry content change
            self.entry.connect('changed', self._search_requested_cb)
        else:
            # Configure entry as search entry
            self.treeview.set_search_entry(entry)

        # Force to sort and search using some column
        self.treeview.set_search_column(column)
        self.model.set_sort_column_id(column, gtk.SORT_ASCENDING)

        # Perform search action on sort change
        self.model.connect('sort-column-changed', self._search_requested_cb)
        # Basic GUI
        self.treeview.connect('start-interactive-search', self._select_search)
        self.entry.connect('icon-press', self._clear_cb)


    def _search_requested_cb(self, widget, data=None):
        """
        Perform a search action.
        """
        if self.filtermode:
            # Trigger filtering
            self.filter_model.refilter()
        else:
            # Set search column
            column, sort = self.treeview.get_model().get_sort_column_id()
            self.treeview.set_search_column(column)
        return False

    def _visible_func(self, filter_model, iterobj, data=None):
        column, sort = self.model.get_sort_column_id()
        if column is None:
            return True
        search_text = self.entry.get_text()
        row_text = filter_model.get_value(iterobj, column)
        print('Search: "{}". Row: "{}"'.format(search_text, row_text))
        return search_text.lower() in row_text.lower()

    def _clear_cb(self, entry, event, data=None):
        """
        Clear entry's text when clear icon is pressed.
        """
        entry.set_text('')
        return False

    def _select_search(self, treeview, data=None):
        """
        Select search entry when default's Ctrl+F is pressed.
        """
        self.entry.grab_focus()
        return False
