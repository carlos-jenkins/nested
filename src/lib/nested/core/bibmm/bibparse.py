# -*- coding:utf-8 -*-
#
# Copyright (c) 2011, 2012 Carlos Jenkins <cjenkins@softwarelibrecr.org>
# Copyright (c) 2011 Juan Fiol <juanfiol@gmail.com>
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
Set of routines to parse BibTeX data and return each entry as a dictionary

USAGE:
    strings, db = parse_file(bibtexfile)
        *or*
    strings, db = parse_data(bibtexdata)
"""

import os
import re
import bibtexdef
import latex
latex.register()

def match_pair(expr, pair=(r'{', r'}'), start=0):
    """
    Find the outermost pair enclosing a given expresion

    pair is a 2-tuple containing (begin, end) where both may be characters or
    strings for instance:
        pair = ('[',']')    or
        pair = ('if','end if') or
        pair = ('<div>','</div>') or ...
    """

    opening = pair[0]
    closing = pair[1]

    # find first opening
    sstart = expr.find(opening, start)

    count = 0

    if opening == closing:
        eend = expr.find(closing, sstart+1)
        return sstart, eend

    p = re.compile('(' + opening + '|' + closing + ')', re.M)
    ps = re.compile(opening, re.M)

    iterator = p.finditer(expr, start)

    for match in iterator:
        if ps.match(match.group()):
            count+= 1
        else:
            count+= -1

        if count == 0:
            return sstart, match.end()

    return None

regex_braces = re.compile('[{}]')
def remove_braces(string):
    """
    Return the string parameter without braces
    """
    return regex_braces.sub('', string)

regex_pages = re.compile(r'\W+')
def parse_pages(pages):
    """
    Returns a 2-tuple (firstpage, lastpage) from a string.
    """
    pp = regex_pages.split(pages)
    firstpage = pp[0]
    if len(pp) == 2:
        lastpage = pp[1]
    else:
        lastpage = ''

    return firstpage, lastpage

def parse_name(name):
    """
    Process one name and separate it in '[von, Last, First, Jr]'
    """
    def getnames_form3(a):
        """
        Case with two commas: the name is of the format
        von Last, Jr, First
        like in: von Hicks, III, Michael
        """
        full_last = a[0].strip()
        full_first = a[1].strip()
        junior = a[2]
        von, last = get_vonlast(full_last)
        return [von.strip(), last.strip(), full_first.strip(), junior.strip()]

    def getnames_form2(a):
        """
        Case with one comma: the name is of the format
        von Last, First
        like in: von Hicks, Michael
        """
        full_last = a[0].strip()
        full_first = a[1].strip()
        junior = ''
        von,last = get_vonlast(full_last)
        return [von.strip(), last.strip(), full_first.strip(), junior]

    def getnames_form1(a):
        """
        Case with NO commas: the name is of the format
        First von Last
        like in: Michael von Hicks
        """
        last = a[0].split(' ')
        nfn = 0
        for l in last:
            if l != '' and not l[0].islower():
                nfn += 1
            else:
                break
        if nfn == len(last):
            nfn = -1

        full_first = ' '.join(last[:nfn])
        full_first = full_first.replace('.',' ')
        full_last =  ' '.join(last[nfn:])
        junior = ' '
        von,last= get_vonlast(full_last)
        return [von.strip(),last.strip(),full_first.strip(),junior.strip()]

    def get_vonlast(full_last):
        von = ''
        last = ''

        for l in full_last.split(' '):
            if len(l) > 0 and l[0].islower():
                von += l.lower() + ' '
            else:
                last += l + ' '
        return von, last

    # Start the processing
    a = name.split(',')
    if len(a) == 3:
        fullname = getnames_form3(a)
    elif len(a) == 2:
        fullname = getnames_form2(a)
    elif len(a) == 1:
        fullname = getnames_form1(a)
    else:
        fullname = []

    return fullname

def parse_author(data):
    """
    Returns a list of authors where each author is a list of the form:
    [von, Last, First, Jr]
    """
    return map(parse_name, remove_braces(data).split(' and '))

def get_fields(strng, strict=False):
    """
    Returns a list with pairs (field, value) from strng
    If strict is True, it will only allow known fields, defined in bibtexdef.bibtex_fields
    """

    comma_rex = re.compile(r'\s*[,]')
    ss = strng.strip()

    if not ss.endswith(','): # Add the last commma if missing
        ss += ','

    fields = []

    while True:
        name, sep, ss = ss.partition('=')
        name = name.strip().lower()   # This should be enough if there is no error in the entry
        if len(name.split()) > 1:    # Help recover from errors. name should be only one word anyway
            name = name.split()[-1]
        ss =ss.strip()
        if sep == '':
            break # We reached the end of the string

        if ss[0] == '{':    # The value is surrounded by '{}'
            s, e = match_pair(ss)
            data = ss[s+1:e-1].strip()
        elif ss[0] == '"':  # The value is surrounded by '"'
            s = ss.find(r'"')
            e = ss.find(r'"',s+1)
            data = ss[s+1:e].strip()
        else: # It should be a number or something involving a string
            e = ss.find(',')
            data = ss[0:e].strip()
            if not data.isdigit(): # Then should be some string
                dd = data.split('#')    # Test for joined strings
                if len(dd) > 1:
                    for n in range(len(dd)):
                        dd[n] = dd[n].strip()
                        dd[n] = dd[n].replace('{','"').replace('}','"')
                        if dd[n][0] != '"':
                            dd[n] = 'definitionofstring(%s) ' % (dd[n])
                    data = '#'.join(dd)
                else:
                    data = 'definitionofstring(%s) ' % data.strip()
        s = ss[e].find(',')
        ss = ss[s+e+1:]
        #if name == 'title':
        #    data = data.capitalize()
        #else:
        #    data = remove_braces(data)
        if not strict or name in bibtexdef.bibtex_fields:
            fields.append((name, data))
    return fields

def parse_file(path):
    """
    Parses a BibTeX file
    """
    if os.path.isfile(path):
        with open(path) as handler:
            data = handler.read()
            strings, db = parse_data(data)
            return strings, db
    return None,None

def find_line(key, lines):
    """
    Find the line of the given key
    """
    key_rex = re.compile(r'\s*@(\w*)\s*[{\(]\s*' + re.escape(key))
    for line_num in range(len(lines)):
        if key_rex.match(lines[line_num]):
            return line_num + 1
    return -1

def remove_comments(data):
    """
    Removes commented lines from BibTeX file. Comments starts with a %
    This is an extension not supported by vanilla BibTeX implementations
    """
    lines = data.split('\n')
    result = []
    for line in lines:
        if not line.strip().startswith('%'):
            result.append(line)
    return u'\n'.join(result)

def parse_data(data):
    """
    Parses a string with a BibTeX database
    """

    # Get lines
    lines = data.split('\n')

    # Remove comments
    data = remove_comments(data)

    # Regular expressions to use:
    #   A '@' followed by any word and an opening brace or parenthesis
    pub_rex = re.compile('\s?@(\w*)\s*[{\(]')
    # Reformat the string
    ss = re.sub('\s+', ' ', data).strip()

    # Find entries
    strings = {}
    preamble = []
    comment = []
    tmpentries = []
    entries = {}
    num = 1

    while True:
        entry = {}
        m = pub_rex.search(ss)

        if m == None:
            break

        if m.group(0)[-1] == '(':
            d = match_pair(ss, pair=('[(]','[)]'), start=m.end()-1)
        else:
            d = match_pair(ss, start=m.end()-1)

        if d != None:
            current = ss[m.start():d[1]-1]  # Currently analyzed entry
            st, entry = parse_entry(current)
            if st != None:
                strings.update(st)
            if entry != None and entry != {}:
                # Add system fields
                entry['_num'] = num
                num += 1
                entry['_line'] = find_line(entry['_code'], lines)
                entries[entry['_code']] = entry
            ss = ss[d[1]+1:].strip()

    return strings, entries

def parse_entry(source):
    """
    Reads an item in bibtex form from a string
    """
    try:
        source + ' '
    except:
        raise TypeError

    # Transform Latex symbols and strip newlines and multiple spaces
    if not isinstance(source, unicode):
        source = source.decode('latex+utf8', 'ignore')

    source.replace('\n',' ')
    source = re.sub('\s+', ' ', source)

    entry = {}
    st = None
    s = source.partition('{')

    if s[1] == '':
        return None, None

    entry_type = s[0].strip()[1:].lower()

    if entry_type == 'string':
        # Split string name and definition, removing outer "quotes" and put them in a list
        name, defin = s[2].strip().split('=')
        defin= defin.replace('"','').strip()
        if defin.startswith('{'):
            defin = defin[1:-1]
        return {name.strip():defin.strip()}, None

    elif entry_type in bibtexdef.bibtex_entries.keys():
        # Then it is a publication that we want to keep
        p = re.match('([^,]+),', s[2] ) # Look for the key followed by a comma
        entry['_type']= entry_type
        entry['_code']= p.group()[:-1]

        ff= get_fields(s[2][p.end():])
        for n,d in ff:
            if n == 'author' or n == 'editor':
                entry[n]= parse_author(d)
            elif n == 'title' or n == 'abstract':
                entry[n] = d.capitalize()
            elif n == 'pages':
                entry['firstpage'], entry['lastpage'] = parse_pages(d)
            elif n == 'year':
                entry[n] = d.strip('.')
            else:
                entry[n] = d
        return None, entry

    elif entry_type == 'comment' or entry_type == 'preamble':
        # Do nothing (for now)
        return None, None
    else:
        return None, None


