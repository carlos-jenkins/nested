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
Base plugin class for Nested.
Compatibility: 1.0
"""

from nested import *
from nested.utils import *

class NestedPlugin(object):
    """
    Base class for creating Nested plugins.

    This class provides hooks for the following situations:

    - Initialization:
        - GUI Access.
        - Event connection.
    - Live cycle:
        - Enabling.
        - Disabling.
        - Configuration.
    - File managment:
        - Save file hook.
        - Load file hook.
    - Publishing:
        - Pre-assembly hook.
        - Pre-publishing hook.
        - Post-publishing hook.
    - Configuration:
        - Nested configuration changed.
    """

    # Metadata
    #  Unique identifier
    uid = "nested_base_1.0"
    #  Name of the plugin. Single line, no dot at the end of line.
    name = 'Nested base plugin'
    #  Version. Single line, no dot at the end of line.
    version = '1.0'
    #  Brief description. Single line, dot at the end of line.
    short_description = 'Base plugin for Nested.'
    #  Large description . Multiple lines, dot at the end of line.
    large_description = '''This is the base plugin class for Nested.'''
    #  Author or authors. Multiples lines, no dot at the end of line.
    #  Each author has his email in format "Author name <mail@foo.bar>".
    authors = '''Carlos Jenkins <carlos@jenkins.co.cr>'''
    #  Website or url to version control system used by the creators
    website = 'http://nestededitor.sourceforge.net/'

    def on_enable(self):
        print('on_enable')
