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
Citation dialog module for BibMM.
"""

from nested import *
from nested.utils import show_error, get_builder

from nested.core.widgets.treeview.search import TreeViewSearch

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

class SearchAndCite(object):
    """
    Simple widget to search and cite a bibliographic entry.
    """

    def __init__(self, model, parent=None):
        """
        The object constructor.
        """
        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'cite.glade')

        # Get the main objects
        self.cite_dialog = go('cite_dialog')
        self.cite_view = go('cite_view')
        self.cite_input = go('cite_input')

        # Create search
        self.cite_view.set_model(model)
        self.search = TreeViewSearch(self.cite_view, self.cite_input)

        # Configure interface
        if parent is not None:
            self.cite_dialog.set_transient_for(parent)

    def cite(self):
        """
        Load the citation dialog and return the id or empty string if user
        cancelled the citation.
        """
        response = self.cite_dialog.run()
        if response != 0:
            self.cite_dialog.hide()
            return ''
        iterobj = self.search.get_selected()
        if not iterobj:
            show_error(_('Please select an entry.'), self.cite_dialog)
            return self.cite()
        self.cite_dialog.hide()
        bibid = self.cite_view.get_model().get_value(iterobj, 2)
        if not bibid:
            show_error(_('The currently selected entry doesn\'t has a valid id.'
                         ' Please correct this in your database or select '
                         'another entry.'),
                self.cite_dialog)
            return self.cite()
        return bibid
