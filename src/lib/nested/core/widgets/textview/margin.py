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
This package provides margin drawing to PyGtk TextViews.
"""

import gtk
import cairo
import pango

class Margin(object):
    """Margin drawing object for PyGtk TextViews"""

    def __init__(self, view, chars=80, color=(0.5, 0.5, 0.5)):

        self.chars = chars
        self.color = color
        self.enabled = True

        self._view = view
        self._chars = 'm' * chars
        self._view.connect('expose_event', self._margin_expose_cb)

    def _margin_expose_cb(self, widget, event, user_data=None):
        """
        Show a margin on the TextView.
        """

        if not self.enabled:
            return False

        # Get the context
        cc = widget.get_window(gtk.TEXT_WINDOW_TEXT).cairo_create()
        width, height = widget.window.get_size()

        # Calculate margin
        margin = widget.create_pango_layout(self._chars).get_pixel_size()[0]

        # Draw the margin
        cc.set_antialias(cairo.ANTIALIAS_NONE)
        cc.set_line_width(1.0)
        cc.set_source_rgb(*self.color)
        cc.move_to(margin, 0)
        cc.rel_line_to(0, height)
        cc.stroke()

        return False
