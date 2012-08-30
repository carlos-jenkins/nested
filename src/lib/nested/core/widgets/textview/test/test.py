# -*- coding:utf-8 -*-

import sys
import gtk

sys.path.insert(0, '.')
from nested.core.widgets.textview import CodeView

if __name__ == '__main__':
    def quit(*args):
        gtk.main_quit()

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title('CodeView Test')
    view = CodeView()
    window.set_default_size(600, 400)
    window.add(view)
    window.show_all()
    window.connect('delete-event', quit)
    gtk.main()
