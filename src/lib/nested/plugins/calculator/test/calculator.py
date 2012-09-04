import gtk
from nested.plugins.calculator.calculator import Calculator

if __name__ == '__main__':
    try:
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Calculator Test')

        calc = Calculator()

        window.set_default_size(300, 500)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        window.add(calc.main)
        window.show_all()
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        gtk.main()

    except KeyboardInterrupt:
        pass
