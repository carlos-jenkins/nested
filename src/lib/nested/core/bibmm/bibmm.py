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
from nested.utils import show_error, ask_user, get_builder

import os
import logging
import gettext

import gtk
import pango

from .bibparse import parse_data, MalformedBibTeX
from .bibtexdef import bibtex_entries, create_template
from ..widgets.textbuffer.bibtex_buffer import BibTeXBuffer
from ..widgets.textview.code_view import CodeView

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

class HelpViewer(object):
    """
    Simple widget to watch help documentation in HTML.
    """

    def __init__(self, parent=None):
        """
        The object constructor.
        """
        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'help.glade')

        # Get the main objects
        self.help_dialog = go('help_dialog')
        help_holder = go('help_holder')

        self.help_view = None
        try:
            import webkit
            self.help_view = webkit.WebView()
            help_holder.add_with_viewport(self.help_view)
            self.help_view.show()
        except ImportError:
            logger.warning('Unable to import webkit module. Entries help will be unavailable.')
            windows_warning = _('''\
Help viewer is not currently supported for Microsoft Windows.
If you need this functionality you can help the developer by packaging
pywebkitgtk for Windows: http://code.google.com/p/pywebkitgtk/\
''')
            placeholder = gtk.Label(windows_warning)
            help_holder.add_with_viewport(placeholder)
            placeholder.show()

        # Configure interface
        if parent is not None:
            self.help_dialog.set_transient_for(parent)

        # Connect signals
        self.builder.connect_signals(self)

    def load_help(self, entry):
        """
        Load help for given entry id.
        """
        if self.help_view is None:
            return

        # Find help file
        help_file = 'entry_{}.html'.format(entry)
        help_path = os.path.join(WHERE_AM_I, 'help', context_lang, help_file)
        if not os.path.isfile(help_path):
            help_path = os.path.join(WHERE_AM_I, 'help', 'en_US', help_file)

        # Load help file
        if not os.path.isfile(help_path):
            self.help_view.load_html_string(
                _('<p>File {} not found.</p>').format(help_path), 'file:///')
        else:
            self.help_view.load_uri('file:///' + help_path)

        # Run help dialog
        self.help_dialog.run()
        self.help_dialog.hide()

    def _back_cb(self, widget):
        """
        Go back in help viewer.
        """
        if self.help_view is not None:
            self.help_view.go_back()
        return False

    def _forward_cb(self, widget):
        """
        Go forward in help viewer.
        """
        if self.help_view is not None:
            self.help_view.go_forward()
        return False


class BibMM(object):
    """
    Specialized GUI to handle bibliography (BibTex) data.
    """

    LINE_CURRENT = 'bibmm-current-entry'
    LINE_SEARCH  = 'bibmm-search-entry'

    def __init__(self, parent=None, textview=None):
        """
        The object constructor.
        """

        self.available_keys = []
        self.current_file = None

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'bibmm.glade')

        # Get the main objects
        self.dialog_bib = go('dialog_bib')

        self.summary = go('summary')
        self.summary_liststore = self.summary.get_model()

        self.templates = go('templates')
        self.templates_liststore = self.templates.get_model()

        self.styles = go('styles')
        self.styles_liststore = self.styles.get_model()
        self.style_previewer = go('style_previewer')
        self.style_canvas = go('style_canvas')

        # Create objects
        holder = go('main_view_holder')
        self.buffer_bibtex = BibTeXBuffer()
        self.view_bibtex = CodeView(self.buffer_bibtex)
        holder.add(self.view_bibtex)
        self.help_viewer = HelpViewer(self.dialog_bib)

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
        if self.help_viewer.help_view is None:
            go('entries_help').set_sensitive(False)

        #  Load templates
        for key in bibtex_entries.keys():
            registry = bibtex_entries[key]
            self.templates_liststore.append([key,
                                '@' + key.upper() + ' - ' + registry['name'],
                                registry['comment']])
        self.templates.set_active(0)

        # Load styles
        # TODO: Should not be hardwire
        self.styles_liststore.append(['apalike', 'APA like style (apalike)'])
        self.styles.set_active(0)

        # Connect signals
        self.builder.connect_signals(self)

    def _view_entry_help_cb(self, widget):
        """
        Load help for currently selected entry type.
        """
        if self.help_viewer.help_view is not None:
            entry = self.templates_liststore[self.templates.get_active()][0]
            self.help_viewer.load_help(entry)
        return False

    def load_bib(self, bib_path):
        """
        Load a bibliography file from the given path into the GUI.
        """

        self._reset_gui()

        # Load file to TextView
        if os.path.isfile(bib_path):
            with open(bib_path) as bib_handler:
                bib_data = bib_handler.read()
                self.view_bibtex.get_buffer().set_text(bib_data)
                try:
                    strings, entries = parse_data(bib_data)
                    self._reload_summary(entries)
                except MalformedBibTeX as e:
                    logger.warning(_('Malformed bibliographic database {}.').format(bib_path))
                self.current_file = bib_path
        else:
            logger.warning(_('Unable to find file {}.').format(bib_path))
        self.buffer_bibtex.place_cursor(self.buffer_bibtex.get_start_iter())

        self.dialog_bib.run()

    def _reset_gui(self):
        """
        Reset the GUI to the default state
        """
        self.view_bibtex.get_buffer().set_text('')
        self.summary_liststore.clear()
        self.view_bibtex.grab_focus()

    def _close_cb(self, widget):
        """
        Hide the dialog.
        """
        self.dialog_bib.hide()

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
        insert_iter = textbuffer.get_iter_at_mark(
                                        textbuffer.get_mark(self.LINE_CURRENT))
        textbuffer.place_cursor(insert_iter)
        textview.grab_focus()

    def _show_style_cb(self, widget):
        """
        Show a simple dialog with a rendering of the currently selected style.
        """
        style = self.styles_liststore[self.styles.get_active()][0]
        style_file = os.path.join(WHERE_AM_I, 'styles', style + '.png')
        self.style_canvas.set_from_file(style_file)
        self.style_previewer.run()
        self.style_previewer.hide()

    def _validate_cb(self, widget):
        """
        Re-validate the current content of the buffer.
        """
        bib_data = self.buffer_bibtex.get_all_text()
        try:
            strings, entries = parse_data(bib_data)
        except MalformedBibTeX as e:
            if e.line >= 0:
                show_error(
                    _('An error ocurred while parsing the database. Please '
                      'check "{}" at line {}.').format(e.text, e.line),
                    self.dialog_bib)
            else:
                show_error(
                    _('An error ocurred while parsing the database.'),
                    self.dialog_bib)
            return False
        self._reload_summary(entries)
        self.buffer_bibtex.refresh()
        self.view_bibtex._spellcheck.recheck() # FIXME

    def _reload_summary(self, entries):
        """
        Rebuild the BibTeX entries summary.
        """

        self.summary_liststore.clear()

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
        return True

    def _scroll_to_item(self, widget):
        """
        Scroll to the source line of the BibTeX entry currently selected in
        summary.
        """

        def _highlight_line(textview, line_num):
            textbuffer = textview.get_buffer()

            # Remove previous highlight
            old_line_iter = textbuffer.get_iter_at_mark(
                                        textbuffer.get_mark(self.LINE_SEARCH))
            old_line_end = old_line_iter.copy()
            old_line_end.forward_to_line_end()
            textbuffer.remove_tag_by_name(self.LINE_SEARCH,
                                        old_line_iter, old_line_end)

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

    def _save_cb(self, widget):
        """
        Save buffer content back to original BibTeX file.
        """
        if self.current_file is None:
            return False

        # Check buffer
        content = self.view_bibtex.get_buffer().get_all_text()
        try:
            strings, entries = parse_data(content)
        except MalformedBibTeX as e:
            yes = ask_user(_('The current database has errors, do you still '
                             'want to save?'), self.dialog_bib)
            if not yes:
                return False

        # Save file
        with open(self.current_file, 'w') as handler:
            handler.write(content)

        self._close_cb(widget)
