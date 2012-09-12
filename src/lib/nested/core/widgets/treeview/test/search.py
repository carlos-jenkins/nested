import sys
import gtk
from os.path import normpath, dirname, abspath, realpath, join
from nested.core.widgets.treeview.search import TreeViewSearch

import logging
logging.set_levels(logging.DEBUG)

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

test_data = [
    ['1', 'book', 'abramowitz+stegun', 'Abramowitz, Stegun', 'Handbook of mathemat...', '1964', ''],
    ['11', 'book', 'hicks2001', 'Hicks', 'Design of a carbon f...', '2001', ''],
    ['22', 'inproceedings', 'author:06', 'Author, Author', 'Some publication tit...', '', ''],
    ['29', 'proceedings', 'conference:06', '', 'Proceedings of the x...', '2006', ''],
]

if __name__ == '__main__':

    try:

        builder = gtk.Builder()
        glade_path = join(WHERE_AM_I, 'search.glade')
        builder.add_from_file(glade_path)
        go = builder.get_object

        window = go('window')
        treeview = go('treeview')
        liststore = go('liststore')
        entry = go('entry')

        for i in test_data:
            liststore.append(i)

        search = TreeViewSearch(treeview, entry, True)

        window.connect('delete-event', lambda x,y: gtk.main_quit())

        window.show_all()
        gtk.main()

    except KeyboardInterrupt:
        pass
