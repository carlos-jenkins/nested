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
Python buffer for code visualization.
"""

__all__ = ['CodeView']

import locale
import pango

from gtk import TextView
from lines import LineNumbers
from margin import Margin
from gtkspellcheck import SpellChecker

class CodeView(TextView):
    """
    Custom view with some code visualization facilities.
    """

    # Initialization and configuration
    def __init__(self, buffer=None, config=None):
        """
        Object constructor:
            - buffer, as in TextView().
        """
        TextView.__init__(self, buffer)

        # Defaults
        self.modify_font(pango.FontDescription('DejaVu Sans Mono 10'))

        if config:
            print('Configuration prototype')

        self._lines = LineNumbers(self)
        self._margin = Margin(self)
        self._spellcheck = SpellChecker(self, locale.getdefaultlocale()[0])

        self.show()

    def set_buffer(self, buffer):
        """
        Overrides the set_buffer parent method.
        """
        super(CodeView, self).set_buffer(buffer)
        self._spellcheck.buffer_initialize()

    # Decorations
    def show_lines(state):
        self._lines.enabled = state

    def show_margin(state):
        self._margin.enabled = state

    def show_invisible_chars(state):
        raise Exception('Unimplemented')

    def show_spellcheck(state):
        self._spellcheck.enabled = state

    # Helpers
    def increase_font_size(self, widget):
        """
        Increase font size by one the of content entry.
        """
        self.change_font_size(1)

    def decrease_font_size(self, widget):
        """
        Decrease font size by one the of content entry.
        """
        self.change_font_size(-1)

    def change_font_size(self, amount):
        """
        Change font size of content entry.
        """
        font = self.get_pango_context().get_font_description()
        new_size = font.get_size() + (amount * pango.SCALE)
        if new_size < pango.SCALE:
            new_size = pango.SCALE
        font.set_size(new_size)
        self.modify_font(font)

    def change_colors(self, text, background):
        """
        Change the base theme of the textview.
        """
        self.modify_text(gtk.STATE_NORMAL, self.get_color(text))
        self.modify_base(gtk.STATE_NORMAL, self.get_color(background))

    # Utilities
    def get_color(foo):
        """
        Accept almost any representation of a color and return a gtk.gdk.Color.
        """
        if isinstance(foo, gtk.gdk.Color):
            return foo
        if isinstance(foo, basestring):
            return gtk.gdk.color_parse(foo)
        if isinstance(foo, tuple):
            one, two, tree = foo
            if isinstance(one, int):
                return gtk.gdk.Color(*foo)
            if isinstance(one, float):
                return gtk.gdk.color_from_hsv(*foo)
        return None
