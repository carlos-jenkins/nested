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
Nested configuration manager.
"""

    #####################################
    # Configuration functions
    #####################################

    def check_prefix(prefix, string):
        """
        Check that everyline in the given string begins with given prefix.
        """
        lines = string.splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line.startswith(prefix):
                result.append(line)
        return ('\n').join(result)

    def format_proc(self, is_preproc, procs, target=''):
        """Format a list of filters to a list of strings in the form (%!p***proc...)"""

        base = '%!{0}{1}: \'{2}\' \'{3}\''
        output = []

        # Type
        proc_type = 'postproc'
        if is_preproc:
            proc_type = 'preproc'
        # Target
        if target:
            target = '({0})'.format(target)

        for proc_filter in procs:
            output.append(base.format(proc_type, target, proc_filter[0], proc_filter[1]))

        return output


    def format_config(self, config):
        """Format a configuration dictionnary to a valid plain text txt2tags configuration section"""

        output = []

        # Target
        target = config.get('target', 'none')
        if target == 'none':
            logger.warning(_('What? Forcing the formatting to target \'xhtmls\' in format_config()'))
            target = 'xhtmls'
        output.append('%!target: ' + target)

        # Common filters
        if config.get('preproc'):  # Exists
            preprocs = config['preproc']
            if preprocs:            # Is not empty
                formatted_preprocs = self.format_proc(True, preprocs)
                if formatted_preprocs:
                    output = output + formatted_preprocs

        if config.get('postproc'):  # Exists
            postprocs = config['postproc']
            if postprocs:            # Is not empty
                formatted_postprocs = self.format_proc(False, postprocs)
                if formatted_postprocs:
                    output = output + formatted_postprocs

        # Format xhtmls
        xhtmls_config = config.get('xhtmls', {})
        if xhtmls_config:

            # Style
            if xhtmls_config.get('style'):
                styles = xhtmls_config['style']
                if styles:
                    output.append('%!style(xhtmls): ' + styles[0])

            # Options
            options = ''
            #  Numbered header
            if xhtmls_config.get('enum-title'):
                # Feature: ignoring if enum-title is false (--no-*)
                options = options + ' --enum-title'
            #  Table of content
            if xhtmls_config.get('toc'):
                # Feature: ignoring if toc is false (--no-*)
                options = options + ' --toc'
            #  Table of content level
            if xhtmls_config.get('toc-level'):
                options = options + ' --toc-level ' + str(xhtmls_config['toc-level'])
            #  Single document
            if xhtmls_config.get('css-inside'):
                # Feature: ignoring if css-inside is false (--no-*)
                options = options + ' --css-inside'
            #  Mask email
            if xhtmls_config.get('mask-email'):
                options = options + ' --mask-email'

            if options:
                output.append('%!options(xhtmls):' + options)

            # Filters
            if xhtmls_config.get('preproc'):  # Exists
                preprocs = xhtmls_config['preproc']
                if preprocs:            # Is not empty
                    formatted_preprocs = self.format_proc(True, preprocs, 'xhtmls')
                    if formatted_preprocs:
                        output = output + formatted_preprocs

            if xhtmls_config.get('postproc'):  # Exists
                postprocs = xhtmls_config['postproc']
                if postprocs:            # Is not empty
                    formatted_postprocs = self.format_proc(False, postprocs, 'xhtmls')
                    if formatted_postprocs:
                        output = output + formatted_postprocs

            # Custom options
            custom_options = ''
            #  Libs
            if xhtmls_config.get('nested-libs'): # Exists
                custom_options = custom_options + ' --libs ' + ','.join(xhtmls_config['nested-libs'])
            #  Base64 encoding of emails
            if xhtmls_config.get('nested-base64'): # Exists
                custom_options = custom_options + ' --base64'

            if custom_options:
                output.append('%!nested(xhtmls):' + custom_options)

        # Format tex
        tex_config = config.get('tex', {})
        if tex_config:

            # Options
            options = ''
            #  Numbered header
            if tex_config.get('enum-title'):
                # Feature: ignoring if enum-title is false (--no-*)
                options = options + ' --enum-title'
            #  Table of content
            if tex_config.get('toc'):
                # Feature: ignoring if toc is false (--no-*)
                options = options + ' --toc'
            #  Table of content level
            if tex_config.get('toc-level'):
                options = options + ' --toc-level ' + str(tex_config['toc-level'])

            if options:
                output.append('%!options(tex):' + options)

            # Filters
            if tex_config.get('preproc'):  # Exists
                preprocs = tex_config['preproc']
                if preprocs:            # Is not empty
                    formatted_preprocs = self.format_proc(True, preprocs, 'tex')
                    if formatted_preprocs:
                        output = output + formatted_preprocs

            if tex_config.get('postproc'):  # Exists
                postprocs = tex_config['postproc']
                if postprocs:            # Is not empty
                    formatted_postprocs = self.format_proc(False, postprocs, 'tex')
                    if formatted_postprocs:
                        output = output + formatted_postprocs

            # Custom options
            custom_options = ''
            #  Document class
            if tex_config.get('nested-docclass'): # Exists
                custom_options = custom_options + ' --docclass ' + tex_config['nested-docclass']
            #  PDF
            if tex_config.get('nested-pdf'): # Exists
                custom_options = custom_options + ' --pdf'

            if custom_options:
                output.append('%!nested(tex):' + custom_options)


        return '\n'.join(output)


    def proc_text_to_dict(self, text):
        """Convert procs in their text form (%!preproc...) to a dictionary in the form:
            {
                target1 : [[patt, repl], [patt, repl]],
                target2 : [[patt, repl], [patt, repl], [patt, repl]],
            }
        """

        # Regexes
        cfgregex  = txt2tags.ConfigLines._parse_cfg
        prepostregex = txt2tags.ConfigLines._parse_prepost

        procs = {}
        if text:
            for line in text.split('\n'):
                # Test if is config line
                match = cfgregex.match(line)
                if not match:
                    continue

                # Save information about this config
                name   = (match.group('name') or '').lower()
                target = (match.group('target') or 'all').lower()
                value  = match.group('value')

                # Test if is preproc or postproc
                valmatch = prepostregex.search(value)
                if not valmatch:
                    continue

                # Save information about this pre/post proc
                getval = valmatch.group
                patt   = getval(2) or getval(3) or getval(4) or ''
                repl   = getval(6) or getval(7) or getval(8) or ''
                value  = [patt, repl]

                # Add target if required
                if not procs.get(target):
                    procs[target] = [value]
                else:
                    procs[target].append(value)
        return procs


    def get_properties(self, get_all=True):
        """Read GUI options and return them as a dictionnary.
           Note: Dictionnary is in the form:
               {
                target   : 'xhtmls',
                preproc  : [[patt, repl], [patt, repl]],
                postproc : [[patt, repl], [patt, repl]],
                xhtmls   : {txt2tags compatible dictionnary + Nested extensions},
                tex      : {txt2tags compatible dictionnary + Nested extensions},
                txt      : {txt2tags compatible dictionnary + Nested extensions}
               }
        """

        config = {}

        # Target
        target = 'xhtmls'
        target_selection = self.targets_combobox.get_active_iter()
        if target_selection:
            target = self.targets_liststore.get_value(target_selection, 1)
        else:
            logger.warning(_('What? Target combo has nothing selected :S'))
        config['target'] = target


        # Filters
        pre = self.properties_preproc.get_buffer()
        post = self.properties_postproc.get_buffer()
        pre_filters_raw  =  pre.get_text(pre.get_start_iter() ,  pre.get_end_iter())
        post_filters_raw = post.get_text(post.get_start_iter(), post.get_end_iter())

        preproc_dict = self.proc_text_to_dict(pre_filters_raw)
        postproc_dict = self.proc_text_to_dict(post_filters_raw)

        if preproc_dict.get('all'):
            config['preproc'] = preproc_dict['all']
        if postproc_dict.get('all'):
            config['postproc'] = postproc_dict['all']

        # xhtmls
        if get_all or target == 'xhtmls':

            # Config for xhtmls
            xhtmls_config = {}
            xhtmls_config['target'] = 'xhtmls'

            # Filters
            if preproc_dict.get('xhtmls'):
                xhtmls_config['preproc'] = preproc_dict['xhtmls']
            if postproc_dict.get('xhtmls'):
                xhtmls_config['postproc'] = postproc_dict['xhtmls']

            # Style
            theme_selection = self.xhtmls_themes_combobox.get_active_iter()
            if theme_selection:
                theme = self.xhtmls_themes_liststore.get_value(theme_selection, 0)
                theme_path = os.path.join('media', 'themes', theme, 'style.css')
                xhtmls_config['style'] = [theme_path]
            else:
                logger.warning(_('What? Theme combo has nothing selected :S'))

            # Options
            #  Numbered header
            if self.xhtmls_enum_title.get_active():
                xhtmls_config['enum-title'] = 1
            #  Table of content
            if self.xhtmls_toc.get_active():
                xhtmls_config['toc'] = 1
                #  Table of content level
                xhtmls_config['toc-level'] = int(self.xhtmls_toc_level.get_value())
                #  Table of content title
                # FIXME, add a widget to get this
                # FIXME, this options it's not working on txt2tags :S
                xhtmls_config['toc-title'] = _('Table of contents')
            #  Single document
            if self.xhtmls_single.get_active():
                xhtmls_config['css-inside'] = 1
            #  Mask email
            if self.xhtmls_hide_simple.get_active():
                xhtmls_config['mask-email'] = 1

            # Custom options
            #  Libs
            libs = self.xhtmls_libs.get_text().replace(' ', '').split(',')
            libs = [i for i in libs if i]
            if libs:
                xhtmls_config['nested-libs'] = libs
            #  Base64 encoding of emails
            if self.xhtmls_hide_base64.get_active():
                xhtmls_config['nested-base64'] = True

            # Save config for xhtmls
            config['xhtmls'] = xhtmls_config


        # tex
        if get_all or target == 'tex':

            # Config for tex
            tex_config = {}
            tex_config['target'] = 'tex'

            # Filters
            if preproc_dict.get('tex'):
                tex_config['preproc'] = preproc_dict['tex']
            if postproc_dict.get('tex'):
                tex_config['postproc'] = postproc_dict['tex']

            # Options
            #  Numbered header
            if self.tex_enum_title.get_active():
                tex_config['enum-title'] = 1
            #  Table of content
            if self.tex_toc.get_active():
                tex_config['toc'] = 1
                #  Table of content level
                tex_config['toc-level'] = int(self.tex_toc_level.get_value())
                #  Table of content title
                # FIXME, add a widget to get this
                # FIXME, this options it's not working on txt2tags :S
                tex_config['toc-title'] = _('Table of contents')

            # Custom options
            #  Get document class
            docclass_selection = self.tex_docclass_combobox.get_active_iter()
            if docclass_selection:
                docclass, abstract = self.tex_docclass_liststore.get(docclass_selection, 1, 2)
                tex_config['nested-docclass'] = docclass
                tex_config['nested-abstract'] = abstract
            else:
                logger.warning(_('What? Document class combo has nothing selected :S'))
            #  Output as PDF
            if self.tex_pdf.get_active():
                tex_config['nested-pdf'] = True
            # Header
            header_buffer = self.tex_header.get_buffer()
            header_content = header_buffer.get_text(
                                header_buffer.get_start_iter(),
                                header_buffer.get_end_iter()
                             ).strip()
            if header_content:
                tex_config['nested-header'] = header_content

            # Save config for tex
            config['tex'] = tex_config

        # txt
        if get_all or target == 'txt':

            # Config for txt
            txt_config = {}
            txt_config['target'] = 'txt'

            # Save config for txt
            config['txt'] = txt_config


        return config


    def default_properties(self):
        """Restore properties dialog to its default"""
        # Headers
        self.properties_line1.set_text('')
        self.properties_line2.set_text('')
        self.properties_line3.set_text('')
        # Filters
        pre = self.properties_preproc.get_buffer().set_text('')
        post = self.properties_postproc.get_buffer().set_text('')
        # Target
        self.targets_combobox.set_active(0) #  Set xhtmls as the target by default
        self.targets_pages.set_current_page(0)
        # xhtmls options
        #  enum_title
        self.xhtmls_enum_title.set_active(False)
        #  toc
        self.xhtmls_toc.set_active(False)
        #  toc-level
        self.xhtmls_toc_level.set_value(5)
        #  single
        self.xhtmls_single.set_active(False)
        #  libs
        self.xhtmls_libs.set_text('')
        #  theme (theme is after libs so its callback can populate required libs)
        for theme_index in range(len(self.xhtmls_themes_liststore)):
            if self.xhtmls_themes_liststore[theme_index][0] == self.xhtmls_default_theme:
                self.xhtmls_themes_combobox.set_active(theme_index)
                break
        #  hide emails
        self.xhtmls_hide_no.set_active(True)
        # tex options
        #  docclass
        self.tex_docclass_combobox.set_active(0) # First document class
        #  pdf
        self.tex_pdf.set_active(False)
        #  enum_title
        self.tex_enum_title.set_active(False)
        #  toc
        self.tex_toc.set_active(False)
        #  toc-level
        self.tex_toc_level.set_value(5)
        #  libs
        self.tex_header.get_buffer().set_text('')


    def load_properties(self, config, raw_config):
        """Load configuration options into the GUI"""

        # Reset GUI
        self.default_properties()

        # Target
        supported_targets = {'xhtmls': 0, 'tex': 1, 'txt': 2}

        target = config.get('target', 'xhtmls')
        if not target in supported_targets:
            logger.warning(_('Sorry, {0} target is not supported. Using xhtmls.').format(target))
            target = 'xhtmls'
        index = supported_targets[target]
        self.targets_combobox.set_active(index)
        self.targets_pages.set_current_page(index)

        # Filters
        preproc_filters = []
        postproc_filters = []

        # Load xhtmls configuration
        if config.get('xhtmls'):
            xhtmls_config = config['xhtmls']

            # Style
            if xhtmls_config.get('style'):
                style = xhtmls_config['style'][0]
                theme = os.path.basename(os.path.dirname(style))
                avalaible_themes = self.xhtmls_themes_liststore
                for i in range(len(avalaible_themes)):
                    if avalaible_themes[i][0] == theme:
                        self.xhtmls_themes_combobox.set_active(i)
                        break

            # Options
            #  Numbered header
            if xhtmls_config.get('enum-title'):
                # Feature: ignoring if enum-title is false (--no-*)
                self.xhtmls_enum_title.set_active(True)
            #  Table of content
            if xhtmls_config.get('toc'):
                # Feature: ignoring if toc is false (--no-*)
                self.xhtmls_toc.set_active(True)
            #  Table of content level
            if xhtmls_config.get('toc-level'):
                self.xhtmls_toc_level.set_value(float(xhtmls_config['toc-level']))
            #  Single document
            if xhtmls_config.get('css-inside'):
                # Feature: ignoring if css-inside is false (--no-*)
                self.xhtmls_single.set_active(True)
            #  Mask email
            if xhtmls_config.get('mask-email'):
                # Feature: ignoring if mask-email is false (--no-*)
                self.xhtmls_hide_simple.set_active(True)

            # Filters
            preproc = xhtmls_config.get('preproc', [])
            postproc = xhtmls_config.get('postproc', [])

            for preproc_filter in preproc:
                preproc_filters.append('%!preproc(xhtmls): \'' + preproc_filter[0] + '\' \'' + preproc_filter[1] + '\'')

            for postproc_filter in postproc:
                postproc_filters.append('%!postproc(xhtmls): \'' + postproc_filter[0] + '\' \'' + postproc_filter[1] + '\'')

            # Custom options
            # Search for config string
            found = []
            custom_options = '%!nested(xhtmls):'
            for line in raw_config:
                if line.startswith(custom_options):
                    found = line.replace(custom_options, '', 1).strip().split(' ')
                    break
            if found:
                #  Libs
                try:
                    i = found.index('--libs')
                    libs = found[i + 1]
                    self.xhtmls_libs.set_text(libs)
                except:
                    pass
                #  Base64 encoding of emails
                #FIXME, uncomment me when this functionality is implemented
                #if '--base64' in found:
                #    self.xhtmls_hide_base64.set_active(True)


        # Load tex configuration
        if config.get('tex'):
            tex_config = config['tex']

            # Options
            #  Numbered header
            if tex_config.get('enum-title'):
                # Feature: ignoring if enum-title is false (--no-*)
                self.tex_enum_title.set_active(True)
            #  Table of content
            if tex_config.get('toc'):
                # Feature: ignoring if toc is false (--no-*)
                self.tex_toc.set_active(True)
            #  Table of content level
            if tex_config.get('toc-level'):
                self.tex_toc_level.set_value(float(tex_config['toc-level']))

            # Filters
            preproc = tex_config.get('preproc', [])
            postproc = tex_config.get('postproc', [])

            for preproc_filter in preproc:
                preproc_filters.append('%!preproc(tex): \'' + preproc_filter[0] + '\' \'' + preproc_filter[1] + '\'')

            for postproc_filter in postproc:
                postproc_filters.append('%!postproc(tex): \'' + postproc_filter[0] + '\' \'' + postproc_filter[1] + '\'')

            # Custom options
            # Search for config string
            found = []
            custom_options = '%!nested(tex):'
            for line in raw_config:
                if line.startswith(custom_options):
                    found = line.replace(custom_options, '', 1).strip().split(' ')
                    break
            if found:
                #  Document class
                try:
                    i = found.index('--docclass')
                    docclass = found[i + 1]
                    avalaible_docclasses = self.tex_docclass_liststore
                    for i in range(len(avalaible_docclasses)):
                        if avalaible_docclasses[i][1] == docclass:
                            self.tex_docclass_combobox.set_active(i)
                            break
                except:
                    pass
                #  PDF
                if '--pdf' in found and self.pdflatex:
                    self.tex_pdf.set_active(True)


        # Load txt configuration
        if config.get('txt'):
            txt_config = config['txt']
            # FIXMEFIXME implement something

        # Filters, again
        self.properties_preproc.get_buffer().set_text('\n'.join(preproc_filters))
        self.properties_postproc.get_buffer().set_text('\n'.join(postproc_filters))

        return
