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
Calculator plugin for Nested.
"""

from nested import *
from nested.utils import get_builder
from .engine import evaluate, ParseException

import os
import logging
import gettext

import gtk
import pango

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

BTNS = {
            # Common
            'sub'    : '-',
            'sum'    : '+',
            'div'    : '/',
            'mult'   : '*',

            # User variables
            'equal'  : '=',
            'xvar'   : 'x',
            'yvar'   : 'y',
            'zvar'   : 'z',

            # Program variables
            'e'      : 'e',
            'pi'     : 'pi',
            'ans'    : 'ans',

            # Others
            'pow'    : '^',
            'opar'   : '(',
            'cpar'   : ')',

            # Numbers
            'num0'   : '0',
            'num1'   : '1',
            'num2'   : '2',
            'num3'   : '3',
            'num4'   : '4',
            'num5'   : '5',
            'num6'   : '6',
            'num7'   : '7',
            'num8'   : '8',
            'num9'   : '9',
            'dot'    : '.',
        }

log_format = '''\
> {}
{}
'''

class Calculator(object):
    """
    Generic calculator class.
    """

    def __init__(self, textview=None):
        """
        The object constructor.
        """

        # "Insert" feature
        self.last = ''
        self.textview = textview

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'calculator.glade')

        # Get the main objects
        self.main = go('main')
        self.log = go('log')
        self.entry = go('entry')

        # Configure interface
        self.log.modify_font(pango.FontDescription('DejaVu Sans Mono 10'))
        self.entry.modify_font(pango.FontDescription('DejaVu Sans Mono 15'))
        self.entry.grab_focus()

        # Connect signals
        self.builder.connect_signals(self)

    def _btn_press_cb(self, widget):
        """
        Insert text into entry.
        """
        name = gtk.Buildable.get_name(widget)
        insert = BTNS[name]
        cursor = self.entry.get_position()
        self.entry.insert_text(insert, cursor)
        self.entry.set_position(cursor + len(insert))

    def _evaluate_cb(self, widget):
        """
        Evaluate entry content.
        """
        # Evaluate expression
        expr = self.entry.get_text()
        try:
            result = evaluate(expr)
            self.last = result
            content = log_format.format(expr, result)
            self.entry.set_text('')
        except ParseException as err:
            err_msg = '\n'.join([
                        '  ' + ' ' * (err.column - 1) + '^',
                        _('Syntax error at character {}.').format(err.column)])
            content = log_format.format(err.line, err_msg)

        # Load result
        buff = self.log.get_buffer()
        end = buff.get_end_iter()
        buff.insert(end, content)
        buff.place_cursor(end)
        line_mark = buff.get_insert()
        self.log.scroll_to_mark(line_mark, 0.0)

    def _clear_cb(self, widget):
        """
        Clear the expression entry.
        """
        self.entry.set_text('')

    def _backspace_cb(self, widget):
        """
        Emulate a backspace on the entry.
        """
        etr = self.entry
        position = etr.get_position()
        if position == 0: return False
        content = etr.get_text()
        etr.set_text(content[:position - 1] + content[position:])
        etr.set_position(max(position - 1, 0))

    def _load_cb(self, widget):
        """
        Load currently selected line from attached textview.
        """
        if self.textview is None:
            return False

        buff = self.textview.get_buffer()
        # Selection
        if buff.get_has_selection():
            start, end = buff.get_selection_bounds()
            selected = buff.get_text(start, end).strip()
            if not selected:
                return False
            line = selected.split('\n')[0].strip()
        # Line at cursor
        else:
            start = buff.get_iter_at_mark(buff.get_insert())
            start.set_line_offset(0)
            end = start.copy()
            end.forward_to_line_end()
            if start.get_line() == end.get_line():
                line = buff.get_text(start, end).strip()
            else:
                line = ''

        if not line:
            return False

        etr = self.entry
        position = etr.get_position()
        content = etr.get_text()
        etr.set_text(content[:position] + line + content[position:])
        etr.set_position(position + len(line))

    def _insert_cb(self, widget):
        """
        Insert calculator history at textbuffer insert.
        """
        if self.textview is None:
            return False

        buff = self.log.get_buffer()
        # Selection
        if buff.get_has_selection():
            start, end = buff.get_selection_bounds()
            text = buff.get_text(start, end).strip()
            if not text:
                return False
        # Last result
        else:
            text = str(self.last)

        if not text:
            return False

        view = self.textview.get_buffer()
        view.insert_at_cursor(text)
