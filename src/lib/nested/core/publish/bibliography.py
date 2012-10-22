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
Module to process bibliography
"""

from nested import *

import re
import os
import shutil
import logging
import gettext
from os.path import isfile


WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext


def copybib(src, dst):
    """Copy a extended bibliography file to some destination"""
    if isfile(dst):
        os.remove(dst)
    if isfile(src):
        shutil.copyfile(src, dst)
    if isfile(dst):
        lines = []
        with open(dst, 'r') as f:
            lines = f.readlines()
        with open(dst, 'w') as f:
            f.write(''.join(
                    [l for l in lines if not l.strip().startswith('%')])
                )


def process_bibliography(section, target, style='apalike', bib='bib'):
    """Process bibliography in a section"""

    cite = re.compile(r'{\|(?P<key>\w+)\|}')
    cite_repl = r"''\\cite{\g<key>}''"
    refs = re.compile(r'^ *%%bib\s*$', re.I + re.M)
    refs_repl = ("''\\\\renewcommand\\\\refname{{\\\\vskip -1cm}}''\n"
                 "''\\\\bibliographystyle{{{style}}}''\n"
                 "''\\\\bibliography{{{bib}}}''")

    def _format_bibliography_xhtmls(section):
        """Format bibliography to the XHTML Strict format"""
        logger.error('Unimplemented')
        return section

    def _format_bibliography_tex(section):
        """Format bibliography to the TeX/LaTeX format"""
        formatted, num_cites = cite.subn(cite_repl, section)
        logger.debug('I had found {} citations.'.format(num_cites))
        if(num_cites > 0):
            return refs.sub(refs_repl.format(style=style, bib=bib), formatted)
        return formatted

    # Format footnotes
    if target == 'xhtmls':
        target_section = _format_bibliography_xhtmls(section)
    elif target == 'tex':
        target_section = _format_bibliography_tex(section)

    return target_section
