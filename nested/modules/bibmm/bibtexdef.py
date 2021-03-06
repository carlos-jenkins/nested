# -*- coding: utf-8 -*-
#       bibtexdef.py - BibTeX entries and fields definitions
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

"""@package bibtexdef
BibTeX entries and fields definitions.
"""

####################################
# Use application context
if __name__ == '__main__':
    import sys
    sys.path.append('../..')
from context import AppContext

WHERE_AM_I = AppContext.where_am_i(__file__)
_ = AppContext().what_do_i_speak()
####################################

# "Official" BibTeX fields
bibtex_fields = ['address', 'author', 'booktitle', 'chapter', 'edition',
                 'editor', 'howpublished', 'institution', 'journal', 'key',
                 'month', 'note', 'number', 'organization', 'pages',
                 'publisher', 'school', 'series', 'title', 'type', 'volume',
                 'year']
# Other common BibTeX fields
other_fields  = ['abstract', 'annote', 'crossref', 'doi', 'file', 'isbn',
                 'issn', 'keywords', 'url'] #'code', 'journal_abbrev','date-added','date-modified']

# Helper variable
all_fields = bibtex_fields + other_fields

# System fields
system_fields = ['_code', '_type', '_num', '_line']

bibtex_entries = {

'article' : {
    'name'    : _('Article'),
    'comment' : _('An article from a journal or magazine.'),
    'required': ['author', 'title', 'journal', 'year'],
    'optional': ['volume', 'number', 'pages', 'month', 'note', 'key'],
},

'book' : {
    'name'    : _('Book'),
    'comment' : _('A book with an explicit publisher.'),
    'required': ['author/editor', 'title', 'publisher', 'year'],
    'optional': ['volume/number', 'series', 'address', 'edition', 'month', 'note', 'key'],
},

'booklet' : {
    'name'    : _('Booklet'),
    'comment' : _('A work that is printed and bound, but without a named publisher or sponsoring institution.'),
    'required': ['title'],
    'optional': ['author', 'howpublished', 'address', 'month', 'year', 'note', 'key'],
},

'inbook' : {
    'name'    : _('Untitled book part'),
    'comment' : _('A part of a book, usually untitled. May be a chapter (or section or whatever) and/or a range of pages.'),
    'required': ['author/editor', 'title', 'chapter/pages', 'publisher', 'year'],
    'optional': ['volume/number', 'series', 'type', 'address', 'edition', 'month', 'note', 'key'],
},

'incollection' : {
    'name'    : _('Book part'),
    'comment' : _('A part of a book having its own title.'),
    'required': ['author', 'title', 'booktitle', 'publisher', 'year'],
    'optional': ['editor', 'volume/number', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note', 'key'],
},

'inproceedings' : {
    'name'    : _('Article in a conference proceedings'),
    'comment' : _('An article in a conference proceedings.'),
    'required': ['author', 'title', 'booktitle', 'year'],
    'optional': ['editor', 'volume/number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key'],
},

'manual' : {
    'name'    : _('Manual'),
    'comment' : _('Technical documentation.'),
    'required': ['title'],
    'optional': ['author', 'organization', 'address', 'edition', 'month', 'year', 'note', 'key'],
},

'mastersthesis' : {
    'name'    : _('Master\'s thesis.'),
    'comment' : _('A Master\'s thesis.'),
    'required': ['author', 'title', 'school', 'year'],
    'optional': ['type', 'address', 'month', 'note', 'key'],
},

'misc' : {
    'name'    : _('Miscellaneous'),
    'comment' : _('For use when nothing else fits.'),
    'required': [],
    'optional': ['author', 'title', 'howpublished', 'month', 'year', 'note', 'key'],
},

'phdthesis' : {
    'name'    : _('Ph.D. thesis'),
    'comment' : _('A Ph.D. thesis.'),
    'required': ['author', 'title', 'school', 'year'],
    'optional': ['type', 'address', 'month', 'note', 'key'],
},

'proceedings' : {
    'name'    : _('Conference proceedings'),
    'comment' : _('The proceedings of a conference..'),
    'required': ['title', 'year'],
    'optional': ['editor', 'volume/number', 'series', 'address', 'month', 'publisher', 'organization', 'note', 'key'],
},

'techreport' : {
    'name'    : _('Technical report'),
    'comment' : _('A report published by a school or other institution, usually numbered within a series.'),
    'required': ['author', 'title', 'institution', 'year'],
    'optional': ['type', 'number', 'address', 'month', 'note', 'key'],
},

'unpublished' : {
    'name'    : _('Unpublished'),
    'comment' : _('A document having an author and title, but not formally published.'),
    'required': ['author', 'title', 'note'],
    'optional': ['month', 'year', 'key'],
},

}

# bibtex_entries['conference'] = bibtex_entries['inproceedings']

def create_template(key, id=None, optional=True):
    """Create a template for the given entry type"""
    
    if not key in bibtex_entries.keys():
        return ''

    required_fields = []
    for field in bibtex_entries[key]['required']:
        required_fields.append('  ' + field + (' ' * max(0, 14 - len(field))) + '= "",')

    optional_fields = []
    if optional:
        for field in bibtex_entries[key]['optional']:
            optional_fields.append('%  ' + field + (' ' * max(0, 14 - len(field))) + '= "",')

    separation = ''
    if required_fields and optional_fields:
        separation = '\n'
    
    template = '@{entry_type}{{{uid},\n{required}{sep}{optional}\n}}\n'
    result = template.format(entry_type=key.upper(),
                             uid=key+'???',
                             required='\n'.join(required_fields),
                             sep=separation,
                             optional='\n'.join(optional_fields))
    
    return result

# Testing
if __name__ == '__main__':
    print(bibtex_entries.keys())
    fields = []
    for key in bibtex_entries.keys():
        fields = fields + bibtex_entries[key]['required'] + bibtex_entries[key]['optional']
    print(list(set(fields)))
    key = bibtex_entries.keys()[0]
    print(create_template(key))
    print('########################################')
    print(create_template(key, optional=False))
    print('########################################')

