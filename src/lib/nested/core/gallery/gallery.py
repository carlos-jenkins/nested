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
Image gallery module for Nested.
"""

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

class Gallery(object):
    """
    Generic image gallery.
    """

    def __init__(self, parent=None, gallery_path=None, textview=None):
        """
        The object constructor.
        """
        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'gallery.glade')

        # Get the main objects
        self.main = go('main')
        self.images_filter = go('images_filter')
        self.wait = go('wait')

        # Configure interface
        if parent is not None:
            self.help_dialog.set_transient_for(parent)

        # Connect signals
        self.builder.connect_signals(self)

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

gobject.threads_init()
