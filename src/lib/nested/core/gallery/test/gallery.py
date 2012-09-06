from os.path import normpath, dirname, abspath, realpath, join
from nested.core.gallery.gallery import Gallery

import gtk

import logging
logging.set_levels(logging.DEBUG)

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

if __name__ == '__main__':
    try:
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Gallery Test')
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        window.set_default_size(800, 500)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        textview = gtk.TextView()

        gallery = Gallery(join(WHERE_AM_I, 'images'), window, textview)

        button = gtk.Button('Click to open gallery.')
        button.connect('clicked', gallery.open_gallery)

        box = gtk.HBox()
        box.set_spacing(5)
        box.pack_start(textview, True, True)
        box.pack_start(button, False, False)
        window.add(box)

        window.show_all()
        gtk.main()

    except KeyboardInterrupt:
        pass
