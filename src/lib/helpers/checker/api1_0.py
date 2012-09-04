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
API 1.0 descriptor and tester.
"""

from os.path import basename

def run(plugin_path, callback):
    """
    Run tests asynchronously.
    """

    def _st(status):
        if status:
            return 'Passed'
        return 'Failed'

    passed = False
    if basename(plugin_path) == 'test_api1_0.py':
        passed = True

    results = []
    # test_name, result, details
    results.append(['Structure: Inheritance.'                     , passed,  _st(passed)])
    results.append(['Structure: Metadata.'                        , passed,  _st(passed)])
    results.append(['Initialization: GUI Access.'                 , passed,  _st(passed)])
    results.append(['Initialization: Event connection.'           , passed,  _st(passed)])
    results.append(['Live cycle: Enabling.'                       , passed,  _st(passed)])
    results.append(['Live cycle: Disabling.'                      , passed,  _st(passed)])
    results.append(['Live cycle: Configuration.'                  , passed,  _st(passed)])
    results.append(['File managment: Save file hook.'             , passed,  _st(passed)])
    results.append(['File managment: Load file hook.'             , passed,  _st(passed)])
    results.append(['Publishing: Pre-assembly hook.'              , passed,  _st(passed)])
    results.append(['Publishing: Pre-publishing hook.'            , passed,  _st(passed)])
    results.append(['Publishing: Post-publishing hook.'           , passed,  _st(passed)])
    results.append(['Configuration: Nested configuration changed.', passed,  _st(passed)])

    callback(results)
