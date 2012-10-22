import os
import sys
import gtk
import subprocess
import nested.core.publish.txt2tags as txt2tags
from os.path import normpath, dirname, abspath, realpath, join, exists
from nested.core.bibmm.bibmm import BibMM
from nested.core.publish.bibliography import process_bibliography, copybib
from nested.utils import default_open, show_error

import logging
logging.set_levels(logging.DEBUG)

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

def do_publish(button, textbuffer):

    # Format text
    text = textbuffer.get_text(textbuffer.get_start_iter(),
                               textbuffer.get_end_iter()).decode('utf-8')
    formatted_text = process_bibliography(text, 'tex', 'apalike', 'test')
    print(formatted_text)

    # Convert text
    data = txt2tags.process_source_file(contents=formatted_text.split('\n'))
    tagged, config = txt2tags.convert_this_files([data])
    target_text = '\n'.join(tagged)
    if not target_text:
        show_error('The target document is empty.')
        return

    # Prepare publication directory
    publish_folder = join(WHERE_AM_I, 'publish')
    if not exists(publish_folder):
        os.makedirs(publish_folder)

    old_bib = join(publish_folder, 'test.bib')
    new_bib = join(WHERE_AM_I, 'test.bib')
    copybib(new_bib, old_bib)

    # Save file
    out_file = join(publish_folder, 'test.tex')
    with open(out_file, 'w') as f:
        f.write(target_text)

    # Convert
    os.chdir(publish_folder)
    ret_code = subprocess.call(['/usr/bin/rubber', '--pdf', out_file])
    os.chdir(WHERE_AM_I)
    if ret_code == 0:
        export_file = join(publish_folder, 'test.pdf')
    else:
        export_file = join(publish_folder, 'test.log')
    default_open(export_file)


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
        publish = gtk.Button('Publish document')

        vbox = gtk.VBox()
        vbox.set_spacing(5)
        vbox.pack_start(launch, False, False)
        vbox.pack_start(cite, False, False)
        vbox.pack_start(publish, False, False)

        box = gtk.HBox()
        box.set_spacing(5)
        box.pack_start(textview, True, True)
        box.pack_start(vbox, False, False)

        window.add(box)
        window.show_all()

        bib = BibMM(window, textview)
        bib.set_file(bib_file)

        launch.connect('clicked', bib.edit)
        cite.connect('clicked', bib.cite)
        publish.connect('clicked',
                        do_publish,
                        textview.get_buffer())

        gtk.main()

    except KeyboardInterrupt:
        pass

