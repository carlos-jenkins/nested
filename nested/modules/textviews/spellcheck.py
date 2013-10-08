# -*- coding: utf-8 -*-
#       spellcheck.py - Enchant based spell checking for PyGtk TextBuffer
#
#       Copyright (c) 2012 Carlos Jenkins <cjenkins@softwarelibrecr.org>
#       Copyright (c) 2011, 2012 Maximilian Köhl <linuxmaxi@googlemail.com>
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

"""@package spellcheck
This package provides spell checking capabilities to PyGtk TextBuffers. This
is a port from PyGObject to PyGtk (backward port) from:

    https://github.com/koehlma/pygtkspellcheck

Special care was taken to maintain the original PyGObject compatibility. If you
need to use this module in PyGObject search the code for "# PyGObject", only 6
lines are completely different.

How to use this package:

-------------------------------------------------------------------
import locale
from spellcheck import SpellChecker
import gtk

def quit(*args):
    gtk.main_quit()

for code, name in SpellChecker.languages:
    print('code: %5s, language: %s' % (code, name))

window = gtk.Window()
view = gtk.TextView()
if SpellChecker.language_exists(locale.getdefaultlocale()[0]):
    spellchecker = SpellChecker(view, locale.getdefaultlocale()[0])
else:
    spellchecker = SpellChecker(view)
window.set_default_size(600, 400)
window.add(view)
window.show_all()
window.connect('delete-event', quit)
gtk.main()
-----------------------------------------------------------------------
"""

import re
import enchant
import gtk #from gi.repository import Gtk as gtk # PyGObject
import nested.modules.locales as locales #import locales

####################################
# Use application context
if __name__ == '__main__':
    import sys
    sys.path.append('../..')
from nested.context import AppContext

WHERE_AM_I = AppContext.where_am_i(__file__)
_ = AppContext().what_do_i_speak()
####################################

class SpellChecker(object):
    """Spell checking object for PyGtk TextBuffers"""

    NUMBER = re.compile('[0-9.,]+')

    # Available languages
    languages = [(language, locales.code_to_name(language)) for language in enchant.list_languages()]
    _language_map = dict(languages)

    @classmethod
    def set_dictionary_path(cls, path):
        """Additional paths to find dictionaries"""
        enchant.set_param('enchant.myspell.dictionary.path', path)
        SpellChecker.languages = [(language, locales.code_to_name(language)) for language in enchant.list_languages()]
        SpellChecker._language_map = dict(SpellChecker.languages)

    @classmethod
    def language_exists(cls, language):
        """Check if a given code is available for spell checking"""
        return language in SpellChecker._language_map

    def __init__(self, view, language='en', prefix='spellchecker'):

        self._enabled = True
        self._view = view
        self._view.connect('button-press-event', self._button_press_event)
        self._view.connect('populate-popup', self._populate_popup)
        self._view.connect('popup-menu', self._popup_menu)
        self._prefix = prefix
        self._misspelled = gtk.TextTag(name='%s-misspelled' % (self._prefix))
        self._misspelled.set_property('underline', 4)
        self._language = language
        self._broker = enchant.Broker()
        self._dictionary = self._broker.request_dict(language)
        self._deferred_check = False
        self._ignore_regex = re.compile('')
        self._ignore_expressions = []
        self.buffer_setup()

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language
        self._dictionary = self._broker.request_dict(language)
        self.recheck_all()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self.recheck_all()
        else:
            start, end = self._buffer.get_bounds()
            self._buffer.remove_tag(self._misspelled, start, end)

    def append_ignore_regex(self, regex):
        self._ignore_expressions.append(regex)
        self._ignore_regex = re.compile('|'.join(self._ignore_expressions))

    def remove_ignore_regex(self, regex):
        self._ignore_expressions.remove(regex)
        self._ignore_regex = re.compile('|'.join(self._ignore_expressions))

    def recheck_all(self):
        start, end = self._buffer.get_bounds()
        self._check_range(start, end, True)

    def buffer_setup(self):
        self._buffer = self._view.get_buffer()
        self._buffer.connect('insert-text', self._insert_text_before)
        self._buffer.connect_after('insert-text', self._insert_text_after)
        self._buffer.connect_after('delete-range', self._delete_range_after)
        self._buffer.connect_after('mark-set', self._mark_set)
        start = self._buffer.get_bounds()[0]
        self._mark_insert_start = self._buffer.create_mark('%s-insert-start' % (self._prefix), start, True)
        self._mark_insert_end = self._buffer.create_mark('%s-insert-end' % (self._prefix), start, True)
        self._mark_click = self._buffer.create_mark('%s-click' % (self._prefix), start, True)
        self._table = self._buffer.get_tag_table()
        self._table.add(self._misspelled)
        self.recheck_all()

    def _ignore_all(self, item, word):
        self._dictionary.add_to_session(word)
        self.recheck_all()

    def _add_to_dictionary(self, item, word):
        self._dictionary.add_to_pwl(word)
        self.recheck_all()

    def _language_change_callback(self, item, language):
        self.language = language

    def _replace_word(self, item, oldword, newword):
        start, end = self._word_extents_from_mark(self._mark_click)
        offset = start.get_offset()
        self._buffer.begin_user_action()
        self._buffer.delete(start, end)
        self._buffer.insert(self._buffer.get_iter_at_offset(offset), newword)
        self._buffer.end_user_action()
        self._dictionary.store_replacement(oldword, newword)

    def _word_extents_from_mark(self, mark):
        start = self._buffer.get_iter_at_mark(mark)
        if not start.starts_word():
            start.backward_word_start()
        end = self._clone_iter(start)
        if end.inside_word():
            end.forward_word_end()
        return start, end

    def _mark_inside_word(self, mark):
        iter = self._buffer.get_iter_at_mark(mark)
        return iter.inside_word()

    def _build_languages_menu(self):
        menu = gtk.Menu()
        group = gtk.RadioMenuItem() #group = [] # PyGObject
        for code, name in SpellChecker.languages:
            item = gtk.RadioMenuItem(group=group, label=name) #item = gtk.RadioMenuItem.new_with_label(group, name) # PyGObject
            item.connect('activate', self._language_change_callback, code)
            if code == self.language:
                item.set_active(True)
            #group.append(item) # PyGObject
            menu.append(item)
        menu.show_all()
        return menu

    def _build_suggestion_menu(self, word):
        menu = gtk.Menu()
        suggestions = self._dictionary.suggest(word)
        if not suggestions:
            item = gtk.MenuItem()
            label = gtk.Label('')
            label.set_markup('<i>(%s)</i>' % _('No suggestions'))
            item.add(label)
            menu.append(item)
        else:
            for suggestion in suggestions:
                item = gtk.MenuItem()
                label = gtk.Label('')
                label.set_markup('<b>%s</b>' % (suggestion))
                label.set_alignment(0.0, 0.5) #label.set_halign(gtk.Align(1)) # PyGObject
                item.add(label)
                item.connect('activate', self._replace_word, word, suggestion)
                menu.append(item)
        menu.append(gtk.SeparatorMenuItem())
        item = gtk.MenuItem(label=_('Add "%s" to Dictionary') % word)
        item.connect('activate', self._add_to_dictionary, word)
        menu.append(item)
        item = gtk.MenuItem(label=_('Ignore all'))
        item.connect('activate', self._ignore_all, word)
        menu.append(item)
        menu.show_all()
        return menu

    def _button_press_event(self, widget, event):
        if not self._enabled:
            return
        if event.button == 3:
            if self._deferred_check:
                self._check_deferred_range(True)
            x, y = self._view.window_to_buffer_coords(2, int(event.x), int(event.y)) #event.x, event.y) # PyGObject
            iter = self._view.get_iter_at_location(x, y)
            self._buffer.move_mark(self._mark_click, iter)
        return False

    def _populate_popup(self, entry, menu):
        if not self._enabled:
            return
        separator = gtk.SeparatorMenuItem()
        separator.show()
        menu.prepend(separator)
        languages = gtk.MenuItem(label=_('Languages'))
        languages.set_submenu(self._build_languages_menu())
        languages.show()
        menu.prepend(languages)
        if self._mark_inside_word(self._mark_click):
            start, end = self._word_extents_from_mark(self._mark_click)
            if start.has_tag(self._misspelled):
                word = self._buffer.get_text(start, end, False)
                suggestions = gtk.MenuItem(label=_('Suggestions'))
                suggestions.set_submenu(self._build_suggestion_menu(word))
                suggestions.show()
                menu.prepend(suggestions)

    def _popup_menu(self, *args):
        if not self._enabled:
            return
        iter = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        self._buffer.move_mark(self._mark_click, iter)
        return False

    def _insert_text_before(self, textbuffer, location, text, len):
        if not self._enabled:
            return
        self._buffer.move_mark(self._mark_insert_start, location)

    def _insert_text_after(self, textbuffer, location, text, len):
        if not self._enabled:
            return
        start = self._buffer.get_iter_at_mark(self._mark_insert_start)
        self._check_range(start, location);
        self._buffer.move_mark(self._mark_insert_end, location);

    def _delete_range_after(self, textbuffer, start, end):
        if not self._enabled:
            return
        self._check_range(start, end);

    def _mark_set(self, textbuffer, location, mark):
        if not self._enabled:
            return
        if mark == self._buffer.get_insert() and self._deferred_check:
            self._check_deferred_range(False);

    def _clone_iter(self, iter):
        return self._buffer.get_iter_at_offset(iter.get_offset())

    def _check_word(self, start, end):
        word = self._buffer.get_text(start, end, False)
        if not SpellChecker.NUMBER.match(word) and (not self._ignore_regex.match(word) or not len(self._ignore_expressions)):
            if not self._dictionary.check(word):
                self._buffer.apply_tag(self._misspelled, start, end)

    def _check_range(self, start, end, force_all=False):
        if end.inside_word():
            end.forward_word_end()
        if not start.starts_word():
            if start.inside_word() or start.ends_word():
                start.backward_word_start()
            else:
                if start.forward_word_end():
                    start.backward_word_start()
        cursor = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        precursor = self._clone_iter(cursor)
        precursor.backward_char()
        highlight = cursor.has_tag(self._misspelled) or precursor.has_tag(self._misspelled)
        self._buffer.remove_tag(self._misspelled, start, end)
        if not start.get_offset():
            start.forward_word_end()
            start.backward_word_start()
        wstart = self._clone_iter(start)
        while wstart.compare(end) < 0:
            wend = self._clone_iter(wstart)
            wend.forward_word_end()
            inword = (wstart.compare(cursor) < 0) and (cursor.compare(wend) <= 0)
            if inword and not force_all:
                if highlight:
                    self._check_word(wstart, wend)
                else:
                    self._deferred_check = True
            else:
                self._check_word(wstart, wend)
                self._deferred_check = False
            wend.forward_word_end()
            wend.backward_word_start()
            if wstart.equal(wend):
                break
            wstart = self._clone_iter(wend)

    def _check_deferred_range(self, force_all):
        start = self._buffer.get_iter_at_mark(self._mark_insert_start)
        end = self._buffer.get_iter_at_mark(self._mark_insert_end)
        self._check_range(start, end, force_all)

