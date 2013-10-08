# -*- coding: utf-8 -*-
#       lines.py - Add line number drawing to PyGtk TextViews.
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

"""@package lines
This package provides line number drawing to PyGtk TextViews. This
is a refactoring from http://www.pygtk.org/pygtk2tutorial/sec-TextViewExample.html
"""

import gtk

class LineNumbers(object):
    """Line number drawing object for PyGtk TextViews"""
        
    def __init__(self, view):
        
        self._enabled = True
        self._view = view
        self._buffer = self._view.get_buffer()
        self._view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 30)
        self._view.connect('expose_event', self._line_numbers_expose_cb)
    
    @property
    def enabled(self):
        return self._enabled
    
    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self._view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 30)
        else:
            self._view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 0)
    
    def _line_numbers_expose_cb(self, widget, event, user_data=None):
        """
        Show line numbers on the TextView.
        """

        if not self._enabled:
            return False
        
        text_view = widget
  
        # See if this expose is on the line numbers window
        left_win = text_view.get_window(gtk.TEXT_WINDOW_LEFT)
        right_win = text_view.get_window(gtk.TEXT_WINDOW_RIGHT)

        if event.window == left_win:
            type = gtk.TEXT_WINDOW_LEFT
            target = left_win
        elif event.window == right_win:
            type = gtk.TEXT_WINDOW_RIGHT
            target = right_win
        else:
            return False
  
        first_y = event.area.y
        last_y = first_y + event.area.height

        x, first_y = text_view.window_to_buffer_coords(type, 0, first_y)
        x, last_y = text_view.window_to_buffer_coords(type, 0, last_y)

        numbers = []
        pixels = []
        count = self._get_lines(widget, first_y, last_y, pixels, numbers)
  
        # Draw fully internationalized numbers!
        layout = widget.create_pango_layout('')
  
        for i in range(count):
            x, pos = text_view.buffer_to_window_coords(type, 0, pixels[i])
            str = '%d' % (numbers[i] + 1)
            layout.set_text(str)
            widget.style.paint_layout(target, widget.state, False,
                                      None, widget, None, 2, pos + 2, layout)

        # Don't stop emission, need to draw children
        return False

    def _get_lines(self, text_view, first_y, last_y, buffer_coords, numbers):
        """
        Return number of lines of a TextView
        """
        # Get iter at first y
        iter, top = text_view.get_line_at_y(first_y)

        # For each iter, get its location and add it to the arrays.
        # Stop when we pass last_y
        count = 0
        size = 0

        while not iter.is_end():
            y, height = text_view.get_line_yrange(iter)
            buffer_coords.append(y)
            line_num = iter.get_line()
            numbers.append(line_num)
            count += 1
            if (y + height) >= last_y:
                break
            iter.forward_line()

        return count
