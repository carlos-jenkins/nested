import sys
import gtk
from os.path import normpath, dirname, abspath, realpath, join
from nested.core.bibmm.bibmm import BibMM

import logging
logging.set_levels(logging.DEBUG)

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

if __name__ == '__main__':

    if len(sys.argv) == 2:
        bib_file = sys.argv[1]
    else:
        bib_file = join(WHERE_AM_I, 'test.bib')

    try:

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('BibMM Test')
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        window.set_default_size(800, 500)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        textview = gtk.TextView()
        launch = gtk.Button('Launch BibMM')
        cite = gtk.Button('Cite/Search BibMM')

        vbox = gtk.VBox()
        vbox.set_spacing(5)
        vbox.pack_start(launch, False, False)
        vbox.pack_start(cite, False, False)

        box = gtk.HBox()
        box.set_spacing(5)
        box.pack_start(textview, True, True)
        box.pack_start(vbox, False, False)

        window.add(box)
        window.show_all()

        bib = BibMM(window, textview)

        def _launch_cb(widget):
            bib.load_bib(bib_file)
            for row in bib.summary_liststore:
                print list(row)

        launch.connect('clicked', _launch_cb)
        #~ cite.connect('clicked', bib._cite_cb)


        gtk.main()

    except KeyboardInterrupt:
        pass
