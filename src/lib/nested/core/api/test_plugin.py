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
Test plugin for PluginsMM.
Compatibility: 1.0
"""

from nested import *
from nested.utils import show_info

from .base_plugin import NestedPlugin

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

class NestedTestPlugin(NestedPlugin):

    uid = 'nested_test_1.0'
    name = 'Nested test plugin'
    version = '1.0'
    short_description = 'Test plugin for Nested.'
    large_description = '''This is the test plugin class for Nested.'''
    authors = '''Carlos Jenkins <carlos@jenkins.co.cr>'''
    website = 'http://nestededitor.sourceforge.net/'

    @classmethod
    def can_configure(self):
        return True

    def on_enable(self):
        show_info('The plugin was enabled.', self.nested.main)
        return

    def on_disable(self):
        show_info('The plugin was disabled.', self.nested.main)
        return

    def on_exit(self):
        logger.info(_('on_exit() called on NestedTestPlugin'))
        return

    def do_configure(self):
        show_info('This is the configuration panel.', self.nested.main)
