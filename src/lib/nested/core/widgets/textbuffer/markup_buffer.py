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
This module provides a syntax highlight buffer for PyGtk TextView and associated
classes.

Markup buffer was adapted from t2t_highlight.py from the Software RedNotebook
by Jendrik Seipp:

    http://rednotebook.sourceforge.net/

Which took the ideas and some code from the highlighting module PyGTKCodeBuffer
by Hannes Matuschek:

    http://code.google.com/p/pygtkcodebuffer/
"""

import re
from .undo_buffer import UndoBuffer as TextBuffer

class Tag(object):
    def __init__(self, start, end, tagname, rule):
        self.start = start
        self.end = end
        self.name = tagname
        self.rule = rule

    def list(self):
        return [self.start, self.end, self.name]


class TagGroup(list):
    @property
    def min_start(self):
        return min([tag.start for tag in self], key=lambda i: i.get_offset()).copy()

    @property
    def max_end(self):
        return max([tag.end for tag in self], key=lambda i: i.get_offset()).copy()

    def sort(self):
        key = lambda tag: (tag.start.get_offset(), -tag.end.get_offset(), tag.name)
        list.sort(self, key=key)

    @property
    def rule(self):
        if len(self) == 0:
            return 'NO ITEM'
        return self[0].rule

    def list(self):
        return map(lambda g: g.list(), self)


class Pattern(object):
    """
    A pattern object allows a regex-pattern to have
    subgroups with different formatting
    """
    def __init__(self, pattern, group_tag_pairs, regex=None, flags="",
                        overlap=False, name='unnamed'):
        self.overlap = overlap
        self.name = name

        # assemble re-flag
        flags += "ML"
        flag = 0

        for char in flags:
            if char == 'M': flag |= re.M
            if char == 'L': flag |= re.L
            if char == 'S': flag |= re.S
            if char == 'I': flag |= re.I
            if char == 'U': flag |= re.U
            if char == 'X': flag |= re.X

        if regex:
            self._regexp = regex
        else:
            # compile re
            try:
                self._regexp = re.compile(pattern, flag)
            except re.error, e:
                raise Exception("Invalid regexp \"%s\": %s" % (pattern, e))

        self.group_tag_pairs = group_tag_pairs

    def __call__(self, txt, start, end):
        m = self._regexp.search(txt)
        if not m: return None

        tags = TagGroup()

        for group, tag_name in self.group_tag_pairs:
            group_matched = bool(m.group(group))
            if not group_matched:
                continue
            mstart, mend = m.start(group), m.end(group)
            s = start.copy(); s.forward_chars(mstart)
            e = start.copy(); e.forward_chars(mend)
            tag = Tag(s, e, tag_name, self.name)
            tags.append(tag)

        return tags


class MarkupDefinition(object):

    def __init__(self, rules):
        self.rules = rules
        self.highlight_rule = None

    def __call__(self, buf, start, end):

        txt = buf.get_slice(start, end)

        tag_groups = []

        rules = self.rules[:]
        if self.highlight_rule:
            rules.append(self.highlight_rule)

        # search min match
        for rule in rules:
            # search pattern
            tags = rule(txt, start, end)
            while tags:
                tag_groups.append(tags)
                subtext = buf.get_slice(tags.max_end, end)
                tags = rule(subtext, tags.max_end, end)

        tag_groups.sort(key=lambda g: (g.min_start.get_offset(), -g.max_end.get_offset()))

        return tag_groups


class MarkupBuffer(TextBuffer):

    def __init__(self, table=None, lang=None, styles={}):
        TextBuffer.__init__(self, table)

        # update styles with user-defined
        self.styles = styles

        # create tags
        for name, props in self.styles.items():
            style = {}
            style.update(props)
            self.create_tag(name, **style)

        # store lang-definition
        self._lang_def = lang

        self.overlaps = ['bold', 'italic', 'underline', 'strikethrough',
                         'highlight', 'ulist', 'olist']

        self.connect_after('insert-text', self._markup_on_insert_text)
        self.connect_after('delete-range', self._markup_on_delete_range)

    def set_search_text(self, text):
        if not text:
            self._lang_def.highlight_rule = None
        else:
            self._lang_def.highlight_rule = Pattern(r'(%s)' % re.escape(text),
                    [(1, 'highlight')], name='highlight', flags='I', overlap=True)
        self.update_syntax(self.get_start_iter(), self.get_end_iter())

    def get_slice(self, start, end):
        """We have to search for the regexes in utf-8 text"""
        slice_text = TextBuffer.get_slice(self, start, end)
        slice_text = slice_text.decode('utf-8')
        return slice_text

    def _markup_on_insert_text(self, buf, it, text, length):

        end = it.copy()
        start = it.copy()
        start.backward_chars(length)

        self.update_syntax(start, end)

    def _markup_on_delete_range(self, buf, start, end):
        start = start.copy()

        self.update_syntax(start, start)

    def remove_all_syntax_tags(self, start, end):
        """Remove all the known tags only"""
        for style in self.styles:
            self.remove_tag_by_name(style, start, end)

    def apply_tags(self, tags):
        for mstart, mend, tagname in tags.list():
            # apply tag
            self.apply_tag_by_name(tagname, mstart, mend)

    def update_syntax(self, start, end):
        """ More or less internal used method to update the
            syntax-highlighting. """
        '''
        Use two categories of rules: one-line and multiline

        Before running multiline rules: Check if e.g. - is present in changed string
        '''

        # Just update from the start of the first edited line
        # to the end of the last edited line, because we can
        # guarantee that there's no multiline rule
        start_line_number = start.get_line()
        start_line_iter = self.get_iter_at_line(start_line_number)
        start = start_line_iter

        end.forward_to_line_end()

        # remove all tags from start to end
        self.remove_all_syntax_tags(start, end)

        tag_groups = self._lang_def(self, start, end)

        min_start = start.copy()

        for tags in tag_groups:
            if tags.rule == 'highlight':
                self.apply_tags(tags)

            elif min_start.compare(tags.min_start) in [-1, 0]:
                # min_start is left or equal to tags.min_start
                self.apply_tags(tags)

                if tags.rule in self.overlaps:
                    min_start = tags.min_start
                else:
                    min_start = tags.max_end

    def refresh(self):
        """Refresh the entire buffer"""
        self.update_syntax(self.get_start_iter(), self.get_end_iter())
