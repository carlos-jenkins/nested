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
This package provides line number drawing to PyGtk TextViews. This is a
refactoring from http://www.pygtk.org/pygtk2tutorial/sec-TextViewExample.html
"""

__all__ = ['LineNumbers']

import gtk
import pango

class LineNumbers(object):
    """Line number drawing object for PyGtk TextViews"""

    def __init__(self, view, zero=False, left=True):

        self._addition = 0 if zero else 1
        self._side = gtk.TEXT_WINDOW_LEFT if left else gtk.TEXT_WINDOW_RIGHT
        self._enabled = True
        self._view = view
        self._nlines = view.get_buffer().get_line_count()
        self._layout = None
        self._view.connect('expose_event', self._line_numbers_expose_cb)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self._line_numbers_expose_cb(self._view, None)
        else:
            self._view.set_border_window_size(self._side, 0)

    def _line_numbers_expose_cb(self, textview, event, data=None):
        """
        Show line numbers on the TextView.
        """

        # Ignore if disabled
        if not self._enabled:
            return False

        # Count lines and avoid rebuild of the layout
        textbuffer = textview.get_buffer()
        nlines = textbuffer.get_line_count()
        if nlines != self._nlines or self._layout is None:
            self._nlines = nlines

            # Create layout with lines
            layout = pango.Layout(textview.get_pango_context())
            layout.set_markup('\n'.join(
                    [str(x + self._addition) for x in range(self._nlines)])
                )
            layout.set_alignment(pango.ALIGN_RIGHT)
            self._layout = layout

        # Resize and clear border
        width = self._layout.get_pixel_size()[0]
        textview.set_border_window_size(self._side, width + 4)
        window = textview.get_window(self._side)
        window.clear()

        # Draw the line numbers
        y = -textview.window_to_buffer_coords(self._side, 2, 0)[1]
        textview.style.paint_layout(window=window,
                                    state_type=gtk.STATE_NORMAL,
                                    use_text=True,
                                    area=None,
                                    widget=textview,
                                    detail=None,
                                    x=2,
                                    y=y,
                                    layout=self._layout)
