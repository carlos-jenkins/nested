# -*- coding: utf-8 -*-
#       nested_gui.py - Nested GUI
#
#       Copyright (c) 2011, 2012 Carlos Jenkins <cjenkins@softwarelibrecr.org>
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

"""@package nested_gui
Nested GUI main file.

This file holds the Nested class and starting point.
"""

import sys              # For command line arguments
import os               # For paths
import shutil           # For copying files
import gobject          # For handling GUI threads
import gtk              # For the GUI
import pango            # For Font Descriptions
import tempfile         # For temporal files
import ConfigParser     # To parse configurations
import txt2tags         # For loading files
import export           # For exporting content to PDF, HTML, etc.
import re               # For matching title when loading files
import unicodedata      # For transliteration
import Image            # For thumbnails
import StringIO         # For PIL Image to GdkPixbuf conversion
import hashlib          # For timehash function
import time             # For timehash function
import subprocess       # To call external apps
import threading        # For background processing
import webbrowser       # Support URL open in Windows
from . import custom_buffer                          # Syntax highlight and Undo/Redo
from .modules.latex.log.viewer import LaTeXLogViewer # To view LaTeX logs
from .modules.textviews.margin import Margin

####################################
# Use application context
from .context import AppContext

WHERE_AM_I = AppContext.where_am_i(__file__)
logger = AppContext.get_logger(__name__)
_ = AppContext('nested', builder=True).what_do_i_speak()
####################################
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

    def fix_glade(self, glade_file):
        """Fix Glade/GtkBuilder weird default behaviour for GtkScrolledWindow"""

        import xml.dom.minidom
        dom = xml.dom.minidom.parse(glade_file)

        for gui_object in dom.getElementsByTagName('object'):
            if gui_object.getAttribute('class') == 'GtkScrolledWindow':
                object_properties = gui_object.getElementsByTagName('property')
                hscrollbar_policy_found = False
                vscrollbar_policy_found = False
                for object_property in object_properties:

                    if not hscrollbar_policy_found and object_property.getAttribute('name') == 'hscrollbar_policy':
                        hscrollbar_policy_found = True

                    if not vscrollbar_policy_found and object_property.getAttribute('name') == 'vscrollbar_policy':
                        vscrollbar_policy_found = True

                if not hscrollbar_policy_found:
                    new_property = dom.createElement('property')
                    new_property.setAttribute('name', 'hscrollbar_policy')
                    new_property.childNodes = [dom.createTextNode('automatic')]
                    gui_object.insertBefore(new_property, gui_object.firstChild)

                if not vscrollbar_policy_found:
                    new_property = dom.createElement('property')
                    new_property.setAttribute('name', 'vscrollbar_policy')
                    new_property.childNodes = [dom.createTextNode('automatic')]
                    gui_object.insertBefore(new_property, gui_object.firstChild)

        return dom.toxml(encoding='UTF-8')


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
        self.sections_clipboard = gtk.Clipboard(selection='SECONDARY')

        # Get the GUI
        self.builder = gtk.Builder()
        self.builder.set_translation_domain('nested') # For l10n
        if sys.platform.startswith('win'):
            logger.info(_('Fixing Glade file for MS Windows.'))
            fixed_glade = self.fix_glade('gui.glade')
            # I don't want to build rsvg just for the logo :S
            fixed_glade = fixed_glade.replace(
                '<property name="icon">nested.svg</property>',
                '<property name="icon">nested.png</property>', 1)
            self.builder.add_from_string(fixed_glade)
        else:
            self.builder.add_from_file('gui.glade')
        go = self.builder.get_object
        self.window                        = go('main_window')
        self.about                         = go('dialog_about')
        self.please_wait                   = go('please_wait')
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

        # Configure textview
        if self.config.getboolean('general', 'show-line-numbers'):
            from .modules.textviews.lines import LineNumbers
            self.lines_numbers = LineNumbers(self.content_entry)
        if self.config.getboolean('general', 'show-margin'):
            from .modules.textviews.margin import Margin
            at_column = self.config.getint('general', 'margin-column')
            self.margin_widget = Margin(self.content_entry, at_column)

        #  Spell checking support
        self.spell_checking = None
        try:
            import locale
            from .modules.textviews.spellcheck import SpellChecker

            # Install all .oxt extensions, if any
            try:
                from .modules.oxt_import import deflate_oxt
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
            logger.error(_('Unable to import spellcheck: spell checking will be unavailable.'))
            raise excep

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

        #  Images dialog specific
        self.dialog_images                 = go('dialog_images')
        self.dialog_images_add             = go('dialog_images_add')
        self.images_liststore              = go('images_liststore')
        self.images_view                   = go('images_view')
        self.filter_images                 = go('filter_images')
        self.filter_images.set_name('Images (*.png, *.jpg, *.gif)')
        self.filter_images.add_mime_type('image/png')
        self.filter_images.add_mime_type('image/jpeg')
        self.filter_images.add_mime_type('image/gif')
        self.filter_images.add_pattern('*.png')
        self.filter_images.add_pattern('*.jpg')
        self.filter_images.add_pattern('*.gif')
        self.dialog_images_add.add_filter(self.filter_images)

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

    # Debug signal
    def print_signal(self, widget):
        print('Signal from: ')
        print(widget)


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


    def transliterate_string(self, string):
        """Transliterate given string"""
        nkfd_form = unicodedata.normalize('NFKD', unicode(string))
        normalized = u''.join([c for c in nkfd_form if not unicodedata.combining(c)])
        return normalized

    def safe_string(self, string):
        """Transform any string to a safer representation:
            e.g: 'Quién sabe caño' -> 'quien_sabe_cano'"""

        string = string.strip()
        normalized = self.transliterate_string(string)
        normalized = normalized.lower()
        normalized = normalized.replace(' ', '_')
        normalized = normalized.replace('-', '_')
        clean = []
        for c in normalized:
            if c.isalnum() or c == '_':
                clean.append(c)
        return ''.join(clean)


    def timehash(self, lenght=10):
        """Generates a hash based on current time"""
        if lenght < 1:
            lenght = 10
        hash = hashlib.sha1()
        hash.update(str(time.time()))
        return hash.hexdigest()[:lenght]


    def default_open_cb(self, widget, something_to_open):
        """default_open() wrapper callback for widgets"""
        return self.default_open(something_to_open)

    def default_open(self, something_to_open):
        """Open given file with default user program"""

        # Check if URL
        if something_to_open.startswith('http') or something_to_open.endswith('.html'):
            webbrowser.open(something_to_open)
            return 0

        ret_code = 0

        if sys.platform.startswith('linux'):
            ret_code = subprocess.call(['xdg-open', something_to_open])

        elif sys.platform.startswith('darwin'):
            ret_code = subprocess.call(['open', something_to_open])  # Untested

        elif sys.platform.startswith('win'):
            logger.debug(something_to_open)
            ret_code = subprocess.call(['start', something_to_open], shell=True)

        return ret_code


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


    def increase_font_size(self, widget):
        """Increase font size by one the of content entry"""
        self.change_font_size(1)

    def decrease_font_size(self, widget):
        """Decrease font size by one the of content entry"""
        self.change_font_size(-1)

    def change_font_size(self, amount):
        """Change font size of content entry"""
        font = self.content_entry.get_pango_context().get_font_description()
        new_size = font.get_size() + (amount * pango.SCALE)
        if new_size < pango.SCALE:
            new_size = pango.SCALE
        font.set_size(new_size)
        self.content_entry.modify_font(font)


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


    def check_prefix(self, prefix, string):
        """Check that everyline in the given string begins with given prefix"""
        lines = string.splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line.startswith(prefix):
                result.append(line)
        return ('\n').join(result)


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


    def select_image(self, iter):
        """Select given image in gallery"""
        if iter:
            path = self.images_liststore.get_path(iter)
            self.images_view.scroll_to_path(path, True, 0.5, 0.5)
            self.images_view.set_cursor(path, None, False)
            self.images_view.select_path(path)
            self.images_view.grab_focus()


    def open_dialog_images(self, widget):
        """Show images dialog / gallery."""

        # Load images if gallery is empty
        if not len(self.images_liststore):
            loading_launched = self.load_images()
            if loading_launched:
                return
        self.images_view.grab_focus()
        self.dialog_images.run()
        self.dialog_images.hide()


    def thumbnail_image(self, image):
        """Creates a thumbnail GdkPixbuf of given image"""

        # Create thumbnail
        img = Image.open(image)
        img.thumbnail((200, 300), Image.ANTIALIAS)

        # Convert to GdkPixbuf
        if img.mode != 'RGB':          # Fix IOError: cannot write mode P as PPM
            img = img.convert('RGB')
        buff = StringIO.StringIO()
        img.save(buff, 'ppm')
        contents = buff.getvalue()
        buff.close()
        loader = gtk.gdk.PixbufLoader('pnm')
        loader.write(contents, len(contents))
        pixbuf = loader.get_pixbuf()
        loader.close()

        return pixbuf


    def process_images(self, images):
        """
        Process images: create thumbnail and send them to the GUI.
        Note: This function is expected to be run in an independent thread
        """

        def _thread_append(image_data):
            self.images_liststore.append(image_data)
            return False

        def _thread_end():
            self.please_wait.hide()
            iter = self.images_liststore.get_iter((0, ))
            self.select_image(iter)
            self.open_dialog_images(None)
            return False

        for path, name in images:
            thumbnail = self.thumbnail_image(path)
            gobject.idle_add(_thread_append, [thumbnail, name])

        gobject.idle_add(_thread_end)


    def load_images(self):
        """Load all images in the image folder"""

        # Verify, again, if images folder exists, if not, do nothing
        images_folder = os.path.join(self.current_file_path, 'images')
        if not os.path.exists(images_folder):
            return

        # List all images
        files_in_images = os.listdir(images_folder)
        files_in_images.sort()
        images = []
        # Process files
        for filename in files_in_images:
            name, ext = os.path.splitext(filename)
            filename = os.path.join(images_folder, filename)
            if os.path.isfile(filename) and ext in supported_images:
                images.append([filename, name + ext])
        # Load files
        if images:
            self.please_wait.show()
            threading.Thread(target=self.process_images, name='Nested process_images()', args=[images]).start()
            return True
        return False


    def load_image(self, to_load):
        """Load an image to images view"""

        # Verify if images folder exists, if not, do nothing
        images_folder = os.path.join(self.current_file_path, 'images')
        if not os.path.exists(images_folder):
            return None

        if to_load:
            # Load image
            name, ext = os.path.splitext(to_load)
            path = os.path.join(images_folder, to_load)
            if not os.path.exists(path):
                logger.error(_('Unable to load image {0}.').format(to_load))
                return None
            thumbnail = self.thumbnail_image(path)

            # Insert image
            for index in range(len(self.images_liststore)):
                current_name = self.images_liststore[index][1]
                if name < current_name:
                    iter = self.images_liststore.insert(index, [thumbnail, name + ext])
                    return iter
            iter = self.images_liststore.append([thumbnail, name + ext])
            return iter


    def add_image(self, widget):
        """Adds and image to the user gallery"""

        response = self.dialog_images_add.run()
        self.dialog_images_add.hide()

        # If Cancel
        if response != 1:
            return

        # Get images
        filenames = self.dialog_images_add.get_filenames()
        images = []
        for filename in filenames:
            if os.path.isfile(filename):
                images.append(filename)

        if not images:
            warning = gtk.MessageDialog(self.window,
                gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_CLOSE, _('Please select a filename.'))
            warning.run()
            warning.destroy()
            self.add_image(widget)
            return

        # Create image folder if needed
        images_folder = os.path.join(self.current_file_path, 'images')
        if not os.path.exists(images_folder):
            os.mkdir(images_folder, 0755)

        # Process images
        last = None
        for image in images:

            # Rename image
            name, ext = os.path.splitext(os.path.basename(image))
            safe_name = self.safe_string(name)
            new_name = safe_name + ext
            destination = os.path.join(images_folder, new_name)

            # Rename destination if it exists
            num = 0
            while os.path.exists(destination):
                new_name = safe_name + '_' + str(num) + ext
                destination = os.path.join(images_folder, new_name)
                num += 1

            # Copy image
            shutil.copy(image, destination)

            # Load image
            last = self.load_image(new_name)

        # Scroll to last image inserted
        self.select_image(last)


    def insert_image(self, widget):
        """Insert image markup at cursor"""

        selection = self.images_view.get_cursor()
        if selection:
            # Get name of the image
            path, cell = selection
            iter = self.images_liststore.get_iter(path)
            name = self.images_liststore.get_value(iter, 1)

            # Insert mark
            pre_markup  = bounded_markup['image'][0]
            post_markup = bounded_markup['image'][1]
            text = pre_markup + name + post_markup
            start_iter, end_iter = self.content_buffer.get_selection_bounds()
            self.content_buffer.insert(start_iter, text)


    def remove_image(self, widget):
        """Remove from gallery the currently selected image"""

        selection = self.images_view.get_cursor()
        if selection:
            # Get info of selected image
            path, cell = selection
            iter = self.images_liststore.get_iter(path)
            name = self.images_liststore.get_value(iter, 1)
            # Remove image
            images_folder = os.path.join(self.current_file_path, 'images')
            if os.path.exists(images_folder):
                image = os.path.join(images_folder, name)
                if os.path.exists(image) and os.path.isfile(image):
                    os.remove(image)
            # Remove from view
            still_valid = self.images_liststore.remove(iter)
            if not still_valid:
                # Try going to the root
                if len(self.images_liststore):
                    iter = self.images_liststore.get_iter((0, ))
                else:
                    iter = None

            # Move to valid item, if exists
            self.select_image(iter)


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


    #####################################
    # Sections functions
    #####################################

    def _previous(self, treestore, current):
        """Get the previous row on a TreeStore given an iter."""
        # Get the current iter position
        current_path = treestore.get_path(current)
        current_depth = treestore.iter_depth(current)
        # Check that the current iter is not the first child
        if current_path[current_depth] > 0:
            # Get the previous iter
            previous_path = list(current_path) # Tuples are inmutable :S
            previous_path[current_depth] = previous_path[current_depth] - 1
            previous = treestore.get_iter(tuple(previous_path))
            return previous
        else:
            return None


    def _change_custody(self, treestore, old, new):
        """Migrate all the children of one row to another row"""
        # Check if the old row has children
        if treestore.iter_has_child(old):
            # Get the first child
            old_child = treestore.iter_children(old)
            while old_child is not None:
                # Get current child data
                title, bloqued, text = treestore.get(old_child, 0, 1, 2)
                # Add child to the new parent
                new_child = treestore.append(new, [title, bloqued, text])
                # Check if this child has children
                self._change_custody(treestore, old_child, new_child)
                # Update index
                old_child = treestore.iter_next(old_child)


    def _path_depend_on_path(self, from_path, to_path):
        """Check if the remove of one path will affect another one and on what index"""
        i_from = len(from_path) - 1
        i_to = len(to_path) - 1

        if i_from > i_to:
            return -1
        elif from_path[i_from] > to_path[i_from]:
            return -1
        else: # Check that both paths have the same root
            i = i_from - 1
            while i > -1:
                if from_path[i] != to_path[i]:
                    return -1
                i -= 1
            return i_from


    def add_section(self, widget):
        """Callback to add a section to the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Append a new row
        if current is not None: # Some row is selected
            parent = self.editor_treestore.iter_parent(current)
            new = self.editor_treestore.insert_after(parent, current, [_('Untitled section'), False, ''])
            # Much better, but TreeView doesn't generate cursor-changed signal
            # with this option, so no sync_tree_fields() is called.
            #selection.select_iter(new)
            self.treeview.set_cursor(self.editor_treestore.get_path(new))
            self.modified(None, external=True)


    def remove_section(self, widget):
        """Callback to remove a section to the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Remove the row
        if current is not None: # Some row is selected
            # Check that we are not removing the only remaining section
            path = self.editor_treestore.get_path(current)
            next = self.editor_treestore.iter_next(current)
            if (path != self.root_path) or (next is not None):
                # Ask confirmation if section has something or childs
                # TODO
                still_valid = self.editor_treestore.remove(current)
                self.current_section = None # The current section has disappeared
                # Set the cursor if iter still valid
                if still_valid:
                    self.treeview.set_cursor(self.editor_treestore.get_path(current))
                else:
                    self.treeview.set_cursor(self.root_path)
                self.modified(None, external=True)


    def forward_section(self, widget):
        """Callback to move up one section on the document."""
         # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move up a section
        if current is not None: # Some row is selected
            previous = self._previous(self.editor_treestore, current)
            if previous is not None: # Is not the first one
                self.editor_treestore.swap(current, previous)
                # Update current section
                self.current_section = self.treeview.get_cursor()[0]
                self.modified(None, external=True)


    def backward_section(self, widget):
        """Callback to move down one section on the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move down a section
        if current is not None: # Some row is selected
            next = self.editor_treestore.iter_next(current)
            if next is not None: # Is not the last one
                self.editor_treestore.swap(current, next)
                # Update current section
                self.current_section = self.treeview.get_cursor()[0]
                self.modified(None, external=True)


    def downgrade_section(self, widget):
        """Move a document section down one level."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Make the current section child of the previous row
        if current is not None: # Some row is selected
            previous = self._previous(self.editor_treestore, current)
            if previous is not None:
                # Get current section data
                title, bloqued, text = self.editor_treestore.get(current, 0, 1, 2)
                # Add new section with previous as its parent
                new = self.editor_treestore.append(previous, [title, bloqued, text])
                # Migrate all the childrens of the old section
                self._change_custody(self.editor_treestore, current, new)
                # Remove old section
                self.editor_treestore.remove(current)
                # Expand parent
                self.treeview.expand_row(self.editor_treestore.get_path(previous), True)
                # Get the new path
                new_path = self.editor_treestore.get_path(new)
                # Update current section
                self.current_section = new_path
                #selection.select_iter(new) # See comments on add_section
                # Select the new row
                self.treeview.set_cursor(new_path)
                self.modified(None, external=True)


    def upgrade_section(self, widget):
        """Move a document section up one level."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move the current row after his parent
        if current is not None: # Some row is selected
            parent = self.editor_treestore.iter_parent(current)
            if parent is not None:
                # Get current section data
                title, bloqued, text = self.editor_treestore.get(current, 0, 1, 2)
                # Insert the new row after his previous parent
                new = self.editor_treestore.insert_after(None, parent, [title, bloqued, text])
                # Migrate all the childrens of the old section
                self._change_custody(self.editor_treestore, current, new)
                # Remove old section
                self.editor_treestore.remove(current)
                # Expand the new node (in case it had children)
                self.treeview.expand_row(self.editor_treestore.get_path(new), True)
                # Get the new path
                new_path = self.editor_treestore.get_path(new)
                # Update current section
                self.current_section = new_path
                #selection.select_iter(new) # See comments on add_section
                # Select the new row
                self.treeview.set_cursor(new_path)
                self.modified(None, external=True)


    def drag_section_begin(self, treeview, drag_context):
        """Handles the movement of the current_section internal index to the new position of a row"""
        # Save content to the TreeStore, just in case
        title = self.title_entry.get_text()
        content = self.content_buffer.get_all_text()
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        model.set(iter, 0, title, 2, content)


    def drag_section_drop(self, treeview, drag_context, x, y, timestamp):
        """Handles the movement of the current_section internal index to the new position of a row"""
        # Get destination row
        row = treeview.get_dest_row_at_pos(x, y)
        if row is not None:
            to_path, how = row
        else: # This happens when the user drops the row to the end of the TreeView
            children = self.editor_treestore.iter_n_children(None)
            to_path = (children - 1, )
            how = gtk.TREE_VIEW_DROP_AFTER

        # Get the source row
        from_path = self.treeview.get_cursor()[0]

        # Check that the drop will change position of a row
        if from_path != to_path:

            # Find out if the move will affect final destination path
            compensation_index = self._path_depend_on_path(from_path, to_path)
            compensated_path = list(to_path)

            # Compensate
            if compensation_index >= 0:
                compensated_path[compensation_index] -= 1

            # Find where was put the row
            if how == gtk.TREE_VIEW_DROP_BEFORE:
                self.current_section = tuple(compensated_path)
            elif how == gtk.TREE_VIEW_DROP_AFTER:
                # Get the next position
                compensated_path[len(to_path) - 1] += 1
                self.current_section = tuple(compensated_path)
            else:
                #gtk.TREE_VIEW_DROP_INTO_OR_BEFORE & gtk.TREE_VIEW_DROP_INTO_OR_AFTER
                # Row will be the first child of the destination row (compensated)
                compensated_path.append(0)
                self.current_section = tuple(compensated_path)

            self.modified(None, external=True)

            # Debug
            #logger.debug('I guest the new position is: ' + str(self.current_section))


    def drag_section_end(self, treeview, drag_context):
        """Show and select the row just being dragged"""
        # Expand parent of the dragged element, if exist
        iter = self.editor_treestore.get_iter(self.current_section)
        parent = self.editor_treestore.iter_parent(iter)
        if parent is not None:
            treeview.expand_row(self.editor_treestore.get_path(parent), True)
        # Select the new row
        self.treeview.set_cursor(self.current_section)


    #####################################
    # Configuration functions
    #####################################

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


    #####################################
    # File (Save/Open/Export) functions
    #####################################

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


    def process_footnotes(self, section, target):
        """Process footnotes in a section"""

        class Namespace:
            pass

        def _format_footmarks_xhtmls(lines, title):
            """Format footmarks to the XHTML Strict format"""
            template = "''<a class=\"footnotemark\" href=\"#{0}_fn{1}\">[{1}]</a>''"
            fn_regex = re.compile(u'°°_')

            ns = Namespace()
            ns.fn_count = 1

            def _footmarks_xhtmls_replacer(m):
                """Regex replacement funtion for XHTML Strict format"""
                fn_link = template.format(title, str(ns.fn_count))
                ns.fn_count = ns.fn_count + 1
                return fn_link

            formatted_footmarks = []
            for line in lines:
                formatted_line = fn_regex.sub(_footmarks_xhtmls_replacer, line)
                formatted_footmarks.append(formatted_line)
            return formatted_footmarks

        def _format_footnotes_xhtmls(footnotes, title):
            """Format footnotes to the XHTML Strict format"""
            if not footnotes:
                return []
            formatted_footnotes = ["''' <div class=\"footnotes\"><ol>"]
            count = 1
            for footnote in footnotes:
                id_attr = title + '_fn' + str(count)
                formatted_footnotes.append("''<li id=\"" + id_attr + "\">''" + footnote + " ''</li>''")
                count = count + 1
            formatted_footnotes.append("''' </ol></div>")
            return formatted_footnotes

        def _format_footmarks_tex(lines):
            """Format footmarks to the TeX/LaTeX format"""
            formatted_footmarks = []
            for line in lines:
                formatted_footmarks.append(line.replace('°°_', r"''\footnotemark{}''"))
            return formatted_footmarks

        def _format_footnotes_tex(footnotes):
            """Format footnotes to the TeX/LaTeX format"""
            if not footnotes:
                return []
            formatted_footnotes = []
            counter = 0
            for footnote in footnotes:
                formatted_footnotes.append(r"''\stepcounter{footnote}\footnotetext{''" + footnote + " ''}''")
                counter = counter + 1
            formatted_footnotes = ['', r"''\addtocounter{footnote}{-%i}''" % counter] + formatted_footnotes + ['']
            return formatted_footnotes

        lines = section.split('\n')

        normal_lines = []
        footnotes = []
        in_footnote = False
        target_comments = re.compile('%(?P<alias>xhtmls|html|tex|latex|pdf|txt|text)%')
        special = []

        # Separate normal lines from footnote lines
        for line in lines:
            if line.startswith('_°° '):
                footnotes.append(line[4:].strip())
                in_footnote = True
            elif in_footnote and line.startswith('    '):
                full_line = footnotes.pop() + ' ' + line[4:].strip()
                footnotes.append(full_line)
            else:
                in_footnote = False
                if footnotes and target_comments.match(line):
                    special.append(line)
                else:
                    normal_lines.append(line)

        # Format footnotes
        if target == 'xhtmls':
            title = normal_lines[0].split('[')[1][:-1]
            target_footmarks = _format_footmarks_xhtmls(normal_lines, title)
            target_footnotes = _format_footnotes_xhtmls(footnotes, title)
        elif target == 'tex':
            target_footmarks = _format_footmarks_tex(normal_lines)
            target_footnotes = _format_footnotes_tex(footnotes)
        lines = target_footmarks + target_footnotes + special + ['']

        return '\n'.join(lines)

    def publish(self, widget):
        """Export document to the selected target"""

        # Flush the content first
        self.sync_tree_fields(None)

        # Get document
        header, full_config, body = self.compile_document()

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

        # Close all before publishing
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
                    section = self.process_footnotes(section, 'xhtmls')
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
                    section = self.process_footnotes(section, 'tex')
                processed_sections.append(section)
            body = processed_sections

        # Magic :D :D
        content = export.convert(''.join(body), target, header, config)

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
                content = export.latex_commands + content

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

if __name__ == '__main__':
    start()
