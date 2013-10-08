# -*- coding: utf-8 -*-
#       export.py - Handles all the format transformations 
#       
#       Copyright (c) 2011 Carlos Jenkins <cjenkins@softwarelibrecr.org>
#       Copyright (c) 2009 Jendrik Seipp
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

"""@package export
Handles all the format transformations.

This module handles all format transformations, like exporting to other formats
or a preview.

Based on markup.py from RedNoteBook by Jendrik Seipp.
"""

import txt2tags
import logging
import re
import sys
import unicodedata

latex_commands = r"""\newcommand{\superscript}[1]{\ensuremath{^{\textrm{\small#1}}}}
\newcommand{\subscript}[1]{\ensuremath{_{\textrm{\small#1}}}}

"""

# Nested supported languages 'syntaxhighlighter' : 'listings'
supported_languages = { 'as3'        : '',
                        'bash'       : 'bash',
                        'cf'         : '',
                        'csharp'     : 'sharp,c',
                        'cpp'        : 'c++',
                        'css'        : '',
                        'delphi'     : 'delphi',
                        'diff'       : '',
                        'erlang'     : 'erlang',
                        'groovy'     : '',
                        'javascript' : '',
                        'java'       : 'java',
                        'javafx'     : 'java',
                        'perl'       : 'perl',
                        'php'        : 'php',
                        'plain'      : '',
                        'powershell' : 'command.com',
                        'python'     : 'python',
                        'ruby'       : 'ruby',
                        'scala'      : '',
                        'sql'        : 'sql',
                        'vb'         : 'visual,basic', # Almost
                        'xhtml'      : 'html'
                      }

def transliterate_string(string):
    """Transliterate given string"""
    nkfd_form = unicodedata.normalize('NFKD', unicode(string))
    normalized = u''.join([c for c in nkfd_form if not unicodedata.combining(c)])
    return normalized

def custom_preproc(lines, target):
    """All this functions sucks :S"""
    
    # Regexes
    code_open  = re.compile('{{{ (?P<code>'+ '|'.join(supported_languages.keys()) + ')')
    code_close = re.compile('}}}')
    math_open  = re.compile('<<<')
    math_close = re.compile('>>>')

    if target == 'xhtmls':

        # HTML replacement
        safe_for_html = [['&', '&amp;' ],
                         ['<', '&lt;'  ],
                         ['>', '&gt;'  ],
                         ['"', '&quot;']]

        code_preproc = []
        inside_code_block = False
        for line in lines:
            # Looking for the beginning of the block
            if not inside_code_block:
                found = code_open.match(line)
                if found:
                    inside_code_block = True
                    code = found.groupdict()['code']
                    code_preproc.append('\'\'\'')
                    code_preproc.append('<pre class="brush: {0}; class-name: code;">'.format(code))
                else:
                    # Normal line
                    code_preproc.append(line)
            # In a code block
            else:
                # Looking for the end of the block
                found = code_close.match(line)
                if found:
                    inside_code_block = False
                    code_preproc.append('</pre>')
                    code_preproc.append('\'\'\'')
                else:
                    # Code line, replace unsafe elements
                    for replacement in safe_for_html:
                        line = line.replace(replacement[0], replacement[1])
                    code_preproc.append(line)

        
        math_preproc = []
        inside_math_block = False
        for line in code_preproc:
            # Looking for the beginning of the block
            if not inside_math_block:
                found = math_open.match(line)
                if found:
                    inside_math_block = True
                    math_preproc.append('\'\'\'')
                    math_preproc.append('<p class="math">')
                else:
                    # Normal line
                    math_preproc.append(line)
            # In a math block
            else:
                # Looking for the end of the block
                found = math_close.match(line)
                if found:
                    inside_math_block = False
                    math_preproc.append('</p>')
                    math_preproc.append('\'\'\'')
                else:
                    # Math line, replace unsafe elements
                    for replacement in safe_for_html:
                        line = line.replace(replacement[0], replacement[1])
                    math_preproc.append(line)

            lines = math_preproc

    elif target == 'tex':

        code_preproc = []
        inside_code_block = False
        for line in lines:
            # Looking for the beginning of the block
            if not inside_code_block:
                found = code_open.match(line)
                if found:
                    inside_code_block = True
                    code = found.groupdict()['code']
                    code = supported_languages[code]
                    
                    code_preproc.append('\'\'\'')

                    code_splited = code.split(',')
                    if len(code_splited) == 1:
                        code_preproc.append('\\lstset{language=' + code + '}')
                    elif len(code_splited) == 2:
                        code_preproc.append('\\lstset{language=[' + code_splited[0] + ']' + code_splited[1] + '}')
                    
                    code_preproc.append('\\begin{lstlisting}')
                else:
                    # Normal line
                    code_preproc.append(line)
            # In a code block
            else:
                # Looking for the end of the block
                found = code_close.match(line)
                if found:
                    inside_code_block = False
                    code_preproc.append('\\end{lstlisting}')
                    code_preproc.append('\'\'\'')
                else:
                    # Code line
                    line = transliterate_string(line) # listings LaTeX package doesn't support non-ascii characters, sad :(
                    code_preproc.append(line)

        lines = code_preproc

    return lines


def _get_config(type):
    """Get the Txt2Tags configuration for specific target."""

    # Set the configuration on the 'config' dict.
    config = txt2tags.ConfigMaster()._get_defaults()
    config['sourcefile'] = txt2tags.MODULEIN
    config['currentsourcefile'] = txt2tags.MODULEIN
    config['infile'] = txt2tags.MODULEIN
    config['outfile'] = txt2tags.MODULEOUT # results as list

    # The Pre (and Post) processing config is a list of lists:
    # [ [this, that], [foo, bar], [patt, replace] ]
    config['postproc'] = []
    config['preproc'] = []

    if type == 'xhtml' or type == 'xhtmls' or type == 'html' or type == 'html5' :
        # Default values
        config['encoding'] = 'UTF-8'
        config['toc'] = 0
        config['style'] = ['themes/default.css']
        config['css-inside'] = 0
        config['css-sugar'] = 1
        
        # Remove target comments
        config['preproc'].append(['%xhtmls% ', ''])
        config['preproc'].append(['%html% ', '']) # Alias
        
        # Allow line breaks, r'\\\\' are 2 \ for regexes
        #config['preproc'].append([r'\\\\', '\'\'<br />\'\'']) # F*ck, these are used in Latex :S
        config['preproc'].append([r'@@', '\'\'<br />\'\'']) # F*ck, @@ is used in diffs :S

        # Math and code blocks are commented because txt2tags doesn't support
        # newlines in preproc, see:
        # http://code.google.com/p/txt2tags/issues/detail?id=25
        # For now, custom_preproc() is used
        ## Support math block
        #config['preproc'].append(['<<<', '\'\'\'\n<pre class="math">'])
        #config['preproc'].append(['>>>', '</pre>\n\'\'\''])

        ## Support code block
        #config['preproc'].append(['{{{ (' + '|'.join(supported_languages.keys()) + ')', '\'\'\'\n<pre class="brush: \\1; class-name: code;">'])
        #config['preproc'].append(['}}}', '</pre>\n\'\'\''])
        
        # Semantic tags, in case user use visual tags
        config['postproc'].append([r'(?i)(</?)b>', r'\1strong>'])
        config['postproc'].append([r'(?i)(</?)i>', r'\1em>'])
        config['postproc'].append([r'(?i)(</?)u>', r'\1ins>'])
        config['postproc'].append([r'(?i)(</?)s>', r'\1del>'])

        # Allow subscript superscript
        config['postproc'].append([r'\^\^(.*?)\^\^', r'<sup>\1</sup>'])
        config['postproc'].append([r',,(.*?),,', r'<sub>\1</sub>'])

        # Apply image resizing and correct path
        config['postproc'].append([r'<img (.*?) src="(\d+)-', r'<img \1 width="\2" src="'])
        config['postproc'].append([r'<img (.*?) src="', r'<img \1 src="media/images/'])

    elif type == 'tex':
        # Default values
        config['encoding'] = 'utf8'
        config['toc'] = 0

        # Support math block
        config['preproc'].append(['<<<', '\'\'\''])
        config['preproc'].append(['>>>', '\'\'\''])
        
        # Remove target comments
        config['preproc'].append(['%tex% ', ''])
        config['preproc'].append(['%latex% ', '']) # Alias
        config['preproc'].append(['%pdf% ', '']) # Alias

        # Allow line breaks, r'\\\\' are 2 \ for regexes
        #config['preproc'].append([r'\$\\backslash\$\$\\backslash\$', r'\'\'\\\\\'\''])  # F*ck, these are used in Latex :S
        config['preproc'].append([r'@@', r"''\\newline{}''"]) # F*ck, @@ is used in diffs :S

        ## Support code block
        #config['preproc'].append(['{{{ (' + '|'.join(supported_languages.keys()) + ')', '\'\'\'\n\\begin{verbatim}'])
        #config['preproc'].append(['}}}', '\\end{verbatim}\n\'\'\'\n'])

        # Allow subscript superscript
        config['postproc'].append([r'\\\^{}\\\^{}(.*?)\\\^{}\\\^{}', r'\\superscript{\1}'])
        config['postproc'].append([r',,(.*?),,', r'\\subscript{\1}'])

        # Apply image resizing
        config['postproc'].append([r'includegraphics\{(\d+)-', r'includegraphics[width=\1px]{'])
        config['postproc'].append([r'includegraphics(.*?)\{', r'noindent\includegraphics\1{media/images/'])

    elif type == 'txt':
        # Default values
        config['toc'] = 0
        
        # Remove target comments
        config['preproc'].append(['%txt% ', ''])
        config['preproc'].append(['%text% ', '']) # Alias
        
        # Allow line breaks, r'\\\\' are 2 \ for regexes
        #config['preproc'].append([r'\\\\', '\n']) # F*ck, these are used in Latex :S
        config['preproc'].append([r'@@', '\n']) # F*ck, @@ is used in diffs :S
        
        # Allow subscript superscript
        config['postproc'].append([r'\^\^(.*?)\^\^', r'\1'])
        config['postproc'].append([r',,(.*?),,', r'\1'])

    return config


def convert(txt, target, headers=None, options=None):
    """Perform the conversion of a given txt2tags ttext to a specific target."""
    
    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')

    # Perform custom preproc
    txt = custom_preproc(txt, target)

    # Base configuration
    config = _get_config(target)

    # Set the three header fields
    if headers is None:
        headers = ['', '', '']
    config['header1'] = headers[0]
    config['header2'] = headers[1]
    config['header3'] = headers[2]
    config['target'] = target

    if options is not None:
        if options.get('preproc'):
            options['preproc'].extend(config['preproc'])
        if options.get('postproc'):
            options['postproc'].extend(config['postproc'])
        config.update(options)

    # Check sanity of the configuration
    config = txt2tags.ConfigMaster().sanity(config)
        
    # Let's do the conversion
    try:
        # Convert
        target_body, marked_toc = txt2tags.convert(txt, config)
        # Footer
        #target_foot = txt2tags.doFooter(config)
        #target_foot.pop() # Unneded because we use txt2tags as a module
        target_foot = []
        # Table of content
        tagged_toc = txt2tags.toc_tagger(marked_toc, config)
        target_toc = txt2tags.toc_formatter(tagged_toc, config)
        target_body = txt2tags.toc_inside_body(target_body, target_toc, config)
        if not txt2tags.AUTOTOC and not config['toc-only']:
            target_toc = []
        # Full body
        config['fullBody'] = target_toc + target_body + target_foot
        # Headers
        outlist = txt2tags.doHeader(headers, config)
        # End document
        finished  = txt2tags.finish_him(outlist, config)
        result = '\n'.join(finished)

    # Txt2tags error, show the messsage to the user
    except txt2tags.error, msg:
        logging.error(msg)
        result = msg

    # Unknown error, show the traceback to the user
    except:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)

    return result
