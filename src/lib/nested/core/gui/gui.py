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
Nested GUI main file. This file holds the Nested class and starting point.
"""

import sys              # For command line arguments
import os               # For paths
import shutil           # For copying files
import gobject          # For handling GUI threads
import gtk              # For the GUI
import pango            # For Font Descriptions
import tempfile         # For temporal files
import ConfigParser     # To parse configurations
import custom_buffer    # Syntax highlight and Undo/Redo
import txt2tags         # For loading files
import export           # For exporting content to PDF, HTML, etc.
import re               # For matching title when loading files
import Image            # For thumbnails
import StringIO         # For PIL Image to GdkPixbuf conversion
import threading        # For background processing
from modules.latex.log.viewer import LaTeXLogViewer # To view LaTeX logs

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

os.chdir(WHERE_AM_I)

bounded_markup = {
                'bold'        : ['**', '**'],
                'italic'      : ['//', '//'],
                'underline'   : ['__', '__'],
                'stroke'      : ['--', '--'],
                'ulist'       : ['\n- ', '\n\n'],
                'olist'       : ['\n+ ', '\n\n'],
                'verbatim'    : ['\n```\n\t', '\n```\n'],
                'link'        : ['[', ']'],
                'image'       : ['[', ']'],
                'underscript' : [',,', ',,'],
                'superscript' : ['^^', '^^']
            }

supported_images = ['.png', '.jpg', '.gif']

class Nested(object):
    """This class holds all the GUI construction, handling and callbacks.

    Some functions of this class includes:
        - Construction of the GUI.
        - Tunning and initialization.
        - Callbacks of the buttons and menus.
    """

    def __init__(self):
        """The Nested constructor."""

        # Application variables
        self.where_am_i = WHERE_AM_I
        logger.info(_('We are in {0}').format(self.where_am_i))
        self.lang = os.environ['LANG'].split('.')[0]

        self.config = ConfigParser.SafeConfigParser()
        self.root_path = (0, )
        self.current_section = self.root_path
        self.focus_mode = False

        self.current_file_path = tempfile.mkdtemp('', 'nested-')
        self.current_file_name = None
        self.saved = True
        self.ignore_modifications = False

        # Read the config files
        self.user_config = os.path.expanduser('~/.nested/config.ini')
        if sys.platform.startswith('win') and os.environ['APPDATA']:
            self.user_config = os.path.join(os.environ['APPDATA'], 'Nested', 'config.ini')
        self.user_dir = os.path.dirname(self.user_config)
        default_config = 'config.ini'
        if not os.path.exists(self.user_config):
            if not os.path.exists(self.user_dir):
                os.makedirs(self.user_dir)
            shutil.copyfile(default_config, self.user_config)
        using_files = self.config.read([default_config, self.user_config])
        logger.info(_('Using configuration files: ') + ', '.join(using_files))

        # Create user directories
        self.user_themes       = os.path.join(self.user_dir, 'themes')
        self.user_libraries    = os.path.join(self.user_dir, 'libraries')
        self.user_templates    = os.path.join(self.user_dir, 'templates')
        self.user_examples     = os.path.join(self.user_dir, 'examples')
        self.user_dictionaries = os.path.join(self.user_dir, 'dictionaries')
        for directory in [self.user_themes, self.user_libraries, self.user_templates, self.user_examples, self.user_dictionaries]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        self.recent_files = os.path.join(self.user_dir, 'recent.txt')
        if not os.path.exists(self.recent_files):
            try:
                recents = open(self.recent_files, 'w')
                recents.write('')
            except:
                logger.error(_('Unable to create recent.txt file. Read-only system?'))
            finally:
                recents.close()

        # Clipboards
        self.text_clipboard = gtk.Clipboard() # Default display, CLIPBOARD

        # Get the GUI
        self.builder, go = get_builder(WHERE_AM_I, 'gui.glade')
        self.window                        = go('main_window')
        self.about                         = go('dialog_about')
        #  GUI Elements
        self.program_menu                  = go('program_menu')
        self.program_toolbar               = go('program_toolbar')
        self.program_title                 = go('program_title')
        self.sections_column               = go('sections_column')
        self.program_statusbar             = go('program_statusbar')
        self.log_viewer = None
        #  Main window TreeView specific
        self.treeview                      = go('treeview1')
        self.editor_treestore              = go('editor_treestore')
        #  Main window text input widgets
        self.title_entry                   = go('title_entry')
        self.format_toolbar                = go('format_toolbar')
        self.markup_or_preview             = go('markup_or_preview')
        self.content_entry                 = go('content_entry')
        self.content_buffer = custom_buffer.CustomBuffer(syntax='txt2tags')
        self.content_entry.set_buffer(self.content_buffer)

        #  Search widget
        self.search_overlay    = go('search_overlay')
        self.search_overlay_entry = go('search_overlay_entry')
        self.content_entry.add_child_in_window(self.search_overlay, gtk.TEXT_WINDOW_WIDGET, 0, 0)

        #  Spell checking support
        self.spell_checking = None
        try:
            import locale
            from modules.textviews.spellcheck import SpellChecker

            # Install all .oxt extensions, if any
            try:
                from modules.oxt_import import deflate_oxt
                deflate_oxt(self.user_dictionaries,
                            self.user_dictionaries,
                            move_path=os.path.join(self.user_dictionaries, 'ext'))
            except:
                logger.error(_('Unable to install .oxt dictionaries'))

            # Add another dictionaries lookup path
            SpellChecker.set_dictionary_path(self.user_dictionaries)

            # Define language for spell checking
            lang_config = self.config.get('spell-checking', 'lang').strip()
            lang_user = locale.getdefaultlocale()[0]
            spell_lang = 'en'
            if (lang_config.lower().strip() != 'auto') and (SpellChecker.language_exists(lang_config)):
                spell_lang = lang_config
            elif SpellChecker.language_exists(lang_user):
                spell_lang = lang_user

            # Create spell checking object
            self.spell_checking = SpellChecker(
                    self.content_entry,
                    language=spell_lang
                )

            # This doesn't work: spellcheck library uses pango word breaking
            # algorythms, and thus a link is never evaluated as a whole, so
            # the regex will never math :S FIXME
            #regex_bank = txt2tags.getRegexes()
            #self.spell_checking.append_ignore_regex(regex_bank['link'].pattern)

            # GUI configuration
            go('toolbutton_spell_separator').show()
            spell_button = go('toolbutton_spell')
            spell_button.show()
            if not self.config.getboolean('spell-checking', 'enabled-by-default'):
                spell_button.set_active(False)
                self.toggle_spell_checking(spell_button)
        except Exception as excep:
            raise excep
            logger.error(_('Unable to import spellcheck: spell checking will be unavailable.'))

        if not self.config.getboolean('editor', 'word-wrap'):
            self.content_entry.set_wrap_mode(gtk.WRAP_NONE)
        self.content_buffer.connect('modified-changed', self.modified)

        #  Dynamic menues
        self.menu_templates                = go('menu_templates')
        self.menu_templates.set_submenu(gtk.Menu())
        self.menu_examples                 = go('menu_examples')
        self.menu_examples.set_submenu(gtk.Menu())
        self.menu_recent                   = go('menu_recent')
        self.menu_recent.set_submenu(gtk.Menu())

        #  Editor dialog specific
        self.dialog_editor     = go('dialog_editor')
        self.editor_font_button            = go('editor_font_button')
        self.editor_theme_type_custom      = go('editor_theme_type_custom')
        self.editor_theme_type_theme       = go('editor_theme_type_theme')
        self.editor_fontcolor_button       = go('editor_fontcolor_button')
        self.editor_backgroundcolor_button = go('editor_backgroundcolor_button')
        self.editor_treeview   = go('editor_treeview')

        #  Link dialog specific
        self.dialog_link                   = go('dialog_link')
        self.link_ext_type                 = go('radiobutton2')
        self.link_ext_url                  = go('entry2')
        self.link_ext_label                = go('entry3')
        self.link_int                      = go('treeview2')

        #  Tables dialog specific
        self.dialog_tables                 = go('dialog_tables')
        self.table_rows_spinbutton         = go('table_rows_spinbutton')
        self.table_columns_spinbutton      = go('table_columns_spinbutton')

        #  Code dialog specific
        self.dialog_code                   = go('dialog_code')
        self.dialog_code_type              = go('dialog_code_type')
        self.dialog_code_content           = go('dialog_code_content')
        self.dialog_code_entry             = go('dialog_code_entry')

        #  File filter specific
        self.filter_nested                 = go('filter_nested')
        self.filter_nested.set_name('Nested (*.t2t)')
        self.filter_nested.add_mime_type('text/x-txt2tags')
        self.filter_nested.add_pattern('*.t2t')

        #  Save dialog specific
        self.dialog_not_saved              = go('dialog_not_saved')
        self.dialog_save                   = go('dialog_save')
        self.dialog_save.add_filter(self.filter_nested)

        #  Load dialog specific
        self.dialog_load = go('dialog_load')
        self.dialog_load.add_filter(self.filter_nested)

        #  Document properties dialog specific
        self.dialog_properties             = go('dialog_properties')
        self.properties_line1              = go('properties_line1')
        self.properties_line2              = go('properties_line2')
        self.properties_line3              = go('properties_line3')
        self.properties_preproc            = go('properties_preproc')
        self.properties_postproc           = go('properties_postproc')
        self.properties_preproc.modify_font(pango.FontDescription('DejaVu Sans Mono 10'))
        self.properties_postproc.modify_font(pango.FontDescription('DejaVu Sans Mono 10'))
        #   Target
        self.targets_combobox              = go('targets_combobox')
        self.targets_liststore             = go('targets_liststore')
        self.targets_pages                 = go('targets_pages')
        #   xhtmls options
        #    theme
        self.xhtmls_themes_liststore       = go('themes_liststore')
        self.xhtmls_themes_combobox        = go('themes_combobox')
        #    enum_title
        self.xhtmls_enum_title             = go('xhtmls_enum_title')
        #    toc
        self.xhtmls_toc                    = go('xhtmls_toc')
        #    toc-level
        self.xhtmls_toc_level              = go('xhtmls_toc_level')
        self.xhtmls_toc_level.set_value(5)
        #    single
        self.xhtmls_single                 = go('xhtmls_single')
        #    libs
        self.xhtmls_libs                   = go('xhtmls_libs')
        #    hide emails
        self.xhtmls_hide_no                = go('xhtmls_hide_no')
        self.xhtmls_hide_simple            = go('xhtmls_hide_simple')
        self.xhtmls_hide_base64            = go('xhtmls_hide_base64')
        #   tex options
        #    class
        self.tex_docclass_combobox         = go('docclass_combobox')
        self.tex_docclass_liststore        = go('docclass_liststore')
        #    options
        self.tex_pdf                       = go('tex_pdf')
        self.tex_enum_title                = go('tex_enum_title')
        self.tex_toc                       = go('tex_toc')
        self.tex_toc_level                 = go('tex_toc_level')
        self.tex_toc_level.set_value(5)
        #    header
        self.tex_header                    = go('tex_header')

        # Enable PDF output support
        self.pdflatex = ''
        hint = ''
        test_path = ''
        # Use user path
        user_path = self.config.get('latex', 'pdflatex-path')
        if user_path is not None and user_path.lower().strip() not in ['none', 'find', 'default', 'search', '']:
            test_path = user_path
            logger.info(_('Using user path for pdflatex: {0}').format(test_path))
        # Go find pdflatex
        #  GNU/Linux
        elif sys.platform.startswith('linux'):
            hint = _('packages <tt>texlive</tt>, <tt>texlive-publishers</tt>\nand <tt>texlive-latex-extra</tt>.')
            test_path = '/usr/bin/pdflatex'
        #  MacOSX
        elif sys.platform.startswith('darwin'):
            hint = _('MacTeX from http://www.tug.org/mactex/.')
            test_path = '' # FIXME I have no idea :S
        #  MS Windows
        elif sys.platform.startswith('win'):
            hint = _('MikTeX from http://miktex.org/.')
            win_program_files = os.environ['ProgramFiles']
            win_installed_programs = os.listdir(win_program_files)
            win_miktex = ''
            for program in win_installed_programs:
                if program.lower().startswith('miktex'):
                    win_miktex = program
                    break
            test_path = os.path.join(win_program_files, win_miktex, 'miktex', 'bin', 'pdflatex.exe')

        if os.path.exists(test_path):
            self.pdflatex = test_path
            self.tex_pdf.set_sensitive(True)
        else:
            nopdflatex_tooltip = _("""\
<tt>pdflatex</tt> command wasn 't found. Please install
{0}""").format(hint)
            self.tex_pdf.set_tooltip_markup(nopdflatex_tooltip)

        #  HTML preview
        self.preview_wrapper = go('scrolledwindow1')
        try:
            import webkit
            self.preview = webkit.WebView()
            self.preview.connect('navigation-requested', self._navigation_requested_cb)
            self.preview_wrapper.add_with_viewport(self.preview)
            self.preview.show()
        except:
            windows_warning = _("""\
Preview is currently not supported for Microsoft Windows, but you still
can publish the document to HTML.
If you need this functionality you can help the developer by packaging
pywebkitgtk for Windows: http://code.google.com/p/pywebkitgtk/\
""")
            self.preview = gtk.Label(windows_warning)
            self.preview_wrapper.add_with_viewport(self.preview)
            self.preview.show()
            self.preview = None


        # Configure interface
        #  Load theme of the editor
        #  I had to do this because Glade doesn't support creating a ListStore
        #  with a column of type gtk.gdk.Color
        self.editor_liststore = gtk.ListStore(
                                    str,
                                    str,
                                    gtk.gdk.Color,
                                    gtk.gdk.Color)
        self.editor_treeview.set_model(self.editor_liststore)
        #  Get and load avalaible themes
        editor_themes = self.config.items('editor-themes')
        editor_themes.sort()
        for theme in editor_themes:
            theme_set = theme[1].split('|')
            self.editor_liststore.append(
                        [theme[0],
                         theme_set[0].strip(),
                         gtk.gdk.Color(theme_set[1].strip()),
                         gtk.gdk.Color(theme_set[2].strip())
                        ]
                    )
        #  Once themes loaded, we can use the one specified
        editor_theme = self.config.get('editor', 'theme')
        editor_theme_set = editor_theme.split('|')
        if len(editor_theme_set) == 1:
            # We are using a theme:
            row = self.editor_liststore.get_iter_root()
            search_id = editor_theme_set[0].strip()
            while row is not None:
                id = self.editor_liststore.get_value(row, 0)
                if id == search_id: # Found!
                    # Select current theme in editor dialog.
                    self.editor_treeview.set_cursor(self.editor_liststore.get_path(row))
                    row = None
                else:
                    row = self.editor_liststore.iter_next(row)
                # Here we do not select the toggle button because theme is the default selection
        else:
            # We are using a custom theme
            font_color = gtk.gdk.Color(editor_theme_set[0].strip())
            background_color = gtk.gdk.Color(editor_theme_set[1].strip())
            # Load colors to fields in editor dialog
            self.editor_fontcolor_button.set_color(font_color)
            self.editor_backgroundcolor_button.set_color(background_color)
            # Select 'custom' optiom in editor dialog
            self.editor_theme_type_custom.set_active(True)

        #  Load font
        editor_font = self.config.get('editor', 'font')
        self.content_entry.modify_font(pango.FontDescription(editor_font))
        self.dialog_code_entry.modify_font(pango.FontDescription(editor_font))
        self.editor_font_button.set_font_name(editor_font)

        self.toggle_themes_types(None) # Update the editor based on previous theme and font settings

        #  Load dinamic elements
        #   Themes
        self.xhtmls_default_theme = self.config.get('xhtmls', 'default-theme')
        themes_list = self.get_subdirset(['themes', self.user_themes])
        if not self.xhtmls_default_theme in themes_list:
            self.xhtmls_default_theme = themes_list[0]
        theme_index = 0
        for theme in themes_list:
            self.xhtmls_themes_liststore.append([theme])
            if theme == self.xhtmls_default_theme:
                self.xhtmls_themes_combobox.set_active(theme_index) # Load default theme
            theme_index = theme_index + 1
        self.load_theme_requires(None) # Update requires
        #   User menu
        #    Templates
        templates_list = self.get_subdirset(['templates', self.user_templates])
        for template in templates_list:
            menu_item = gtk.MenuItem(template)
            self.menu_templates.get_submenu().append(menu_item)
            menu_item.connect('activate', self.dinamic_menu_cb, ('templates', template))
            menu_item.show()
        separator = gtk.SeparatorMenuItem()
        separator.show()
        self.menu_templates.get_submenu().append(separator)
        open_user_folder = gtk.MenuItem(_('My Nested folder'))
        open_user_folder.connect('activate', self.default_open_cb, self.user_dir)
        self.menu_templates.get_submenu().append(open_user_folder)
        open_user_folder.show()
        #    Examples
        examples_list = self.get_subdirset(['examples', self.user_examples])
        for example in examples_list:
            menu_item = gtk.MenuItem(example)
            self.menu_examples.get_submenu().append(menu_item)
            menu_item.connect('activate', self.dinamic_menu_cb, ('examples', example))
            menu_item.show()
        separator = gtk.SeparatorMenuItem()
        separator.show()
        self.menu_examples.get_submenu().append(separator)
        open_user_folder = gtk.MenuItem(_('My Nested folder'))
        open_user_folder.connect('activate', self.default_open_cb, self.user_dir)
        self.menu_examples.get_submenu().append(open_user_folder)
        open_user_folder.show()
        #   Recent files
        self.recent_files_reload()


        # Connect signals
        self.builder.connect_signals(self)


        # Initialize the interface
        self.fullscreen = False
        self.editor_treestore.append(None, [self.title_entry.get_text(), False, ''])
        self.treeview.set_cursor(self.root_path)
        self.content_entry.grab_focus()
        if self.config.getboolean('general', 'start-maximized'):
            self.window.maximize()
        self.content_buffer.clear_stacks()


        # Check arguments
        arguments = sys.argv[1:]
        if arguments:
            logger.info(_('Using arguments:'))
            logger.info(arguments)
            # FIXME, implement arguments and flags
            file_to_open = os.path.abspath(arguments[0])
            if os.path.exists(file_to_open):
                self.file_load(file_to_open)

        # Load last file, if enabled
        else:
            load_last_file = self.config.getboolean('general', 'load-last-document')
            if load_last_file:
                items = self.menu_recent.get_submenu().get_children()
                items[0].activate()
            # So... new file
            else:
                self.saved = True
                self.content_buffer.set_modified(False)

        # Start the save/backup daemon
        backup_timeout = self.config.getint('general', 'backup-timeout')
        self.backup_daemon = gobject.timeout_add(backup_timeout, self.file_backup)

        # Everything is done
        self.window.set_visible(True)


    #####################################
    # Utilities
    #####################################

    def get_subdirset(self, dir_list):
        """Return the set of subdirectories in the given directories list"""

        result = []

        for dirname in dir_list:
            dirname = os.path.abspath(dirname)
            for filename in os.listdir(dirname):
                if os.path.isdir(os.path.join(dirname, filename)) and not filename.startswith('.'):
                    result.append(filename)

        # Remove repeated ones
        result = list(set(result))
        result.sort()

        return result


    def default_open_cb(self, widget, something_to_open):
        """default_open() wrapper callback for widgets"""
        return self.default_open(something_to_open)


    #####################################
    # GUI functions
    #####################################

    def gtk_main_quit(self, widget, what=''): # What is required for delete-event
        """Gtk+ main quit function."""
        if not self.saved:
            response = self.dialog_not_saved.run()
            self.dialog_not_saved.hide()
            # Save
            if response == 2:
                self.file_save(widget)
                if not self.saved:
                    return True # Stop signal propagation
            # If Cancel
            if response <= 0:
                return True # Stop signal propagation
        gtk.main_quit()


    def modified(self, textbuffer, external=False):
        """Shows a visual feedback (*) when the document is modified"""
        if (not self.content_buffer.get_modified() or
            self.ignore_modifications) and not external:
            return
        else:
            if not self.current_file_name is None:
                self.window.set_title(self.current_file_name + '* - Nested')
            self.saved = False


    def fullscreen(self, widget):
        """Application fullscreen callback."""
        if self.fullscreen:
            self.window.unfullscreen()
            self.fullscreen = False
        else:
            self.window.fullscreen()
            self.fullscreen = True


    def toggle_focus_mode(self, widget):
        """Toggle the focus mode"""
        if self.focus_mode:
            #self.program_menu.show() # I want to hide this, but the associated accelerators stopped working :S
            self.program_toolbar.show()
            self.program_title.show()
            self.sections_column.show()
            self.program_statusbar.show()
            self.focus_mode = False
        else:
            #self.program_menu.hide()
            self.program_toolbar.hide()
            self.program_title.hide()
            self.sections_column.hide()
            self.program_statusbar.hide()
            self.focus_mode = True


    def toggle_about(self, widget):
        """Toggle about dialog visibility."""
        self.about.run()
        self.about.hide()


    def toggle_bloqued(self, widget, path):
        """Toggle TreeView bloqued cells."""
        self.editor_treestore.set_value(self.editor_treestore.get_iter_from_string(path), 1, not widget.get_active())
        self.content_entry.set_sensitive(widget.get_active())
        self.title_entry.set_sensitive(widget.get_active())
        self.format_toolbar.set_sensitive(widget.get_active())


    def sync_titles(self, widget):
        """Synchronize TreeView cell when title change."""
        treeiter = self.editor_treestore.get_iter(self.treeview.get_cursor()[0])
        self.editor_treestore.set_value(treeiter, 0, self.title_entry.get_text())


    def sync_tree_fields(self, widget):
        """Synchronize text fields and TreeView."""
        # Check if we have moved, if not, just flush the content back to the treestore
        current_path = self.treeview.get_cursor()[0]
        if self.current_section == current_path:
            current = self.editor_treestore.get_iter(current_path)
            title = self.title_entry.get_text()
            content = self.content_buffer.get_all_text()
            self.editor_treestore.set(current, 0, title, 2, content)
            return
        # Save content to previous section
        #  Get the previous section, only in case the previous sections still exists
        if self.current_section is not None:
            previous_iter = self.editor_treestore.get_iter(self.current_section)
            if previous_iter is not None: # Check that previous section wasn't removed
                # Get the content
                old_title = self.title_entry.get_text()
                old_content = self.content_buffer.get_all_text()
                self.editor_treestore.set(previous_iter, 0, old_title, 2, old_content)
            else:
                logger.error(_('Wait what? Error on sync_tree_fields() :S'))

        # Load the new section
        #  Get the data from the new section
        current = self.editor_treestore.get_iter(current_path)
        title, bloqued, text = self.editor_treestore.get(current, 0, 1, 2)
        #  Load that data to the interface
        self.title_entry.set_text(title)

        self.ignore_modifications = True
        self.content_buffer.set_text(text)
        self.content_buffer.clear_stacks()
        self.ignore_modifications = False
        self.content_buffer.set_modified(False)

        self.content_entry.set_sensitive(not bloqued)
        self.title_entry.set_sensitive(not bloqued)
        self.format_toolbar.set_sensitive(not bloqued)
        #  Save the current section we are working with
        self.current_section = current_path
        # Check if we are previewing, if so, then call the preview function
        self.sync_code_visual(None, None, self.markup_or_preview.get_current_page())


    def sync_code_visual(self, notebook, page, page_num):
        """Synchronize markup with preview."""

        if page_num == 1: # We were at 'markup' and turned to 'preview'

            # Disable toolbar
            self.format_toolbar.set_sensitive(False)

            if not self.preview: # Return if the preview is disabled
                return

            content = self.content_buffer.get_all_text().strip()
            html = '<html></html>'
            if content:
                try:
                    html = export.convert(content, 'xhtmls')
                except:
                    html = _('<html>Unable to preview. Please check the syntax.</html>')
            self.preview.load_html_string(html, 'file:///')
        else:
            # Enable toolbar if content is not bloqued
            current = self.editor_treestore.get_iter(self.current_section)
            bloqued = self.editor_treestore.get_value(current, 1)
            self.format_toolbar.set_sensitive(not bloqued)


    def _navigation_requested_cb(self, view, frame, networkRequest):
        """Handle preview widget navigation requests"""
        uri = networkRequest.get_uri()
        if uri.startswith('file://'):
            return False
        return True


    def toggle_link_types(self, widget):
        """Toggle visibility of the link types blocks."""
        if self.link_ext_type.get_active(): # External link selected
            self.link_ext_url.set_sensitive(True)
            self.link_ext_label.set_sensitive(True)
            self.link_int.set_sensitive(False)
            self.link_ext_url.grab_focus()
        else: # Internal link selected
            self.link_ext_url.set_sensitive(False)
            self.link_ext_label.set_sensitive(False)
            self.link_int.set_sensitive(True)
            self.link_int.grab_focus()


    def update_editor_appearance(self, widget):
        """Update the editor when some appearence option changed"""

        # Font
        font = self.editor_font_button.get_font_name()
        self.content_entry.modify_font(pango.FontDescription(font))
        self.dialog_code_entry.modify_font(pango.FontDescription(font))
        self.config.set('editor', 'font', str(font))
        # Custom theme
        if self.editor_theme_type_custom.get_active():
            f_color = self.editor_fontcolor_button.get_color()
            b_color = self.editor_backgroundcolor_button.get_color()
        # Predefined theme
        else:
            current_path = self.editor_treeview.get_cursor()[0]
            current = self.editor_liststore.get_iter(current_path)
            f_color, b_color = self.editor_liststore.get(current, 2, 3)
        self.config.set('editor', 'theme', str(f_color) + ' | ' + str(b_color))

        # Load settings
        self.content_entry.modify_text(gtk.STATE_NORMAL, f_color)
        self.content_entry.modify_base(gtk.STATE_NORMAL, b_color)
        self.dialog_code_entry.modify_text(gtk.STATE_NORMAL, f_color)
        self.dialog_code_entry.modify_base(gtk.STATE_NORMAL, b_color)

        # Save user values
        if self.window.get_visible():
            try:
                file_handler = open(self.user_config, 'w')
                self.config.write(file_handler)
            except:
                self.program_statusbar.push(0, _('Unable to save preferences. Are you in a read-only system?'))
            finally:
                file_handler.close()


    def toggle_themes_types(self, widget):
        """Toggle visibility of the theme types blocks."""
        if self.editor_theme_type_custom.get_active(): # Custom theme
            self.editor_fontcolor_button.set_sensitive(True)
            self.editor_backgroundcolor_button.set_sensitive(True)
            self.editor_treeview.set_sensitive(False)
        else: # Theme
            self.editor_fontcolor_button.set_sensitive(False)
            self.editor_backgroundcolor_button.set_sensitive(False)
            self.editor_treeview.set_sensitive(True)
        self.update_editor_appearance(widget)


    def find_file(self, group, filename):
        """Find the preferred file of a certain group (example, template, etc).
           This algorythm first search in the user folder, then in the system
           folder. It will return files in this order:
                - Region file (e.g. Hello.es_CR.t2t)
                - Language file (e.g. Hello.es.t2t)
                - Default file (English) (e.g. Hello.t2t)
        """

        region = '.' + self.lang
        lang = '.' + self.lang.split('_')[0]

        for path_type in [os.path.join(self.user_dir, group),
                          os.path.join(self.where_am_i, group)]:
            for option in [region, lang, '']:
                possible_file = os.path.join(path_type, filename, filename + option + '.t2t')
                if os.path.exists(possible_file):
                    return possible_file
        return None

    def dinamic_menu_cb(self, widget, data):
        """Routes actions of all dinamic menu elements"""

        group, name = data
        file_to_load = self.find_file(group, name)
        if file_to_load:

            if not self.saved:
                response = self.dialog_not_saved.run()
                self.dialog_not_saved.hide()
                # Save
                if response == 2:
                    self.file_save(widget)
                    if not self.saved:
                        return # Stop
                # If Cancel
                if response <= 0:
                    return # Stop

            self.file_load(file_to_load)
            self.current_file_path = tempfile.mkdtemp('', 'nested-')
            self.current_file_name = None

            # Copy payload if necessary
            template_dir = os.path.dirname(file_to_load)
            gallery_src = os.path.join(template_dir, 'images')
            gallery_dst = os.path.join(self.current_file_path, 'images')
            tex_header_src = os.path.join(template_dir, 'header.tex')
            tex_header_dst = os.path.join(self.current_file_path, 'header.tex')
            tex_title_src = os.path.join(template_dir, 'title.tex')
            tex_title_dst = os.path.join(self.current_file_path, 'title.tex')
            if os.path.exists(gallery_src):
                shutil.copytree(gallery_src, gallery_dst)
            if os.path.exists(tex_header_src):
                shutil.copyfile(tex_header_src, tex_header_dst)
            if os.path.exists(tex_title_src):
                shutil.copyfile(tex_title_src, tex_title_dst)

        else:
            self.program_statusbar.push(0, _('Error, file not found for entry: ') + name)


    def _menu_link_cb(self, widget):
        """Open help link"""

        links = {
            'help_markup_reference' : 'http://nestededitor.sourceforge.net/learn.html#markup',
            'help_user_manual'      : 'http://nestededitor.sourceforge.net/learn.html',
            'help_translate'        : 'http://nestededitor.sourceforge.net/participate.html#translate',
            'help_report_bug'       : 'http://sourceforge.net/p/nestededitor/tickets/',
            'help_find_help'        : 'https://groups.google.com/group/nestededitor',
        }

        name = gtk.Buildable.get_name(widget)

        if name in links.keys():
            self.default_open(links[name])


    def load_theme_requires(self, widget):
        """Load required libraries"""

        selection = self.xhtmls_themes_combobox.get_active()
        theme = self.xhtmls_themes_liststore[selection][0]
        # Check if is a user o system theme
        theme_path = os.path.join(self.user_dir, 'themes', theme)
        if not os.path.exists(theme_path):
            theme_path = os.path.join(self.where_am_i, 'themes', theme)
        # If theme exists
        if os.path.exists(theme_path):
            # Check if theme has a requires.txt
            theme_requires = os.path.join(theme_path, 'requires.txt')
            if os.path.exists(theme_requires):
                # Try to read the file
                try:
                    requires_file_handler = open(theme_requires, 'r')
                    content = requires_file_handler.read().strip()
                    if content:
                        lines = content.split('\n')
                        requires = []
                        for line in lines:
                            if not line.startswith('#'):
                                raw_requires = line.split(',')
                                for raw_require in raw_requires:
                                    lib = raw_require.strip()
                                    if lib:
                                        requires.append(lib)
                                if requires:
                                    break
                        if requires:
                            current_libs = self.xhtmls_libs.get_text().strip()
                            if not current_libs:
                                self.xhtmls_libs.set_text(requires[0])
                                del requires[0]
                            for lib in requires:
                                if not lib in current_libs:
                                    self.xhtmls_libs.set_text(current_libs + ', ' + lib)
                except:
                    logger.error(_('Unable to read {0} theme requires file. Do you have permissions?').format(theme))
                finally:
                    requires_file_handler.close()


    def recent_files_add(self, path):
        """Upgrade or add a new entry to the recent files file"""

        if os.path.exists(self.recent_files):
            try:
                # Read file
                recent_files = open(self.recent_files, 'r+')
                content = recent_files.read().strip()
                entries = []
                if content:
                    entries = content.split('\n')
                # Remove if exists (upgrade)
                try:
                    found = entries.index(path)
                    del entries[found]
                except:
                    pass
                # Add to the top
                entries.insert(0, path)
                # Clip list to user maximun
                user_max = self.config.getint('general', 'recent-files-limit')
                if len(entries) > user_max:
                    entries = entries[0:user_max]
                # Save file
                recent_files.seek(0)
                recent_files.write(('\n'.join(entries)).strip())
                recent_files.truncate()
            except:
                logger.error(_('Unable to add {0} to the recent files file. Are you in a read-only system?').format(path))
            finally:
                recent_files.close()


    def recent_files_reload(self):
        """Read recent files file and rebuild menu"""

        # Clear current menu
        self.menu_recent.set_submenu(gtk.Menu())

        # Load recent files file
        if os.path.exists(self.recent_files):

            entries = None
            try:
                # Read file
                recent_files = open(self.recent_files, 'r')
                content = recent_files.read().strip()
                if content:
                    entries = content.split('\n')
            except:
                logger.error(_('Unable to read the recent files file. Do you have permissions?'))
            finally:
                recent_files.close()

            # Create menu entries
            if entries:
                for entry in entries:
                    entry = entry.strip()
                    if entry:
                        menu_item = gtk.MenuItem(entry)
                        self.menu_recent.get_submenu().append(menu_item)
                        menu_item.connect('activate', self.recent_files_cb, entry)
                        menu_item.show()
            else:
                menu_item = gtk.MenuItem(_('<None>'))
                self.menu_recent.get_submenu().append(menu_item)
                menu_item.show()


    def recent_files_cb(self, widget, path):
        """Try to load a recent file"""

        if os.path.exists(path):

            if not self.saved:
                response = self.dialog_not_saved.run()
                self.dialog_not_saved.hide()
                # Save
                if response == 2:
                    self.file_save(widget)
                    if not self.saved:
                        return # Stop
                # If Cancel
                if response <= 0:
                    return # Stop

            # Load file
            self.file_load(path)
            self.current_file_path = os.path.dirname(path)
            self.current_file_name = os.path.basename(path)
        else:
            # Notification
            self.program_statusbar.push(0, _('Error, file not found: ') + path)
            # Remove entry
            try:
                # Read file
                recent_files = open(self.recent_files, 'r+')
                content = recent_files.read().strip()
                entries = []
                if content:
                    entries = content.split('\n')
                # Remove if exists
                try:
                    found = entries.index(path)
                    del entries[found]
                except:
                    pass
                # Save file
                recent_files.seek(0)
                recent_files.write(('\n'.join(entries)).strip())
                recent_files.truncate()
            except:
                logger.error(_('Unable to remove entry from recent files file. Read-only system?'))
            finally:
                recent_files.close()
            # Reload menu
            self.recent_files_reload()


    def _content_entry_resize(self, widget, allocation):
        """Move the search bar to the botom-right corner on window resize"""
        x = allocation.width - self.search_overlay.allocation.width - 10
        y = allocation.height - self.search_overlay.allocation.height - 10
        self.content_entry.move_child(self.search_overlay, x, y)


    def _do_find_cb(self, widget):
        if not self.search_overlay.get_visible():
            self._search_entry_changed(self.search_overlay_entry)
            self.search_overlay.show()
        self.search_overlay_entry.grab_focus()

    def _search_action(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self._close_search_overlay(widget)
            return
        if event.keyval == gtk.keysyms.Return:
            self.find_next(widget)
            return

    def _close_search_overlay(self, widget):
        self.content_buffer.set_search_text('')
        self.search_overlay.hide()
        self.content_entry.grab_focus()

    def _search_entry_changed(self, widget):
        self.content_buffer.set_search_text(widget.get_text())

    def find_next(self, widget, allow_restart=True):
        to_search = self.search_overlay_entry.get_text()
        insert_iter, selection_iter = self.content_buffer.get_selection_bounds()
        result = selection_iter.forward_search(to_search, gtk.TEXT_SEARCH_VISIBLE_ONLY)
        if result:
            match_start, match_end = result
            self.content_buffer.select_range(match_start, match_end)
            self.content_entry.scroll_to_iter(match_start, 0.2)
        elif allow_restart:
            self.content_buffer.place_cursor(self.content_buffer.get_start_iter())
            self.find_next(widget, allow_restart=False)

    def find_previous(self, widget, allow_restart=True):
        to_search = self.search_overlay_entry.get_text()
        insert_iter, selection_iter = self.content_buffer.get_selection_bounds()
        result = insert_iter.backward_search(to_search, gtk.TEXT_SEARCH_VISIBLE_ONLY)
        if result:
            match_start, match_end = result
            self.content_buffer.select_range(match_start, match_end)
            self.content_entry.scroll_to_iter(match_start, 0.2)
        elif allow_restart:
            self.content_buffer.place_cursor(self.content_buffer.get_end_iter())
            self.find_previous(widget, allow_restart=False)

    #####################################
    # Toolbar buttons callbacks
    #####################################

    def _get_focus_widget(self, parent):
        """Gets the widget that is a child of parent with the focus."""
        focus = parent.get_focus_child()
        if focus is None or focus.has_focus():#(focus.flags() & gtk.HAS_FOCUS):
            return focus
        else:
            return self._get_focus_widget(focus)


    def toggle_spell_checking(self, widget):
        """Enable/Disable spell checking"""
        if self.spell_checking is not None:
            if widget.get_active():
                self.spell_checking.enabled = True
            else:
                self.spell_checking.enabled = False


    def on_cut(self, widget, data=None):
        """Cuts currently selected text."""
        focus = self._get_focus_widget(self.window)
        classname = focus.__class__.__name__
        if classname == 'TextView':
            focus.get_buffer().cut_clipboard(self.text_clipboard, focus.get_editable())
        elif classname == 'TreeView':
            logger.debug('Cut is unimplemented for TreeView')
        elif focus is not None and hasattr(focus, "cut_clipboard"):
            focus.cut_clipboard()


    def on_copy(self, widget, data=None):
        """Copies currently selected text."""
        focus = self._get_focus_widget(self.window)
        classname = focus.__class__.__name__
        if classname == 'TextView':
            focus.get_buffer().copy_clipboard(self.text_clipboard)
        elif classname == 'TreeView':
            logger.debug('Copy is unimplemented for TreeView')
        elif focus is not None and hasattr(focus, "copy_clipboard"):
            focus.copy_clipboard()


    def on_paste(self, widget, data=None):
        """Pastes text to currently focused widget."""
        focus = self._get_focus_widget(self.window)
        classname = focus.__class__.__name__
        if classname == 'TextView':
            focus.get_buffer().paste_clipboard(self.text_clipboard, None, focus.get_editable())
        elif classname == 'TreeView':
            logger.debug('Paste is unimplemented for TreeView')
        elif focus is not None and hasattr(focus, "paste_clipboard"):
            focus.paste_clipboard()


    def editor_undo(self, widget):
        """Undo last modification on the document buffer"""
        self.content_buffer.undo()


    def editor_redo(self, widget):
        """Redo last modification on the document buffer"""
        self.content_buffer.redo()


    def toolbar_format(self, action):
        """Toolbar formating callback."""
        action_name = action.get_name()
        if action_name == 'GtkToolButton': # In case is called from a button and not a menu
            action_name = action.get_action().get_name()

        pre_markup  = bounded_markup[action_name][0]
        post_markup = bounded_markup[action_name][1]

        # Insert the PRE and POST markup
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.insert(start_iter, pre_markup)
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.insert(end_iter, post_markup)

        # Place the cursor at the beginning of the selection
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.place_cursor(start_iter)


    def open_dialog_properties(self, widget):
        """Show properties dialog."""
        self.dialog_properties.run()
        self.dialog_properties.hide()


    def dialog_properties_sanity_check(self, widget):
        """Check sanity in document properties"""

        pre = self.properties_preproc.get_buffer()
        post = self.properties_postproc.get_buffer()

        dirty_pre = pre.get_text(pre.get_start_iter(), pre.get_end_iter())
        dirty_post = post.get_text(post.get_start_iter(), post.get_end_iter())

        # Regexes
        cfgregex  = txt2tags.ConfigLines._parse_cfg
        prepostregex = txt2tags.ConfigLines._parse_prepost

        # Sanitize pre
        clean_pre = []
        for line in dirty_pre.split('\n'):
            # Test if is config line
            match = cfgregex.match(line)
            if match:
                # Get value of the config line
                name   = (match.group('name') or '').lower()
                value  = match.group('value')

                if name == 'preproc':
                    # Test if is preproc or postproc
                    valmatch = prepostregex.search(value)
                    if valmatch:
                        clean_pre.append(line)

        # Sanitize post
        clean_post = []
        for line in dirty_post.split('\n'):
            # Test if is config line
            match = cfgregex.match(line)
            if match:
                # Get value of the config line
                name   = (match.group('name') or '').lower()
                value  = match.group('value')

                if name == 'postproc':
                    # Test if is preproc or postproc
                    valmatch = prepostregex.search(value)
                    if valmatch:
                        clean_post.append(line)

        pre.set_text('\n'.join(clean_pre))
        post.set_text('\n'.join(clean_post))

        # FIXME: Not really, no changes could be made
        self.modified(None, external=True)

    def open_dialog_editor(self, widget):
        """Show editor dialog."""
        self.dialog_editor.run()
        self.dialog_editor.hide()


    def insert_list(self, action):
        """Insert an ordered / unordered list"""

        action_name = action.get_name()
        if action_name == 'GtkToolButton': # In case is called from a button and not a menu
            action_name = action.get_action().get_name()
        symbol = '- '
        if action_name == 'olist':
            symbol = '+ '

        start_iter, end_iter = self.content_buffer.get_selection_bounds()

        # If cursor is not in the first line
        insert = ''
        if not self.content_entry.starts_display_line(start_iter):
            insert = '\n'

        self.content_buffer.begin_user_action()

        selected_text = self.content_buffer.get_text(start_iter, end_iter, False)
        if selected_text:
            # Split the text (newlines), that is, get the lines separated.
            # For each line, append a hyphen in front of them
            # Insert two newlines.
            lines = selected_text.split('\n')
            formatted_lines = []
            for line in lines:
                formatted_lines.append(symbol + line)
            insert = insert + '\n'.join(formatted_lines) + '\n\n'
            self.content_buffer.delete(start_iter, end_iter)
            self.content_buffer.insert(start_iter, insert)
        else:
            # Insert a hyphen (plus sign) in front of the line, then go to the
            # end of that line and then insert two newlines
            self.content_buffer.insert(start_iter, insert + symbol)
            start_iter.forward_to_line_end()
            self.content_buffer.insert(start_iter, '\n\n')

        self.content_buffer.end_user_action()


    def open_dialog_link(self, widget):
        """Show links dialog."""
        # Reset text fields
        self.link_ext_url.set_text('http://')

        # Get the selected text and load it
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        selected_text = self.content_buffer.get_text(start_iter, end_iter, False)
        self.link_ext_label.set_text(selected_text)

        self.link_int.set_cursor(self.root_path)
        # Show dialog
        self.dialog_link.run()
        self.dialog_link.hide()


    def insert_link(self, widget):
        """Insert internal / external link at cursor."""
        # Remove selected text
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.delete(start_iter, end_iter)

        # Check what kind of link the user picked up
        if self.link_ext_type.get_active():
            # It's an external link
            url = self.link_ext_url.get_text()
            label = self.link_ext_label.get_text()
            # Form the markup
            if label == '':
                self.content_buffer.insert_at_cursor(url)
            else:
                link = '[' + label + ' ' + url + ']'
                self.content_buffer.insert_at_cursor(link)
        else:
            # It's an internal link

            #  Numeric
            #data = [self.link_int.get_cursor()[0], '', 1] # Path, title, position
            #self.editor_treestore.foreach(self.count_tree_position, data)
            #self.content_buffer.insert_at_cursor('[' + data[1] + ' #toc' + str(data[2]) + ']')

            #  Anchor
            path = self.link_int.get_cursor()[0]
            iter = self.editor_treestore.get_iter(path)
            title = self.editor_treestore.get_value(iter, 0) # Get the title
            self.content_buffer.insert_at_cursor('[' + title + ' #' + self.safe_string(title) + ']')


    def count_tree_position(self, model, path, iter, data):
        """Count the sequential position of the path"""
        if path == data[0]:
            data[1] = model.get_value(iter, 0) # Get the title
            return True
        else:
            data[2] = data[2] + 1 # Count # items before the wanted one



    def open_dialog_tables(self, widget):
        """Show tables dialog."""
        # Reset fields
        self.table_rows_spinbutton.set_value(3)
        self.table_columns_spinbutton.set_value(3)
        # Show dialog
        self.dialog_tables.run()
        self.dialog_tables.hide()


    def insert_table(self, widget):
        """Insert table at cursor."""
        rows = self.table_rows_spinbutton.get_value()
        columns = self.table_columns_spinbutton.get_value()
        table = ''
        if (rows >= 1) and (columns >= 1):
            table = '|          ' * int(columns) + '|\n'
            table = table * int(rows)
            self.content_buffer.insert_at_cursor(table.replace('| ', '||', 1))


    def insert_footnote(self, widget):
        """Insert footnote mark at cursor, then scroll and insert footnote text at the end of the document."""

        # Insert at current cursor the footnote mark
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.insert(start_iter, '°°_')

        # Insert footnote text token at the end of the section
        end_iter = self.content_buffer.get_end_iter()
        insert = '_°° '
        if not self.content_entry.starts_display_line(end_iter):
            insert = '\n' + insert
        self.content_buffer.insert(end_iter, insert)

        # Scroll to footnote text entry
        end_iter = self.content_buffer.get_end_iter()
        self.content_buffer.place_cursor(end_iter)
        self.content_entry.scroll_mark_onscreen(self.content_buffer.get_insert())


    def insert_math(self, widget):
        """Insert math example."""
        base = '\
<<<\n\
\\[ \n\
\\left( \\sum_{k=1}^n a_k b_k \\right)^{\\!\\!2} \\leq \n\
 \left( \\sum_{k=1}^n a_k^2 \\right) \\left( \\sum_{k=1}^n b_k^2 \\right) \n\
\\]\n\
>>>'
        # Insert code
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.insert(start_iter, base)

        # Add mathjax lib if necessary
        libs = self.xhtmls_libs.get_text()
        if not libs:
            self.xhtmls_libs.set_text('mathjax')
        elif not 'mathjax' in libs:
            self.xhtmls_libs.set_text(libs + ', mathjax')


    def open_dialog_code(self, widget):
        """Show code dialog."""
        self.dialog_code.run()
        self.dialog_code.hide()


    def insert_code(self, widget):
        """Insert user programming code."""

        # Get the code
        iter_start = self.dialog_code_content.get_start_iter()
        iter_end = self.dialog_code_content.get_end_iter()
        code = self.dialog_code_content.get_text(iter_start, iter_end).decode('utf-8')

        # Configure base string
        selected = self.dialog_code_type.get_active()
        if selected < 0:
            return None

        # Format text
        brush = self.dialog_code_type.get_model()[selected][1]
        code = '{{{ ' + brush + '\n' + code + '\n}}}'

        # Insert code
        start_iter, end_iter = self.content_buffer.get_selection_bounds()
        self.content_buffer.insert(start_iter, code)

        # Add syntaxhighlighter lib if necessary
        libs = self.xhtmls_libs.get_text()
        if not libs:
            self.xhtmls_libs.set_text('syntaxhighlighter')
        elif not 'syntaxhighlighter' in libs:
            self.xhtmls_libs.set_text(libs + ', syntaxhighlighter')

        # Clean-up
        self.dialog_code_content.set_text('')



def start():
    # Start the GUI
    AppContext.set_logger_level(AppContext.LOGGER_DEBUG)
    logger.info(_('Starting Nested...'))
    try:
        gobject.threads_init()
        gui = Nested()
        gtk.main()
    except KeyboardInterrupt:
        pass
