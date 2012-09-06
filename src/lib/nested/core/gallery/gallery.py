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
from nested.utils import get_builder, safe_string, show_error

import os
import logging
import gettext
import shutil

import gtk
import gobject

from .loading import LoadingWindow, WorkingThread

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

# If you change the size of the thumbnails you'll need to update the
# cellrenderers at the Glade file.
THUMBNAILSIZE = (200, 300)
PREVIEWSIZE = (200, 300)
IMAGES = ['.png', '.jpg', '.gif']


class LoaderThread(WorkingThread):
    """
    Independent thread that performs the heavy images loading process.
    """
    def payload(self):
        # Get data
        obj = self.data
        gallery = obj.gallery_path

        # Get list of loaded and available
        already_loaded = [l[1] for l in obj.images_liststore]
        files_in_gallery = os.listdir(gallery)

        # Find files to load
        images = []
        for filename in files_in_gallery:
            # Check if stop was requested
            if self.stop:
                break
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(gallery, filename)
            if os.path.isfile(filepath) and \
                            ext in IMAGES and not filename in already_loaded:
                images.append((filepath, filename))

        if images and not self.stop:
            gobject.idle_add(obj.loading.show, len(images), self)

        for filepath, filename in images:
            # Check if stop was requested
            if self.stop:
                break

            # Load image in the gui
            info, width, height = gtk.gdk.pixbuf_get_file_info(filepath)
            size = '({w} x {h})'.format(w=width, h=height)
            thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(
                                                    filepath,
                                                    THUMBNAILSIZE[0],
                                                    THUMBNAILSIZE[1])
            gobject.idle_add(obj._load_thumbnail, thumbnail, filename , size)

            # Update progress
            obj.loading.pulse(filename)

        # Select last image
        gobject.idle_add(obj._select_last_image)

        # Close loading dialog
        obj.loading.close()


class ImporterThread(WorkingThread):
    """
    Independent thread that performs the heavy images import process.
    """
    def payload(self):
        gallery, images = self.data
        for image in images:

            # Check if stop was requested
            if self.stop:
                break

            # Safe rename image
            name, ext = os.path.splitext(os.path.basename(image))
            name = safe_string(name)
            ext = ext.lower()
            new_name = name + ext
            destination = os.path.join(gallery.gallery_path, new_name)

            # Rename destination if it exists
            num = 0
            while os.path.exists(destination):
                new_name = name + '_' + str(num) + ext
                destination = os.path.join(gallery.gallery_path, new_name)
                num += 1

            # Copy image
            try:
                logger.debug(_('Copying image to: {}').format(destination))
                shutil.copy(image, destination)
            except Exception as e:
                logger.error(
                    _('Unable to import image {}. Exception '
                      'thrown:\n{}').format(image, str(e)))

                # Update progress
                gallery.loading.pulse(_('Error importing {}').format(new_name))
                continue

            # Load image in the gui
            info, width, height = gtk.gdk.pixbuf_get_file_info(destination)
            size = '({w} x {h})'.format(w=width, h=height)
            thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(
                                                    destination,
                                                    THUMBNAILSIZE[0],
                                                    THUMBNAILSIZE[1])
            gobject.idle_add(gallery._load_thumbnail, thumbnail, new_name, size)

            # Update progress
            gallery.loading.pulse(new_name)

        # Select last image
        gobject.idle_add(gallery._select_last_image)

        # Close loading dialog
        gallery.loading.close()


class Gallery(object):
    """
    Generic image gallery.
    """

    def __init__(self, gallery_path=None, parent=None, textview=None):
        """
        The object constructor.
        """

        self.last_image = None
        self.gallery_path = gallery_path
        self.textview = textview

        # Create the interface
        self.builder, go = get_builder(WHERE_AM_I, 'gallery.glade')

        # Get the main objects
        self.gallery = go('gallery')

        self.add_image = go('add_image')
        self.preview_image= go('preview_image')
        self.preview_name = go('preview_name')
        self.preview_width = go('preview_width')
        self.preview_height = go('preview_height')

        self.images_view = go('images_view')
        self.images_liststore = go('images_liststore')
        self.images_filter = go('images_filter')

        loading_parent = parent if parent is not None else self.gallery
        self.loading = LoadingWindow(parent)

        # Configure interface
        self.images_filter.set_name('Images (*.png, *.jpg, *.gif)')
        self.images_filter.add_mime_type('image/png')
        self.images_filter.add_mime_type('image/jpeg')
        self.images_filter.add_mime_type('image/gif')
        self.images_filter.add_pattern('*.png')
        self.images_filter.add_pattern('*.jpg')
        self.images_filter.add_pattern('*.gif')
        self.add_image.add_filter(self.images_filter)

        # Configure interface
        if parent is not None:
            self.gallery.set_transient_for(parent)

        # Connect signals
        self.builder.connect_signals(self)

    #########################
    # UTILITIES
    #########################
    def _select_last_image(self):
        if self.last_image is not None:
            self._select_image(self.last_image)
        return False

    def _select_image(self, gtkiter):
        """
        Select given image iter in gallery.
        """
        if gtkiter:
            path = self.images_liststore.get_path(gtkiter)
            self.images_view.scroll_to_path(path, True, 0.5, 0.5)
            self.images_view.set_cursor(path, None, False)
            self.images_view.select_path(path)
            self.images_view.grab_focus()

    #########################
    # ADD IMAGE
    #########################
    def _open_add_cb(self, widget):
        """
        Open the add image dialog.
        """
        self._update_preview_cb(self.add_image)
        self.add_image.run()
        return False

    def _update_preview_cb(self, widget):
        """
        Update preview widget add selection dialog.
        """
        filename = widget.get_preview_filename()
        if filename is None:
            widget.set_preview_widget_active(False)
            return False
        logger.debug('Update preview for {}'.format(filename))
        try:
            # Get info
            info, width, height = gtk.gdk.pixbuf_get_file_info(filename)
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename,
                                                          PREVIEWSIZE[0],
                                                          PREVIEWSIZE[1])
            name, ext = os.path.splitext(os.path.basename(filename))
            ext = ext.lower()

            # Load preview
            self.preview_image.set_from_pixbuf(pixbuf)
            self.preview_name.set_text(safe_string(name) + ext)
            self.preview_width.set_text('{}px'.format(width))
            self.preview_height.set_text('{}px'.format(height))

            has_preview = True
        except:
            has_preview = False

        widget.set_preview_widget_active(has_preview)
        return False

    def _add_image_cb(self, widget):
        """
        Adds and image to the user gallery.
        """
        gallery = self.gallery_path
        if gallery is None:
            show_error(_('Cannot import images, the gallery path is'
                         'not configured.'), self.add_image)
            return False

        # Get images
        images = filter(os.path.isfile, self.add_image.get_filenames())
        if not images:
            show_error(_('Please select a filename.'), self.add_image)
            return False

        # Create image folder if needed
        if not os.path.exists(gallery):
            try:
                os.mkdir(gallery, 0755)
            except Exception as e:
                show_error(_('Error creating the gallery directory. '
                             'Read-only file system?'), self.add_image)
                logger.error(_('Unable to create gallery directory. '
                               'Exception thrown: \n{}').format(str(e)))
                return False

        elif not os.path.isdir(gallery):
            show_error(_('The gallery path is not a directory. '
                         'Cannot proceed.'), self.add_image)
            return False

        self.import_images(images)
        self._close_add_cb(widget)
        return False

    def _close_add_cb(self, widget):
        """
        Close the add image dialog.
        """
        self.add_image.hide()
        return False

    #########################
    # REMOVE IMAGE
    #########################
    def _remove_image_cb(self, widget):
        """
        Remove the currently selected image from gallery.
        """
        selection = self.images_view.get_cursor()
        if selection:
            # Get info of selected image
            path, cell = selection
            iterobj = self.images_liststore.get_iter(path)
            name = self.images_liststore.get_value(iterobj, 1)
            # Remove image
            if os.path.exists(self.gallery_path):
                image = os.path.join(self.gallery_path, name)
                if os.path.exists(image) and os.path.isfile(image):
                    os.remove(image)
            # Remove from view
            still_valid = self.images_liststore.remove(iterobj)
            if not still_valid:
                # Try going to the root
                remaining_images = len(self.images_liststore)
                if remaining_images > 0:
                    iterobj = self.images_liststore.get_iter(
                                            (remaining_images - 1, ))
                else:
                    iterobj = None

            # Move to valid item, if exists
            self._select_image(iterobj)

    #########################
    # IMAGE HANDLING
    #########################
    def _load_thumbnail(self, thumbnail, name, size):
        """
        Load a thumbnail to the images view.
        """
        # Insert image
        for index in range(len(self.images_liststore)):
            current_name = self.images_liststore[index][1]
            if name < current_name:
                self.last_image = self.images_liststore.insert(
                                                index, [thumbnail, name, size])
                return False
        self.last_image = self.images_liststore.append([thumbnail, name, size])
        return False

    def rescan_gallery(self):
        """
        Check if gallery rescan is needed.
        """
        if self.gallery_path is None or not os.path.isdir(self.gallery_path):
            return None

        workthread = LoaderThread((self))
        workthread.start()

        return workthread

    def import_images(self, images):
        """
        Import a list of images path to the gallery.
        """
        if not images:
            return

        workthread = ImporterThread((self, images))
        self.loading.show(len(images), workthread)
        workthread.start()

        return workthread

    #########################
    # LIFE CYCLE
    #########################
    def open_gallery(self, widget=None):
        """
        Open gallery dialog.
        """
        self.loading.show(1, None)
        self.rescan_gallery()
        self.gallery.run()

    def _close_gallery_cb(self, widget):
        """
        Close the gallery dialog.
        """
        self.gallery.hide()

    #########################
    # INSERTION
    #########################
    def _insert_image_cb(self, widget):
        print('Unimplemented')

    #~ def insert_image(self, widget):
        #~ """
        #~ Insert image markup at cursor.
        #~ """
#~
        #~ selection = self.images_view.get_cursor()
        #~ if selection:
            #~ # Get name of the image
            #~ path, cell = selection
            #~ iter = self.images_liststore.get_iter(path)
            #~ name = self.images_liststore.get_value(iter, 1)
#~
            #~ # Insert mark
            #~ pre_markup  = bounded_markup['image'][0]
            #~ post_markup = bounded_markup['image'][1]
            #~ text = pre_markup + name + post_markup
            #~ start_iter, end_iter = self.content_buffer.get_selection_bounds()
            #~ self.content_buffer.insert(start_iter, text)
