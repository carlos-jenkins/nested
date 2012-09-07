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
Module to process footnotes
"""

import re

def process_footnotes(section, target):
    """Process footnotes in a section"""

    class Namespace:
        pass

    def _format_footmarks_xhtmls(lines, title):
        """Format footmarks to the XHTML Strict format"""
        template = "''<a class=\"footnotemark\" href=\"#{0}_fn{1}\">[{1}]</a>''"
        fn_regex = re.compile(u'°°_')

        ns = Namespace()
        ns.fn_count = 1

        def _footmarks_xhtmls_replacer(m):
            """Regex replacement funtion for XHTML Strict format"""
            fn_link = template.format(title, str(ns.fn_count))
            ns.fn_count = ns.fn_count + 1
            return fn_link

        formatted_footmarks = []
        for line in lines:
            formatted_line = fn_regex.sub(_footmarks_xhtmls_replacer, line)
            formatted_footmarks.append(formatted_line)
        return formatted_footmarks

    def _format_footnotes_xhtmls(footnotes, title):
        """Format footnotes to the XHTML Strict format"""
        if not footnotes:
            return []
        formatted_footnotes = ["''' <div class=\"footnotes\"><ol>"]
        count = 1
        for footnote in footnotes:
            id_attr = title + '_fn' + str(count)
            formatted_footnotes.append(
                    "''<li id=\"" + id_attr + "\">''" + footnote + " ''</li>''")
            count = count + 1
        formatted_footnotes.append("''' </ol></div>")
        return formatted_footnotes

    def _format_footmarks_tex(lines):
        """Format footmarks to the TeX/LaTeX format"""
        formatted_footmarks = []
        for line in lines:
            formatted_footmarks.append(line.replace('°°_', r"''\footnotemark{}''"))
        return formatted_footmarks

    def _format_footnotes_tex(footnotes):
        """Format footnotes to the TeX/LaTeX format"""
        if not footnotes:
            return []
        formatted_footnotes = []
        counter = 0
        for footnote in footnotes:
            formatted_footnotes.append(
                            r"''\stepcounter{footnote}\footnotetext{''" +
                            footnote + " ''}''")
            counter = counter + 1
        formatted_footnotes = ['',
                            r"''\addtocounter{footnote}{-%i}''" % counter] +
                            formatted_footnotes + ['']
        return formatted_footnotes

    lines = section.split('\n')

    normal_lines = []
    footnotes = []
    in_footnote = False
    target_comments = re.compile(
                        '%(?P<alias>xhtmls|html|tex|latex|pdf|txt|text)%')
    special = []

    # Separate normal lines from footnote lines
    for line in lines:
        if line.startswith('_°° '):
            footnotes.append(line[4:].strip())
            in_footnote = True
        elif in_footnote and line.startswith('    '):
            full_line = footnotes.pop() + ' ' + line[4:].strip()
            footnotes.append(full_line)
        else:
            in_footnote = False
            if footnotes and target_comments.match(line):
                special.append(line)
            else:
                normal_lines.append(line)

    # Format footnotes
    if target == 'xhtmls':
        title = normal_lines[0].split('[')[1][:-1]
        target_footmarks = _format_footmarks_xhtmls(normal_lines, title)
        target_footnotes = _format_footnotes_xhtmls(footnotes, title)
    elif target == 'tex':
        target_footmarks = _format_footmarks_tex(normal_lines)
        target_footnotes = _format_footnotes_tex(footnotes)
    lines = target_footmarks + target_footnotes + special + ['']

    return '\n'.join(lines)
