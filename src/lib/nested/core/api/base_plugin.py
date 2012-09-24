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

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

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
    #  Unique identifier (authorprefix_name_version)
    #   e.g.: 'nested_base_1.0'
    uid = ''

    #  Name of the plugin. Single line, no dot at the end of line.
    #   e.g.: 'Nested base plugin'
    name = ''

    #  Version. Single line, no dot at the end of line.
    #   e.g.: '1.0'
    version = '1.0'

    #  Brief description. Single line, dot at the end of line.
    #   e.g.: 'Base plugin for Nested.'
    short_description = ''

    #  Large description . Multiple lines, dot at the end of line.
    #   e.g.: '''This is the base plugin class for Nested.'''
    large_description = ''''''

    #  Author or authors. Multiples lines, no dot at the end of line.
    #  Each author has his email in format "Author name <mail@foo.bar>".
    #   e.g.: '''Carlos Jenkins <carlos@jenkins.co.cr>'''
    authors = ''''''

    #  Website or url to version control system used by the creators
    #   e.g.: 'http://nestededitor.sourceforge.net/'
    website = ''

    def __init__(self, nested):
        """
        Generic constructor
        """
        self.nested = nested

    @classmethod
    def can_configure(cls):
        """
        Indicates if the plugin can load a configuration panel.
        The configuration should open when calling do_configure().
        """
        return False

    def on_enable(self):
        """
        Enable the plugin.
        This function is called when the user enables the plugin in the
        plugins administration dialog, just after the plugin instantiation.
        """
        logger.info(_('on_enable() called on NestedPlugin'))
        return

    def on_disable(self):
        """
        Disables the plugin.
        This function is called when the user disables the plugin in the
        plugins administration dialog. Close and free any resources here.
        """
        logger.info(_('on_disable() called on NestedPlugin'))
        return

    def on_exit(self):
        """
        Shutdown the plugin.
        This function is called when the user is quiting Nested.
        """
        logger.info(_('on_exit() called on NestedPlugin'))
        return

    def do_configure(self):
        """
        This function is called when the configuration panel for this plugin
        was requested by the user.
        """
        return


