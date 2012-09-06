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
Loading Window Widget.
"""

from __future__ import division

from nested import *
from nested.utils import get_builder

import os
import logging
import gettext
import threading

import gtk
import gobject

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.getLogger(__name__)
_ = gettext.translation().gettext

class WorkingThread(threading.Thread):
    """
    Working thread subclass.
    """
    def __init__(self, data=None):
        """
        Object constructor.
        """
        super(WorkingThread, self).__init__()
        self.stop = False
        self.data = data

    def cancel(self):
        """
        Request for a cancelation of the executing task.
        """
        self.stop = True

    def run(self):
        """
        Override threading.Thread dummy run().
        """
        self.payload()

    def payload(self):
        """
        This function do the heavy work.
        Please override on subclasses.
        This function can use self.stop to know if a cancel was requested, also
        it can use self.data for any data it needs. self.data is set in the
        constructor when creating the thread.
        """
        raise Exception(
            _('Please subclass and implement WorkingThread.payload()'))


class LoadingWindow(object):
    """
    Show and handle a loading window.
    """

    def __init__(self, parent=None, label=None):
        """
        The object constructor.
        """

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'loading.glade')

        # Get the main objects
        self.wait = go('wait')
        self.label = go('label')
        self.progress = go('progress')

        # Configure object
        self.pulses = 0
        self._count = 0
        self.workthread = None

        if parent is not None:
            self.wait.set_transient_for(parent)
        if label is not None:
            self.label.set_markup(label)

        # Connect signals
        self.builder.connect_signals(self)

    def show(self, pulses, workthread):
        """
        Show loading window.
        This needs to be called from Gtk main thread.
        """
        if self.workthread is not None:
            logger.warning(
                _('There is a workthread active. Please call close() '
                  'or cancel() before starting a new loading event.'))
            return False

        if not isinstance(workthread, WorkingThread):
            raise Exception(
                    _('The thread needs to be a subclass of WorkingThread.'))

        self.workthread = workthread
        self.pulses = max(pulses, 1)
        self._count = 0
        self.wait.show()
        return True

    def pulse(self, text=None):
        """
        Pulse one step forward the progress bar.
        This can be called outside the Gtk main thread.
        """
        self._count += 1
        fraction = min(1.0, self._count / self.pulses)

        if text is None:
            text = '{0:0.1f}%'.format(fraction*100)

        gobject.idle_add(self.progress.set_fraction, fraction)
        gobject.idle_add(self.progress.set_text, text)

    def close(self):
        """
        Close the loading window.
        This should be called when the workthread has finished it's work.
        This can be called outside the Gtk main thread.
        """
        self.workthread = None
        gobject.idle_add(self.wait.hide)

    def cancel(self, widget=None):
        """
        Close the loading window.
        This should be called when the workthread has finished it's work.
        This can be called outside the Gtk main thread.
        """
        self.workthread.cancel()
        self.close()
