import gtk
from nested.plugins.calculator.calculator import Calculator

import logging
logging.set_levels(logging.DEBUG)

if __name__ == '__main__':
    try:
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Calculator Test')
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        window.set_default_size(800, 500)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        textview = gtk.TextView()

        calc = Calculator(textview)

        box = gtk.HBox()
        box.set_spacing(5)
        box.pack_start(textview, True, True)
        box.pack_start(calc.main, False, True)
        window.add(box)

        window.show_all()
        gtk.main()

    except KeyboardInterrupt:
        pass
