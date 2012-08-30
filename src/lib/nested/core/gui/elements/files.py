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
Utilities for Nested.
"""

    def load_sections(self, sections):
        """Load a sections list into the treestore"""

        # Clear previous document
        self.editor_treestore.clear()

        current_parent = None
        parents = [current_parent]
        current_depth = 1
        last = None

        for section in sections:

            level, title, content = section

            # Change parent
            if level > current_depth:   # Child
                parents.append(current_parent)
                current_parent = last
                current_depth = level
            else:                       # Uncle, grandfather, etc
                while level < current_depth:
                    current_parent = parents.pop()
                    current_depth = current_depth - 1

            # Append section
            # 0 - Title
            # 1 - Bloqued
            # 2 - Body
            joined = '\n'.join(content)
            if joined.startswith('\n'): #FIXME: this is to compensate a formatting feature of the save algorythm of this editor
                joined = joined.replace('\n', '', 1)
            last = self.editor_treestore.append(current_parent, (title, False, joined))


    def body_to_sections(self, body):
        """Convert a txt2tags body to a structured sections list"""

        # Regexes directly borrowed from txt2tags
        title_template = r'^(?P<id>%s)(?P<txt>%s)\1(\[(?P<label>[\w-]*)\])?\s*$'
        normal_title   = re.compile(title_template % ('[=]{1,5}', '[^=](|.*[^=])'))
        numbered_title = re.compile(title_template % ('[+]{1,5}', '[^+](|.*[^+])'))

        sections = []
        current_content = []
        current_title = _('Untitled section')
        level = 1

        for line in body:
            # Remove Nested special section comment
            was_commented = False
            if line.startswith('%S'):
                line = line.replace('%S', '').strip()
                was_commented = True

            # Look for titles
            is_title = False
            #  Check if is a normal title
            match = normal_title.match(line)
            if match:
                is_title = True
            #  If not, check if is a numbered title
            else:
                match = numbered_title.match(line)
                if match:
                    is_title = True

            if is_title:

                # Check if is not the first title
                if current_content or sections:
                    sections.append((level, current_title, current_content))

                line_disect = match.groupdict()
                level = len(line_disect['id'])
                current_title = line_disect['txt'].strip()
                if was_commented:
                    current_title = '%' + current_title
                current_content = []
            else:
                current_content.append(line)
        # Flush last section
        sections.append((level, current_title, current_content))

        return sections


    def compile_node(self, model, path, iter, result):
        """Compile a document section into a string"""
        # 0 - Title
        # 1 - Bloqued
        # 2 - Body
        level = model.iter_depth(iter) + 1
        body = model.get_value(iter, 2)
        title = model.get_value(iter, 0)
        if(not body.endswith('\n')):
            body = body + '\n'

        title_anchor = '[' + self.safe_string(title) + ']'
        formatted_level = '=' * level
        formatted_title = formatted_level + ' ' + title.replace('%', '') + ' ' + formatted_level + title_anchor + '\n'

        if title.startswith('%'):
            formatted_title = '%S ' + formatted_title

        result.append(formatted_title + '\n' + body + '\n')


    def compile_document(self):
        """Compile document into its components:
            header, as 3 elements list
            config, as a dictionnary
            body, as a list of formatted sections
        """

        # Get header area
        line1 = self.properties_line1.get_text()
        line2 = self.properties_line2.get_text()
        line3 = self.properties_line3.get_text()
        header = [line1, line2, line3]

        # Get config area
        config = self.get_properties()

        # Get body area
        document = []
        self.editor_treestore.foreach(self.compile_node, document)
        return (header, config, document)


    def file_backup(self):
        """Backup current document"""

        # Flush the content first
        self.sync_tree_fields(None)

        # Write the file
        file_path = os.path.join(self.current_file_path, '.backup.t2t.bak')
        header, config, body = self.compile_document()
        document = '\n'.join(header) + '\n\n' + self.format_config(config) + '\n\n' + ''.join(body)

        # Backup backup if backups are too different
        if os.path.exists(file_path):
                old_backup_size = os.path.getsize(file_path)
                if (old_backup_size - len(document)) > 1024: # 1KB FIXME make it user configurable
                    shutil.copyfile(file_path, file_path + '-' + self.timehash())

        try:
            file_handler = open(file_path, 'w')
            file_handler.write(document)
            # Visual notification
            self.program_statusbar.push(0, _('Document saved to backup file .backup.t2t.bak'))
        except:
            self.program_statusbar.push(0, _('Unable to save backup file. Are you in a read-only system?'))
        finally:
            file_handler.close()

        return True


    def file_save(self, widget):
        """Save the document to the selected file"""

        if self.current_file_name is None:
            self.file_save_as(widget)
        else:
            # Flush the content first
            self.sync_tree_fields(widget)
            # Compile the document
            file_path = os.path.join(self.current_file_path, self.current_file_name)
            header, config, body = self.compile_document()
            document = '\n'.join(header) + '\n\n' + self.format_config(config) + '\n\n' + ''.join(body)

            # Write the file
            try:
                file_handler = open(file_path, 'w')
                file_handler.write(document)
            except:
                self.program_statusbar.push(0, _('Unable to save the document. Are you in a read-only system?'))
                return
            finally:
                file_handler.close()

            # Write the Tex special header file
            tex_header_content = config['tex'].get('nested-header', '')
            if tex_header_content:
                try:
                    tex_header_path = os.path.join(self.current_file_path, 'header.tex')
                    tex_header_file_handler = open(tex_header_path, 'w')
                    tex_header_file_handler.write(tex_header_content + '\n')
                except:
                    logger.error(_('Unable to save the Tex header file. Read-only system?'))
                finally:
                    tex_header_file_handler.close()

            # Add file to recent files
            self.recent_files_add(file_path)
            # Reload recent files menu
            self.recent_files_reload()
            # Visual notification
            self.program_statusbar.push(0, _('Document saved in ') + file_path)
            self.window.set_title(self.current_file_name + ' - Nested')
            # Start watching modifications
            self.content_buffer.set_modified(False)
            self.saved = True


    def file_save_as(self, widget):
        """Show save as dialog and perform related checks"""
        response = self.dialog_save.run()
        filename = self.dialog_save.get_filename()
        if response == 0: # Save
            if filename is None:
                warning = gtk.MessageDialog(self.window,
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE, _('Please write a filename.'))
                warning.run()
                warning.destroy()
                self.file_save_as(widget)
                return
            else:
                if os.path.exists(filename):
                    confirm = gtk.MessageDialog(self.window,
                        gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                        gtk.BUTTONS_YES_NO, _('Do you want to overwrite the file?'))
                    sure = confirm.run()
                    confirm.destroy()
                    if sure != gtk.RESPONSE_YES:
                        self.file_save_as(widget)
                        return
                self.dialog_save.hide()
                new_current_file_name = os.path.basename(filename)
                if not new_current_file_name.endswith('.t2t'):
                    new_current_file_name = new_current_file_name + '.t2t'
                new_current_file_path = os.path.dirname(filename)

                # Migrate images
                images_path = os.path.join(self.current_file_path, 'images')
                if self.current_file_path != new_current_file_path and os.path.exists(images_path) and os.path.isdir(images_path): # Export is required

                    new_images_path = os.path.join(new_current_file_path, 'images')

                    # Backup folder with same name
                    if os.path.exists(new_images_path):
                        shutil.move(new_images_path, new_images_path + '-' + self.timehash())

                    # Copy payload
                    shutil.copytree(images_path, new_images_path)

                # Migrate title
                title_path = os.path.join(self.current_file_path, 'title.tex')
                if self.current_file_path != new_current_file_path and os.path.exists(title_path) and os.path.isfile(title_path): # Export is required

                    new_title_path = os.path.join(new_current_file_path, 'title.tex')

                    # Copy payload
                    shutil.copyfile(title_path, new_title_path)

                # Save file variables
                self.current_file_name = new_current_file_name
                self.current_file_path = new_current_file_path
                # Perfom the save
                self.file_save(widget)
                return
        else: # Cancel
            self.dialog_save.hide()


    def token_conf_to_dict(self, source_conf):
        """Convert a list of configuration tokens to a dictionary
           Note: see get_properties() for a description of the output dict.
        """

        output = {}

        source_parsed = txt2tags.ConfigMaster(source_conf).parse()
        target = source_parsed.get('target', 'xhtmls')

        output['target'] = target
        output[target] = source_parsed

        for supported_target in ['xhtmls', 'tex', 'txt']:
            if supported_target != target:
                target_conf = source_conf + [['all', 'target', supported_target]]
                output[supported_target] = txt2tags.ConfigMaster(target_conf).parse()

        return output

    def file_load(self, path_to_file):
        """Open, parse and load file onto the GUI"""

        path_to_file = os.path.abspath(path_to_file)
        logger.info(_('Loading file: {0}').format(path_to_file))

        # Read file
        content = ''
        try:
            file_handler = open(path_to_file, 'r')
            content = file_handler.read()
        except:
            logger.error(_('Unable to load file {0}.').format(path_to_file))
            return
        finally:
            file_handler.close()

        # Parse document
        lines = content.splitlines()
        source = txt2tags.SourceDocument(contents=lines)
        header, conf, body = source.split()

        # Load configuration
        token_conf  = source.get_raw_config()
        parsed_conf = self.token_conf_to_dict(token_conf)
        self.load_properties(parsed_conf, conf)
        #  Special Tex header
        tex_header = os.path.join(os.path.dirname(path_to_file), 'header.tex')
        if os.path.exists(tex_header):
            try:
                tex_header_file_handler = open(tex_header, 'r')
                tex_header_content = tex_header_file_handler.read().strip()
                self.tex_header.get_buffer().set_text(tex_header_content)
            except:
                logger.error(_('Unable to open LaTex header. Do you have permissions?'))
            finally:
                tex_header_file_handler.close()

        # Load headers
        if not header:
            header = ['', '', '']
        self.properties_line1.set_text(header[0])
        self.properties_line2.set_text(header[1])
        self.properties_line3.set_text(header[2])

        # Load body
        #  Compensate the Nested commented title feature that txt2tags does not understand :(
        commented_title_found = False
        lines_to_add = []
        for line in conf:
            if line.startswith('%S ='):
                commented_title_found = True
            if commented_title_found:
                lines_to_add.append(line)
        body = lines_to_add + body
        #  Load sections into the treestore
        sections = self.body_to_sections(body)
        self.load_sections(sections)

        # Set variables about file loaded
        self.current_file_name = os.path.basename(path_to_file)
        self.current_file_path = os.path.dirname(path_to_file)

        # Add file to recent files
        self.recent_files_add(path_to_file)
        self.recent_files_reload()

        # Tune up the GUI
        self.treeview.expand_all()
        self.current_section = None # In this way we avoid flushing the editor content back :)
        self.treeview.set_cursor(self.root_path)
        self.current_section = self.root_path
        self.content_entry.grab_focus()
        self.program_statusbar.push(0, _('File successfully loaded: ') + path_to_file)
        self.content_buffer.clear_stacks()
        self.images_liststore.clear()
        self.window.set_title(self.current_file_name + ' - Nested')

        # Start watching modifications
        self.content_buffer.set_modified(False)
        self.saved = True


    def file_open(self, widget):
        """Perform GUI tasks to load a file"""
        if not self.saved:
            response = self.dialog_not_saved.run()
            self.dialog_not_saved.hide()
            # Save
            if response == 2:
                self.file_save(widget)
                if not self.saved:
                    return
            # If Cancel
            if response <= 0:
                return

        response = self.dialog_load.run()
        self.dialog_load.hide()
        if response == 0: # Load
            filename = self.dialog_load.get_filename()
            if filename:
                self.file_load(filename)
            else:
                warning = gtk.MessageDialog(self.window,
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE, _('Please select a filename.'))
                warning.run()
                warning.destroy()
                self.file_open(widget)


    def file_new(self, widget):
        """Create and empty file and clean the interface"""
        if not self.saved:
            response = self.dialog_not_saved.run()
            self.dialog_not_saved.hide()
            # Save
            if response == 2:
                self.file_save(widget)
                if not self.saved:
                    return
            # If Cancel
            elif response <= 0:
                return

        self.current_file_path = tempfile.mkdtemp('', 'nested-')
        self.current_file_name = None
        self.saved = False

        # Reset GUI
        self.default_properties()
        self.window.set_title(_('Untitled document* - Nested'))
        self.title_entry.set_text(_('Untitled section'))
        self.content_buffer.set_text('')
        self.current_section = self.root_path
        self.editor_treestore.clear()
        self.editor_treestore.append(None, ['', False, ''])
        self.treeview.set_cursor(self.root_path)
        self.content_entry.grab_focus()
        self.program_statusbar.push(0, _('New file created...'))
        self.content_buffer.clear_stacks()
        self.images_liststore.clear()

        # Start watching modifications
        self.saved = True
        self.content_buffer.set_modified(False)
