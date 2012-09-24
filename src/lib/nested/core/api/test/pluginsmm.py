import sys
import gtk
from os.path import normpath, dirname, abspath, realpath, join
from nested.core.api.pluginsmm import PluginsMM
from nested.core.api.test_plugin import NestedTestPlugin

import logging
logging.set_levels(logging.DEBUG)

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

class NestedDummy(object):
    """
    Dummy Nested class.
    """
    pass

if __name__ == '__main__':

    try:

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('PluginsMM Test')
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        window.set_default_size(800, 500)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        mb = gtk.MenuBar()
        menu = gtk.Menu()
        tools = gtk.MenuItem('Tools')
        tools.set_submenu(menu)
        mb.append(tools)

        menu.append(gtk.MenuItem('Characters counter'))
        menu.append(gtk.MenuItem('Spellcheck'))
        menu.append(gtk.MenuItem('Bibliography'))
        menu.append(gtk.SeparatorMenuItem())
        plugins = gtk.MenuItem('Plugins manager')
        menu.append(plugins)

        vbox = gtk.VBox()
        vbox.set_spacing(5)
        vbox.pack_start(mb, False, False)
        vbox.pack_start(gtk.Label(''), True, True)

        window.add(vbox)
        window.show_all()

        nested = NestedDummy()
        nested.main = window
        admin = PluginsMM(nested)
        could_load = admin._load(NestedTestPlugin)
        print('NestedTestPlugin could be loaded: {}.'.format(could_load))

        plugins.connect('activate', lambda x: admin.admin(x))

        gtk.main()

    except KeyboardInterrupt:
        pass
