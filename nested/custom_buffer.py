# -*- coding: utf-8 -*-
#       custom_buffer.py - Custom PyGtk TextBuffer for Nested
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

"""@package custom_buffer
This package contains the clases for syntax highlight plus a custom buffer 
for PyGtk TextView with syntax highlight, time based undo/redo and helper functions.
"""

from modules.buffers.markup_buffer import Pattern, MarkupDefinition, MarkupBuffer
import txt2tags
import pango

class Txt2tagsSyntax(object):
    """Txt2tags syntax highlight class."""
    def __init__(self):
    
        self.bank = txt2tags.getRegexes()
        
        # Styles
        self.styles = {
            'bold':             {'weight'       : pango.WEIGHT_BOLD},
            'italic':           {'style'        : pango.STYLE_ITALIC},
            'underline':        {'underline'    : pango.UNDERLINE_SINGLE},
            'strikethrough':    {'strikethrough': True},
            'gray':             {'foreground'   : '#6D6D6D'},
            'red':              {'foreground'   : 'red'},
            'green':            {'foreground'   : 'darkgreen'},
            'raw':              {'font'         : 'Oblique'},
            'verbatim':         {'font'         : 'monospace'},
            'tagged':           {},
            'link':             {'foreground'   : 'blue',
                                 'underline'     : pango.UNDERLINE_SINGLE,},
            'highlight':        {'background'   : 'yellow'},
            'quote':            {'background'   : '#6D6D6D'}
            }
        
        # Generate styles for titles
        sizes = [
            pango.SCALE_XX_LARGE,
            pango.SCALE_X_LARGE,
            pango.SCALE_LARGE,
            pango.SCALE_MEDIUM,
            pango.SCALE_SMALL,
            ]
        for level, size in enumerate(sizes):
            style = {'weight': pango.WEIGHT_ULTRABOLD,
                    'scale': size}
            name = 'title%s' % (level+1)
            self.styles[name] = style
        
        # Generate patterns for titles
        title_patterns = []
        ''' # Disabled, because Nested don't really need those and create a lot of trouble
        title_style = [(1, 'gray'), (3, 'gray'), (4, 'gray')]
        titskel = r'^ *(%s)(%s)(\1)(\[[\w-]*\])?\s*$'
        for level in range(1, 6):
            title_pattern    = titskel % ('[=]{%s}'%(level),'[^=]|[^=].*[^=]')
            numtitle_pattern = titskel % ('[+]{%s}'%(level),'[^+]|[^+].*[^+]')
            style_name = 'title%s' % level
            title = Pattern(title_pattern, title_style + [(2, style_name)])
            numtitle = Pattern(numtitle_pattern, title_style + [(2, style_name)])
            title_patterns += [title, numtitle]
        '''
        
        # Patterns
        self.patterns = [
            # Bold
            self.get_pattern('\*', 'bold'),
            # Underline
            self.get_pattern('_', 'underline'),
            # Italic
            self.get_pattern('/', 'italic'),
            # Strikethrough
            self.get_pattern('-', 'strikethrough'),
            # Normal list
            Pattern(r"^ *(\-) [^ ].*$", [(1, 'red'), (1, 'bold')], name='olist'),
            # Numbered list
            Pattern(r"^ *(\+) [^ ].*$", [(1, 'red'), (1, 'bold')], name='ulist'),
            # Comment
            Pattern(r'^(\%.*)$', [(1, 'gray')]),
            # Line
            Pattern(r'^[\s]*([_=-]{20,})[\s]*$', [(1, 'bold')]),
            # Raw
            self.get_pattern('"', 'raw'),
            # Verbatim
            self.get_pattern('`', 'verbatim'),
            # Tagged
            self.get_pattern("'", 'tagged'),
            # Linebreak
            Pattern(r'(@@)', [(1, 'gray')]),
            # Image
            Pattern(r'(\["")(%s)("")(\.%s)(\?\d+)?(\])' % (r'\S.*?\S|\S', r'png|jpe?g|gif|eps|bmp'),
                [(1, 'gray'), (2, 'green'), (3, 'gray'), (4, 'green'), (5, 'gray'), (6, 'gray')], flags='I'),
            # Named link
            Pattern(r'(\[)(.*?)\s("")(\S.*?\S)(""\])', [(1, 'gray'), (2, 'link'), (3, 'gray'), (4, 'gray'), (5, 'gray')], flags='LI'),
            # Link : Use txt2tags link guessing mechanism
            Pattern('OVERWRITE', [(0, 'link')], regex=self.bank['link'], name='link'),
            ] + title_patterns
        
        # Create lexer
        self.lang = MarkupDefinition(self.patterns)

    def get_pattern(self, char, style):
        # original strikethrough in txt2tags: r'--([^\s](|.*?[^\s])-*)--'
        # txt2tags docs say that format markup is greedy, but
        # that doesn't seem to be the case

        # Either one char, or two chars with (maybe empty) content between them.
        # In both cases no whitespaces between chars and markup.
        regex = r'(%s%s)(\S|.*?\S%s*)(%s%s)' % ((char, ) * 5)
        group_style_pairs = [(1, 'gray'), (2, style), (3, 'gray')]
        return Pattern(regex, group_style_pairs, name=style)



class CustomBuffer(MarkupBuffer):
    """
    Custom buffer for PyGtk TextView with several options for syntax 
    highlight and undo/redo capabilities.
    """
    
    def __init__(self, table=None, syntax='txt2tags'):
        """
        Object constructor:
            - table, as in TextBuffer().
            - syntax, a string identifying the syntax highlight.
        """
        
        # Use syntax highlight
        lang = None
        styles= {}

        if syntax == 'txt2tags':
            syntax_highlight = Txt2tagsSyntax()
            lang = syntax_highlight.lang
            styles = syntax_highlight.styles
            
        elif syntax == 'bibtex':
            syntax = Txt2tagsSyntax()
            lang = syntax_highlight.lang
            styles = syntax_highlight.styles
        
        MarkupBuffer.__init__(self, table, lang=lang, styles=styles)

    def get_all_text(self):
        """
        Get all text currently in the buffer, in UTF-8. 
        Note: Can't believe TextBuffer doesn't have this method :S
        """
        return self.get_text(self.get_start_iter(), self.get_end_iter()).decode('utf-8')

    def get_selection_bounds(self):
        """Return the start and end selection iters"""
        
        native = MarkupBuffer.get_selection_bounds(self)
        
        if not native:
            start_iter = self.get_iter_at_mark(self.get_insert())
            end_iter = start_iter
        else:
            start_iter, end_iter = native
        
        return start_iter, end_iter

