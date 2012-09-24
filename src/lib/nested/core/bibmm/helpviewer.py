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
HTML help viewer module for BibMM.
"""

from nested import *
from nested.utils import get_builder

import os
import logging
import gettext

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

class HelpViewer(object):
    """
    Simple widget to watch help documentation in HTML.
    """

    def __init__(self, parent=None):
        """
        The object constructor.
        """
        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'help.glade')

        # Get the main objects
        self.help_dialog = go('help_dialog')
        help_holder = go('help_holder')

        self.help_view = None
        try:
            import webkit
            self.help_view = webkit.WebView()
            help_holder.add_with_viewport(self.help_view)
            self.help_view.show()
        except ImportError:
            logger.warning('Unable to import webkit module. Entries help will be unavailable.')
            windows_warning = _('''\
Help viewer is not currently supported for Microsoft Windows.
If you need this functionality you can help the developer by packaging
pywebkitgtk for Windows: http://code.google.com/p/pywebkitgtk/\
''')
            placeholder = gtk.Label(windows_warning)
            help_holder.add_with_viewport(placeholder)
            placeholder.show()

        # Configure interface
        if parent is not None:
            self.help_dialog.set_transient_for(parent)

        # Connect signals
        self.builder.connect_signals(self)

    def load_help(self, entry):
        """
        Load help for given entry id.
        """
        if self.help_view is None:
            return

        # Find help file
        help_file = 'entry_{}.html'.format(entry)
        help_path = os.path.join(WHERE_AM_I, 'help', context_lang, help_file)
        if not os.path.isfile(help_path):
            help_path = os.path.join(WHERE_AM_I, 'help', 'en_US', help_file)

        # Load help file
        if not os.path.isfile(help_path):
            self.help_view.load_html_string(
                _('<p>File {} not found.</p>').format(help_path), 'file:///')
        else:
            self.help_view.load_uri('file:///' + help_path)

        # Run help dialog
        self.help_dialog.run()
        self.help_dialog.hide()

    def _back_cb(self, widget):
        """
        Go back in help viewer.
        """
        if self.help_view is not None:
            self.help_view.go_back()
        return False

    def _forward_cb(self, widget):
        """
        Go forward in help viewer.
        """
        if self.help_view is not None:
            self.help_view.go_forward()
        return False
