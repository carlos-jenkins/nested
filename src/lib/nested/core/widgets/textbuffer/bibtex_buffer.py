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
This package contains the clases for syntax highlight of BibTeX markup.
"""

import pango
from nested.bibmm.bibtexdef import all_fields, bibtex_entries
from .markup_buffer import Pattern, MarkupDefinition, MarkupBuffer

class BibTeXSyntax(object):
    """BibTeX syntax highlight class."""
    def __init__(self):

        # Styles
        self.styles = {
            'types'     :       {'weight'       : pango.WEIGHT_BOLD,
                                 'foreground'   : 'black'},
            'ids'       :       {'weight'       : pango.WEIGHT_ULTRABOLD,
                                 'scale'        : pango.SCALE_LARGE,
                                 'foreground'   : 'darkblue'},
            'bracket'   :       {'weight'       : pango.WEIGHT_ULTRABOLD,
                                 'scale'        : pango.SCALE_X_LARGE,
                                 'foreground'   : 'red'},
            'fields'    :       {'foreground'   : '#C95200',
                                 'underline'    : pango.UNDERLINE_SINGLE},
            'equal'     :       {'weight'       : pango.WEIGHT_BOLD,
                                 'foreground'   : '#8000C9'},
            'comment'   :       {'foreground'   : '#6D6D6D'},
            }

        entries = bibtex_entries.keys()
        # Patterns
        self.patterns = [
            # Types
            Pattern(r'^(?P<at>@)(?P<type>' + '|'.join(entries) + ')', [(1, 'types'), (2, 'types')], flags='I'),
            # IDS
            Pattern(r'^(?P<at>@)(?P<type>' + '|'.join(entries) + r')\s*(?P<open>\{)\s*(?P<id>\S+)\s*,\s*\n',
                    [(3, 'bracket'), (4, 'ids')], flags='I'),
            # Close bracket
            Pattern(r'^\s*(?P<close>\})\s*\n', [(1, 'bracket')]),
            # Fields
            Pattern(r'\s*(?P<fields>' + '|'.join(all_fields) + r')\s*(?P<equal>=)', [(1, 'fields'), (2, 'equal')]),
            # Comment
            Pattern(r'^(\%.*)$', [(1, 'comment')]),
            ]

        # Create lexer
        self.lang = MarkupDefinition(self.patterns)


class BibTeXBuffer(MarkupBuffer):
    """
    Custom buffer with syntax highlight for BibTeX markup.
    """

    def __init__(self, table=None):
        """
        Object constructor:
            - table, as in TextBuffer().
        """
        syntax_highlight = BibTeXSyntax()
        lang = syntax_highlight.lang
        styles = syntax_highlight.styles
        MarkupBuffer.__init__(self, table, lang=lang, styles=styles)
