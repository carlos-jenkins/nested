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
Python buffer for code visualitation.
"""

__all__ = ['CodeBuffer']

from .markup_buffer import MarkupBuffer

class CodeBuffer(MarkupBuffer):
    """
    Custom view with some code facilities.
    """
    def __new__(cls, syntax):

        if syntax == 'txt2tags':
            from .txt2tags_buffer import Txt2tagsBuffer
            return Txt2tagsBuffer

        if syntax == 'bibtex':
            from .bibtex_buffer import BibTeXBuffer
        print "creating a new season %s" % season
        return Season.seasons[season]()
