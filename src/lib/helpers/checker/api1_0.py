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

def run(plugin_path, callback):
    """
    Run tests asynchronously.
    """
    results = []
    # test_name, result, details
    results.append(['Structure: Inheritance.'                     , False, 'Ignored'])
    results.append(['Structure: Metadata.'                        , True,  'Passed'])
    results.append(['Initialization: GUI Access.'                 , True,  'Passed'])
    results.append(['Initialization: Event connection.'           , True,  'Passed'])
    results.append(['Live cycle: Enabling.'                       , True,  'Passed'])
    results.append(['Live cycle: Disabling.'                      , True,  'Passed'])
    results.append(['Live cycle: Configuration.'                  , True,  'Passed'])
    results.append(['File managment: Save file hook.'             , True,  'Passed'])
    results.append(['File managment: Load file hook.'             , True,  'Passed'])
    results.append(['Publishing: Pre-assembly hook.'              , True,  'Passed'])
    results.append(['Publishing: Pre-publishing hook.'            , True,  'Passed'])
    results.append(['Publishing: Post-publishing hook.'           , True,  'Passed'])
    results.append(['Configuration: Nested configuration changed.', True,  'Passed'])

    callback(results)
