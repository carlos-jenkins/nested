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
This package contains a base custom buffer with improved operations.
"""

import pango
from gtk import TextBuffer

class CustomBuffer(TextBuffer):
    """
    Improved custom text buffer for Nested.
    """

    def __init__(self, table=None):
        """
        Object constructor:
            - table, as in vanilla TextBuffer().
        """
        TextBuffer.__init__(self, table)

    def get_all_text(self):
        """
        Get all text currently in the buffer, in UTF-8.
        Note: Can't believe TextBuffer doesn't have this method :S
        """
        return self.get_text(self.get_start_iter(), self.get_end_iter()).decode('utf-8')

    def get_selection_bounds(self):
        """
        Return the start and end selection iters.
        """

        native = TextBuffer.get_selection_bounds(self)

        if not native:
            start_iter = self.get_iter_at_mark(self.get_insert())
            end_iter = start_iter
        else:
            start_iter, end_iter = native

        return start_iter, end_iter

