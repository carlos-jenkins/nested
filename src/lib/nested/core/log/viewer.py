# -*- coding: utf-8 -*-
#       latex_log.py - Simple LaTeX error log viewer.
#
#       Copyright (c) 2012 Carlos Jenkins <cjenkins@softwarelibrecr.org>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program. If not, see <http://www.gnu.org/licenses/>

"""@package latex_log
Simple LaTeX log viewer.
"""

import os
import logging
import gettext

import gtk
import pango

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

import .logparser

class LaTeXLogViewer(object):
    """Specialized GUI to analyze LaTeX log files."""

    LINE_SEARCH = 'viewer-highlight-line'

    def __init__(self, parent=None):
        """The object constructor."""

        # Create the interface
        self.builder = gtk.Builder()
        self.builder.set_translation_domain('nested')
        glade_file = os.path.join(WHERE_AM_I, 'viewer.glade')
        self.builder.add_from_file(glade_file)

        # Get the main objects
        self.dialog_log = self.builder.get_object('dialog_log')

        self.view_log = self.builder.get_object('view_log')
        self.view_latex = self.builder.get_object('view_latex')

        self.summary = self.builder.get_object('summary')
        self.summary_liststore = self.summary.get_model()

        self.error_msg = self.builder.get_object('error_msg')
        self.warning_msg = self.builder.get_object('warning_msg')
        self.info_msg = self.builder.get_object('info_msg')
        self.log_parser = logparser.LogParser()

        # Get the pixbuf icons for the summary
        self.icon_warning = self.summary.render_icon(
                                    stock_id=gtk.STOCK_DIALOG_INFO,
                                    size=gtk.ICON_SIZE_MENU,
                                    detail=None)
        self.icon_error = self.summary.render_icon(
                                    stock_id=gtk.STOCK_DIALOG_ERROR,
                                    size=gtk.ICON_SIZE_MENU,
                                    detail=None)

        # Configure interface
        if parent is not None:
            self.dialog_log.set_transient_for(parent)

        def _configure_text_view(textview):
            # Configure View
            textview.modify_font(pango.FontDescription('DejaVu Sans Mono 10'))
            linenumbers = LineNumbers(textview)
            # Configure Model
            textbuffer = textview.get_buffer()
            textbuffer.create_tag(self.LINE_SEARCH,
                                  weight=pango.WEIGHT_BOLD,
                                  foreground='red',
                                  background='yellow')
            textbuffer.create_mark(self.LINE_SEARCH,
                                    textbuffer.get_start_iter(),
                                    True)
        _configure_text_view(self.view_log)
        _configure_text_view(self.view_latex)

        # Connect signals
        self.builder.connect_signals(self)

    def load_log(self, log_path):
        """
        Load a log file from the given path into the GUI.
        """

        self._reset_gui()

        # Load LaTeX document
        latex_path = os.path.splitext(log_path)[0] + '.tex'
        if os.path.isfile(latex_path):
            with open(latex_path) as latex_handler:
                self.view_latex.get_buffer().set_text(latex_handler.read())

        # Load and parse log
        if os.path.isfile(log_path):

            # Load log
            with open(log_path) as log_handler:
                log_text = log_handler.read().decode('utf-8', 'ignore')
                self.view_log.get_buffer().set_text(log_text)

            # Parse log
            if(self.log_parser.read(log_path) == 0): # Valid log

                level = 'info'

                warnings_list = []
                for warning in self.log_parser.get_warnings():
                    if level != 'warning':
                        logger.info(_('Warnings found on the log file.'))
                        level = 'warning'
                    logger.debug(warning)
                    warnings_list.append(
                        [
                            self.icon_warning,
                            'Warning',
                            0,
                            warning['text'],
                            int(warning['log_line'])
                        ]
                    )

                errors_list = []
                for error in self.log_parser.get_errors():
                    if level != 'error':
                        logger.info(_('Errors found on the log file.'))
                        level = 'error'
                    logger.debug(error)
                    errors_list.append(
                        [
                            self.icon_error,
                            'Error',
                            0 if error['line'] is None else int(error['line']),
                            error['text'],
                            int(error['log_line']),
                        ]
                    )

                # Append erros to summary
                last_error = None
                for row in errors_list:
                    last_error = self.summary_liststore.append(row)

                # Find a show a hint about the problem
                if last_error:
                    hint = self.summary_liststore.get_path(last_error)
                    self.summary.set_cursor(hint)
                    self.summary.scroll_to_cell(hint)
                    self.summary.grab_focus()

                # Append warnings to summary
                for row in warnings_list:
                    self.summary_liststore.append(row)

                # Configure message
                if level == 'error':
                    self.info_msg.hide()
                    self.error_msg.show()
                elif level == 'warning':
                    self.info_msg.hide()
                    self.warning_msg.show()

            else:
                logger.error(_('The log file is invalid.'))

        if self.dialog_log.get_transient_for() is None:
            self.dialog_log.show()
        else:
            response = self.dialog_log.run()
            self.dialog_log.hide()

    def _reset_gui(self):
        """
        Reset the GUI to the default state.
        """
        self.view_log.get_buffer().set_text('')
        self.view_latex.get_buffer().set_text('')
        self.summary_liststore.clear()
        self.error_msg.hide()
        self.warning_msg.hide()
        self.info_msg.show()

    def _close_cb(self, widget, what=''): # 'what' is required for delete-event
        """
        If ran standalone exit the application.
        """
        if self.dialog_log.get_transient_for() is None:
            logger.info(_('Running standalone shutdown...'))
            gtk.main_quit()

    def _scroll_to_item(self, widget):
        """
        Scroll to the log file line and latex source line for the currently
        selected row in summary.
        """

        def _highlight_line(textview, line_num):
            textbuffer = textview.get_buffer()

            # Remove previous highlight
            old_line_iter = textbuffer.get_iter_at_mark(
                                textbuffer.get_mark(self.LINE_SEARCH))
            old_line_end = old_line_iter.copy()
            old_line_end.forward_to_line_end()
            textbuffer.remove_tag_by_name(
                                self.LINE_SEARCH, old_line_iter, old_line_end)

            # Highlight line if required and place cursor
            if line_num < 1:
                line_iter = textbuffer.get_start_iter()
            else:
                line_iter = textbuffer.get_iter_at_line(line_num - 1)
                line_end = line_iter.copy()
                line_end.forward_to_line_end()
                textbuffer.apply_tag_by_name(
                            self.LINE_SEARCH,
                            line_iter,
                            line_end)
            textbuffer.place_cursor(line_iter)

            # Move line mark
            textbuffer.move_mark_by_name(self.LINE_SEARCH, line_iter)

            # Scroll to insert
            line_mark = textbuffer.get_insert()
            textview.scroll_to_mark(line_mark, 0.2)

        selection = self.summary.get_selection().get_selected()[1]
        log_line = self.summary_liststore.get_value(selection, 4)
        latex_line = self.summary_liststore.get_value(selection, 2)
        _highlight_line(self.view_log, log_line)
        _highlight_line(self.view_latex, latex_line)

