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
Main publishing framework for Nested on top of txt2tags.
WARNING: This hacks module should eventually disappear in favor of a nested
flavored txt2tags fork.
"""

__all__ = ['publish', 'convert', 'latex_commands', 'supported_languages']

from nested import *

import re
import os
import sys
import logging
import gettext

import .txt2tags
from .footnotes import process_footnotes

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext


# Module static variables
latex_commands = r'''\newcommand{\superscript}[1]{\ensuremath{^{\textrm{\small#1}}}}
\newcommand{\subscript}[1]{\ensuremath{_{\textrm{\small#1}}}}

'''

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

def publish(header, full_config, body):
    """
    Export document to the selected target.
    """

    # Get configuration
    target = full_config['target']
    config = full_config[target]

    # Merge procs
    common_preprocs  = full_config.get('preproc', [])
    common_postprocs = full_config.get('postproc', [])
    target_preprocs  = config.get('preproc', [])
    target_postprocs = config.get('postproc', [])
    preprocs  = common_preprocs  + target_preprocs
    postprocs = common_postprocs + target_postprocs
    if preprocs:
        config['preproc'] = preprocs
    if postprocs:
        config['postproc'] = postprocs

    # Close all blocks before publishing
    for i in range(len(body)):
        body[i] = body[i] + '\n'

    # Custom structure document
    if target == 'xhtmls':
        restructured_content = []
        restructured_section = '\'\'\'\n\n<div id="section{0}" class="section">\n\'\'\'\n{1}\n\n\'\'\'\n</div>\n\'\'\'\n'
        section_count = 1
        for section in body:
            # Footnotes
            if section.find('°°_') >= 0:
                section = process_footnotes(section, 'xhtmls')
            restructured_content.append(restructured_section.format(section_count, section))
            section_count += 1
        body = restructured_content

    #  Automatic abstract and footnotes
    elif target == 'tex':
        # Abstract support
        abstract_support = config.get('nested-abstract', False)
        if abstract_support:
            # Comment title
            if not body[0].startswith('%S '):
                body[0] = '%S ' + body[0]
                body.insert(1, r"''' \end{abstract}" + '\n')
                body.insert(0, r"''' \begin{abstract}" + '\n')

        # Footnotes support
        processed_sections = []
        for section in body:
            if section.find('°°_') >= 0:
                section = process_footnotes(section, 'tex')
            processed_sections.append(section)
        body = processed_sections

    # Magic :D :D
    content = convert(''.join(body), target, header, config)

    if content:

        # Create export directories if needed
        export_dir = os.path.join(self.current_file_path, 'publish')
        export_dir_target = os.path.join(export_dir, target)
        if not os.path.exists(export_dir_target):
            os.makedirs(export_dir_target, 0755)

        # Export images
        if target == 'xhtmls' or target == 'tex':
            # Check if image export is required
            images_path = os.path.join(self.current_file_path, 'images')
            if os.path.exists(images_path) and os.path.isdir(images_path): # Export is required

                export_dir_target_images = os.path.join(export_dir_target, 'media', 'images')

                # Remove previous images
                if os.path.exists(export_dir_target_images):
                    shutil.rmtree(export_dir_target_images)

                # Copy payload
                shutil.copytree(images_path, export_dir_target_images)

        # Include libraries
        if target == 'xhtmls':
            libs = config.get('nested-libs', [])
            libs_includes = []
            for lib in libs:
                # Check if is a user o system library
                lib_path = os.path.join(self.user_dir, 'libraries', lib)
                if not os.path.exists(lib_path):
                    lib_path = os.path.join(self.where_am_i, 'libraries', lib)
                # If library exists
                if os.path.exists(lib_path):
                    # Check if library has a payload directory
                    lib_payload_path = os.path.join(lib_path, 'media', 'libraries', lib)
                    if os.path.exists(lib_payload_path):

                        export_dir_target_library = os.path.join(export_dir_target, 'media', 'libraries')
                        dst = os.path.join(export_dir_target_library, lib)

                        # Create target media and library directory if necessary
                        if not os.path.exists(export_dir_target_library):
                            os.makedirs(export_dir_target_library, 0755)
                        # Remove previous payload
                        elif os.path.exists(dst):
                            shutil.rmtree(dst)

                        # Copy payload
                        shutil.copytree(lib_payload_path, dst)

                    # Check if library has an include file
                    include_path = os.path.join(lib_path, 'include.html')
                    if os.path.exists(include_path):
                        try:
                            include_handler = open(include_path, 'r')
                            include_content = include_handler.read().strip()
                            if include_content:
                                libs_includes.append(include_content)
                        except:
                            logger.warning(_('Unable to include library {0}.'.format(include_path)))
                        finally:
                            include_handler.close()
                else:
                    logger.warning(_('Ignoring library {0}').format(lib))

            # Load includes
            content = content.replace('</head>', '\n'.join(libs_includes) + '\n</head>', 1)

        # Include theme
        if target == 'xhtmls':
            selection = self.xhtmls_themes_combobox.get_active()
            theme = self.xhtmls_themes_liststore[selection][0]
            # Check if is a user o system theme
            theme_path = os.path.join(self.user_dir, 'themes', theme)
            if not os.path.exists(theme_path):
                theme_path = os.path.join(self.where_am_i, 'themes', theme)
            # If theme exists
            if os.path.exists(theme_path):
                # We need to include, or to copy theme files?
                theme_css = os.path.join(theme_path, 'style.css')
                theme_js  = os.path.join(theme_path, 'scripts.js')
                if_theme_css = os.path.exists(theme_css)
                if_theme_js  = os.path.exists(theme_js)
                if config.get('css-inside', False):
                    # Include Style
                    if if_theme_css:
                        theme_css_content = ''
                        try:
                            theme_css_handler = open(theme_css, 'r')
                            theme_css_content = theme_css_handler.read().strip()
                        except:
                            logger.error(_('Unable to open style {0}.'.format(theme_css)))
                        finally:
                            theme_css_handler.close()
                        if theme_css_content:
                            theme_css_content = '<style type="text/css">\n' + theme_css_content + '\n</style>\n</head>'
                            content = content.replace('</head>', theme_css_content, 1)
                    # Include Scripts
                    if if_theme_js:
                        theme_js_content = ''
                        try:
                            theme_js_handler = open(theme_js, 'r')
                            theme_js_content = theme_js_handler.read().strip()
                        except:
                            logger.error(_('Unable to open script {0}.'.format(theme_js)))
                        finally:
                            theme_js_handler.close()
                        if theme_js_content:
                            theme_js_content = '<script type="text/javascript">\n//<![CDATA[\n' + theme_js_content + '\n//]]>\n</script>\n</head>'
                            content = content.replace('</head>', theme_js_content, 1)
                else:
                    if if_theme_css or if_theme_js:
                        # Remove old theme on the target if it exists
                        old_theme = os.path.join(export_dir_target, 'media', 'themes', theme)
                        if os.path.exists(old_theme):
                            shutil.rmtree(old_theme)
                        # Copy theme
                        shutil.copytree(theme_path, old_theme)
                        # Reference files
                        if if_theme_css:
                            relative_css = os.path.join('media', 'themes', theme, 'style.css')
                            theme_css_link = '<link rel="stylesheet" type="text/css" href="{0}" />\n</head>'.format(relative_css)
                            content = content.replace('</head>', theme_css_link, 1)
                        if if_theme_js:
                            relative_js = os.path.join('media', 'themes', theme, 'scripts.js')
                            theme_js_link = '<script type="text/javascript" src="{0}"></script>\n</head>'.format(relative_js)
                            content = content.replace('</head>', theme_js_link, 1)
                # Insert header and footer is theme has one
                theme_header = os.path.join(theme_path, 'header.html')
                theme_footer = os.path.join(theme_path, 'footer.html')
                if os.path.exists(theme_header):
                    header_content = ''
                    try:
                        header_handler = open(theme_header, 'r')
                        header_content = header_handler.read().strip()
                    except:
                        logger.error(_('Unable to open header {0}.'.format(theme_header)))
                    finally:
                        header_handler.close()
                    if header_content:
                        content = content.replace('<body>', '<body>\n' + header_content, 1)
                if os.path.exists(theme_footer):
                    footer_content = ''
                    try:
                        footer_handler = open(theme_footer, 'r')
                        footer_content = footer_handler.read().strip()
                    except:
                        logger.error(_('Unable to open footer {0}.'.format(theme_footer)))
                    finally:
                        footer_handler.close()
                    if footer_content:
                        content = content.replace('</body>', footer_content + '\n</body>\n', 1)

            else:
                logger.error(_('Theme {0} could not be found').format(theme))

        # Finish the document
        if target == 'xhtmls':
            generator_tag = '<meta name="generator" content="http://txt2tags.org" />'
            content = content.replace(
                generator_tag,
                generator_tag.replace('http://txt2tags.org', 'Nested http://nestededitor.sourceforge.net/', 1), 1)
        elif target == 'tex':
            # Document class
            documentclass = config.get('nested-docclass', '{article}')
            if documentclass != '{article}':
                # Change document class ({IEEEtran}, {report}, {book})'
                content = content.replace(r'\documentclass{article}', r'\documentclass' + documentclass, 1)
                content = content.replace('\\clearpage\n', '', 1)
            # LaTeX header
            if config.get('nested-header'):
                tex_header = config['nested-header']
                content = content.replace(r'\begin{document}', '% header\n' + tex_header + '\n\n\\begin{document}', 1)
            # Custom title
            tex_title_path = os.path.join(self.current_file_path, 'title.tex')
            if os.path.isfile(tex_title_path):
                with open(tex_title_path) as tex_title_handler:
                    tex_title = tex_title_handler.read().strip()
                    if tex_title:
                        title_regex = re.compile('% Title.*?% Title end', re.DOTALL)
                        # I know this is stupid, but I didn't want to deal with re.escape - codec - slash thing
                        content = title_regex.sub('%%%TITLETEMPORALPLACEHOLDER%%%', content, count=1)
                        content = content.replace('%%%TITLETEMPORALPLACEHOLDER%%%', '% Title\n' + tex_title + '\n% Title end', 1)

            # Add support for superscript and subscript
            content = latex_commands + content

        # Save file
        export_file = self.current_file_name
        if export_file is None:
            export_file = target
        if export_file.endswith('.t2t'):
            export_file = export_file[:-4]
        if not export_file:
            export_file = '_'

        file_base = os.path.join(export_dir_target, export_file)

        extension = 'html' if target == 'xhtmls' else target
        export_file = file_base + '.' + extension

        try:
            file_handler = open(export_file, 'w')
            file_handler.write(content)
        except:
            self.program_statusbar.push(0, _('Unable to publish the document. Are you in a read-only system?'))
            return
        finally:
            file_handler.close()

        # Check if PDF is requested
        if target == 'tex':
            pdf_requested = config.get('nested-pdf', False)
            if pdf_requested:
                if self.pdflatex:
                    os.chdir(export_dir_target)
                    if sys.platform.startswith('linux') and os.path.isfile('/usr/bin/rubber'):
                        ret_code = subprocess.call(['/usr/bin/rubber', '--pdf', export_file])
                    else:
                        ret_code = subprocess.call([self.pdflatex, '-halt-on-error', '-interaction=batchmode', export_file])
                    os.chdir(self.where_am_i)
                    if ret_code == 0: # Succeed
                        export_file = file_base + '.pdf'
                    else:             # Failed
                        export_file = file_base + '.log'
                else:
                    logger.error(_('pdflatex command is not avalaible.'))

        # Open log viewer dialog
        if export_file.endswith('.log') or (target == 'tex' and self.config.getboolean('latex', 'always-show-log-viewer')):
            # Create GUI if required
            if self.log_viewer is None:
                self.log_viewer = LaTeXLogViewer(self.window)
            # export_file can be .pdf, .tex, etc. Make sure to open the log.
            log_file = os.path.splitext(export_file)[0] + '.log'
            self.log_viewer.load_log(log_file)

        # Launch default application for that file
        if self.config.getboolean('general', 'open-after-publish') and not export_file.endswith('.log'):
            self.default_open(export_file)

        # Show to the status bar
        self.program_statusbar.push(0, target + _(' file published to: ') + export_file)

def _custom_preproc(lines, target):
    """
    Implement some of the Nested features as custom preprocessors.
    All this functions sucks :S
    """

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
        # For now, _custom_preproc() is used
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
    """Perform the conversion of a given txt2tags text to a specific target."""

    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')

    # Perform custom preproc
    txt = _custom_preproc(txt, target)

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
