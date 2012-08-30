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
Independent Bibliography (BibTeX) Management Module for Python and PyGtk.
"""

from nested import *

import os
import logging
import gettext

import gtk
import pango

import bibparse
from bibtexdef import bibtex_entries, create_template

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

class BibMM(object):
    """Specialized GUI to handle bibliography (BibTex) data."""

    LINE_CURRENT = 'bibmm-current-entry'
    LINE_SEARCH  = 'bibmm-search-entry'

    def __init__(self, parent=None):
        """The object constructor."""

        self.available_keys = []
        self.current_file = ''

        # Create the interface
        self.builder = gtk.Builder()
        self.builder.set_translation_domain(AppContext.DEFAULT_APP)
        glade_file = os.path.join(WHERE_AM_I, 'bibmm.glade')
        self.builder.add_from_file(glade_file)

        # Get the main objects
        self.dialog_bib = self.builder.get_object('dialog_bib')
        self.view_bibtex = self.builder.get_object('view_bibtex')
        self.buffer_bibtex = BibTeXBuffer()
        self.view_bibtex.set_buffer(self.buffer_bibtex)
        self.summary = self.builder.get_object('summary')
        self.summary_liststore = self.summary.get_model()
        self.templates = self.builder.get_object('templates')
        self.templates_liststore = self.templates.get_model()

        # Create tags and marks
        self.buffer_bibtex.create_tag(self.LINE_SEARCH,
                                    weight=pango.WEIGHT_BOLD,
                                    foreground='red',
                                    background='yellow')
        self.buffer_bibtex.create_mark(self.LINE_SEARCH,
                                    self.buffer_bibtex.get_start_iter(),
                                    True)
        self.buffer_bibtex.create_mark(self.LINE_CURRENT,
                                    self.buffer_bibtex.get_start_iter(),
                                    True)

        # Configure interface
        if parent is not None:
            self.dialog_bib.set_transient_for(parent)
        #  Load templates
        for key in bibtex_entries.keys():
            registry = bibtex_entries[key]
            self.templates_liststore.append([
                                        key,
                                        '@' + key.upper() + ' - ' + registry['name'],
                                        registry['comment']
                                            ])
        self.templates.set_active(0)

        # Connect signals
        self.builder.connect_signals(self)

    def load_bib(self, bib_path):
        """
        Load a bibliography file from the given path into the GUI.
        """

        self._reset_gui()

        # Load file to TextView
        if os.path.isfile(bib_path):
            self.current_file = bib_path #!
            with open(bib_path) as bib_handler:
                bib_data = bib_handler.read()
                self.view_bibtex.get_buffer().set_text(bib_data)
                self._reload_summary(bib_data)
        self.buffer_bibtex.place_cursor(self.buffer_bibtex.get_start_iter())

        if self.dialog_bib.get_transient_for() is None:
            self.dialog_bib.show()
        else:
            response = self.dialog_bib.run()
            self.dialog_bib.hide()

    def _reset_gui(self):
        """
        Reset the GUI to the default state
        """
        self.view_bibtex.get_buffer().set_text('')
        self.summary_liststore.clear()
        self.view_bibtex.grab_focus()

    def _close_cb(self, widget, what=''): # 'what' is required for delete-event
        """
        If ran standalone exit the application.
        """
        if self.dialog_bib.get_transient_for() is None:
            logger.info(_('Running standalone shutdown...'))
            gtk.main_quit()

    def _insert_template_cb(self, widget):
        """
        Insert the currently selected template in the text buffer.
        """
        # Helpers
        def _get_insert_iter():
            return textbuffer.get_iter_at_mark(textbuffer.get_insert())
        textview = self.view_bibtex
        textbuffer = self.buffer_bibtex

        # Get template
        active = self.templates.get_active()
        key = self.templates_liststore[active][0]
        template = create_template(key)

        # Go to a newline if required
        insert_iter = _get_insert_iter()
        if not textview.starts_display_line(insert_iter):
            textbuffer.insert(insert_iter, '\n')
            insert_iter = _get_insert_iter()

        # Insert template
        textbuffer.move_mark_by_name(self.LINE_CURRENT, insert_iter)
        textbuffer.insert(insert_iter, template)

        # Scroll to the currently inserted entry
        textview.scroll_mark_onscreen(textbuffer.get_mark(self.LINE_CURRENT))
        insert_iter = textbuffer.get_iter_at_mark(textbuffer.get_mark(self.LINE_CURRENT))
        textbuffer.place_cursor(insert_iter)
        textview.grab_focus()

    def _validate_cb(self, widget):
        """
        Re-validate the current content of the buffer
        """
        self.summary_liststore.clear()
        self.buffer_bibtex.refresh()
        bib_data = self.buffer_bibtex.get_all_text()
        self._reload_summary(bib_data)

    def _reload_summary(self, bib_data):
        """
        Rebuild the BibTeX entries summary
        """
        strings, entries = bibparse.parse_data(bib_data)
        self.available_keys = entries.keys() #!
        if entries:

            # Liststore {line, type, id , author, title, year, note}
            # Liststore {str , str , str, str   , str  , str , str }
            # Fields    {str , str , str, list  , str  , str , str }
            fields = ['_line', '_type', '_code', 'author', 'title', 'year', 'note']

            for key in entries.keys():
                entry = entries[key]
                row = []
                for field in fields:
                    current = ''
                    if field in entry:
                        if field == 'author':
                            authors_list = entry[field]
                            for author_fields in authors_list:
                                if author_fields[1]: # Last name
                                    if current:
                                        current += ', '
                                    current += author_fields[1]
                        elif field == 'title' and len(entry[field]) > 20:
                            current = entry[field][:20].strip() + '...'
                        else:
                            current = entry[field]
                    row.append(current)
                self.summary_liststore.append(row)

            # Sort the model by line number
            self.summary_liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def _scroll_to_item(self, widget):
        """
        Scroll to the source line of the BibTeX entry currently selected in summary.
        """

        def _highlight_line(textview, line_num):
            textbuffer = textview.get_buffer()

            # Remove previous highlight
            old_line_iter = textbuffer.get_iter_at_mark(textbuffer.get_mark(self.LINE_SEARCH))
            old_line_end = old_line_iter.copy()
            old_line_end.forward_to_line_end()
            textbuffer.remove_tag_by_name(self.LINE_SEARCH, old_line_iter, old_line_end)

            # Highlight line if required and place cursor
            if line_num < 1:
                line_iter = textbuffer.get_start_iter()
            else:
                line_iter = textbuffer.get_iter_at_line(line_num - 1)
                line_end = line_iter.copy()
                line_end.forward_to_line_end()
                textbuffer.apply_tag_by_name(self.LINE_SEARCH, line_iter, line_end)
            textbuffer.place_cursor(line_iter)

            # Move line mark
            textbuffer.move_mark_by_name(self.LINE_SEARCH, line_iter)

            # Scroll to insert
            line_mark = textbuffer.get_insert()
            textview.scroll_to_mark(line_mark, 0.2)

        selection = self.summary.get_selection().get_selected()[1]
        if selection:
            entry_line = self.summary_liststore.get_value(selection, 0)
            _highlight_line(self.view_bibtex, int(entry_line))

