# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2013 Carlos Jenkins <carlos@jenkins.co.cr>
# Copyright (C) 2012 Maximilian Köhl <linuxmaxi@googlemail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.


"""
Context module for multiplatform and multilanguage applications.
This module provides (via monkey patching):
    1) A improved `logging` module, on top of the standard `logging` module,
       that allows to set the level of all the loggers used in the application.
    2) A much improved `gettext` module, on top of the standard `gettext`
       module, that supports multiplatform applications, with platform specific
       default locale directories and C library integration.
    3) A improved `os.path` module, on top of the standard `os.path` module,
       that takes into consideration frozen environments and allows modules to
       find where are they located.
"""

import os
import sys
import locale
import gettext
import logging
import tempfile

# Enable threading if PyGObject is available
try:
    from gi.repository import GObject
    GObject.threads_init()
except ImportError:
    pass

# Public Objects
__all__ = ['logger', 'respath', 'root', '_']



################################################################################
# LOGGING FIX
# -----------
#
# Fix Python's logging package, first, normalize function names according Python
# standards (fooBar() vs foo_bar()). Second, allow to set a global level for all
# application loggers.

# Save the old `logging.Manager`
logging._OldManager = logging.Manager

# New manager for logging which supports a setLevels method to set the same
# levels to all loggers requested with `logging.getLogger`
class Manager(logging.Manager):
    def __init__(self, *args, **kwargs):
        logging._OldManager.__init__(self, *args, **kwargs)
        self._current_level = logging.WARNING

    def getLogger(self, name):
        if name in self.loggerDict:
            return logging._OldManager.getLogger(self, name)
        else:
            logger = logging._OldManager.getLogger(self, name)
            if sys.platform.startswith('win'):
                handler = logging.FileHandler(
                        os.path.join(tempfile.gettempdir(), 'nested.log')
                    )
            else:
                handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(self._current_level)
            return logger

    def setLevels(self, level):
        if level < logging.NOTSET or level > logging.CRITICAL:
            return
        self._current_level = level
        for logger in self.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.setLevel(level)

# Monkey patch `logging` standard module
logging.Manager = Manager
_manager = Manager(logging.root)
logging.Logger.manager = _manager
logging.manager = _manager
logging.get_logger = logging.getLogger
logging.setLevels = _manager.setLevels
logging.set_levels = logging.setLevels

# Logging for the rest of the module
log = logging.get_logger(__name__)

# PUBLIC logger module
logger = logging



################################################################################
# OS.PATH FIX
# -----------
#
# Add to Python's standard `os.path` module the `respath()` function, from
# "resource path", that returns an absolute path to module's parent directory.
# The default behavior is to return the directory where the requesting source
# file is located. If running inside a frozen environment (py2exe for example)
# it returns the path where the exe or dll is located.
def respath(file_var):
    """
    Allows any module to know where to find its own directory. It also supports
    frozen environments.
    The `file_var` must be the current module's `__file__`.
    """
    frozen = getattr(sys, 'frozen', '')
    if not frozen:
        return os.path.normpath(os.path.dirname(
                    os.path.abspath(os.path.realpath(file_var))
                ))
    elif frozen in ('dll', 'console_exe', 'windows_exe'):
        return os.path.normpath(os.path.dirname(
                    sys.executable
                ))

# Monkey patch `os.path` standard module with `respath` function
os.path.respath = respath

# PUBLIC root variable for application use
root = respath(__name__)



################################################################################
# GETTEX FIX
# ----------
#
# A new `gettext.translation` function that cares about the localedir for every
# application that uses it. So a default path for all translation files could be
# given. Also the `fallback` argument would be `True` for every translation.

# Set LANG environment variable if not already set
# (Required by gettext module, variable not present on Windows OS)
if os.getenv('LANG') is None:
    lang, enc = locale.getdefaultlocale()
    os.environ['LANG'] = lang

# Save the old `gettext.translation`
gettext._old_translation = gettext.translation

# New Gettext class that uses OS dependent or application dependent locales dir
class Gettext():
    DEFAULT_DOMAIN = 'nested'  # If domain is `None`. This is not compatible
                               # with the python standard library.
    DEFAULT_DIRS = {
                    'linux' : '/usr/share/locale',
                    'windows' : os.path.join(root, 'l10n')
                }
    LOCALE_DIR = DEFAULT_DIRS['linux']
    if sys.platform.startswith('win'):
        LOCALE_DIR = DEFAULT_DIRS['windows']

    def translation(self, domain=None, localedir=None, languages=None,
                    class_=None, fallback=True, codeset=None, builder=False):

        domain = Gettext.DEFAULT_DOMAIN if domain is None else domain

        log.debug('Requesting translation for domain "{}"'.format(domain))

        # Fix translation on Windows
        if sys.platform.startswith('win'):
            try:
                import ctypes
                libintl = ctypes.cdll.LoadLibrary('intl.dll')
                libintl.bindtextdomain(domain, Gettext.LOCALE_DIR)
                libintl.bind_textdomain_codeset(domain, 'utf-8')
            except:
                log.error('Error loading C translation library.')

        # Search in default locale directory first
        if gettext.find(domain, Gettext.LOCALE_DIR):
            return gettext._old_translation(domain, Gettext.LOCALE_DIR,
                                            languages, class_, True, codeset)
        # Then in given locale directory
        return gettext._old_translation(domain, localedir, languages, class_,
                                        True, codeset)

    def set_locale_dir(self, locale_dir):
        Gettext.LOCALE_DIR = locale_dir

# Monkey patch `gettext` standard module
_gettext = Gettext()
gettext.translation = _gettext.translation
gettext.set_locale_dir = _gettext.set_locale_dir

# PUBLIC translation function
_ = gettext.translation().gettext
