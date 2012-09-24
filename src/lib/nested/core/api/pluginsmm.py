# -*- coding:utf-8 -*-
#
# Copyright (C) 2012, Carlos Jenkins <carlos@jenkins.co.cr>
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
Nested interface for plugin administration.
"""

from nested import *
from nested.utils import show_error, get_builder

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

class PluginsMM(object):
    """
    Plugin management interface.
    """

    def __init__(self, parent=None):
        """
        The object constructor.
        """

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'pluginsmm.glade')

        # Get the main objects
        self.plugins_dialog = go('plugins_dialog')
        self.plugins_view = go('plugins_view')

        # Configure interface
        if parent is not None:
            self.plugins_dialog.set_transient_for(parent)

    def admin(self, widget=None):
        """
        Runs the plugins management dialog.
        """
        response = self.plugins_dialog.run()
        if response == 0:
            self.plugins_dialog.hide()
            return False


        return self.admin()

