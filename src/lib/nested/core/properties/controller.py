# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2013 Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.


"""
Nested 3 document properties dialog controller.
"""

from os.path import join
from gi.repository import Gtk

from nested.context import *
log = logger.getLogger(__name__)
res = respath(__file__)

#logger.set_levels(logger.INFO)
#log.info(__name__)

class Properties(object):

    def __init__(self, parent=None):
        """
        Build document properties GUI
        """

        # Build GUI from Glade file
        self.builder = Gtk.Builder()
        self.glade_file = join(res, 'properties.glade')
        self.builder.add_from_file(self.glade_file)

        # Get objects
        go = self.builder.get_object
        self.properties = go('properties')

        # Connect signals
        self.builder.connect_signals(self)

    def run(self):
        while True:
            res = self.properties.run()
            if self.validate():
                return

    def validate(self):
        return False
