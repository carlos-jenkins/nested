import time
import threading

import gtk

from nested.core.gallery.loading import LoadingWindow, WorkingThread

class MyWorkingThread(WorkingThread):
    def payload(self):
        loading = self.data
        for s in range(steps):
            if self.stop:
                break
            loading.pulse()
            print('Pulse {}.'.format(s))
            time.sleep(0.1)
        if self.stop:
            print('Working thread canceled.')
        else:
            print('Working thread ended.')
        loading.close()

if __name__ == '__main__':
    try:
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Loading Test')
        window.connect('delete-event', lambda x,y: gtk.main_quit())
        window.set_default_size(200, 100)
        window.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        loading = LoadingWindow(window)
        steps = 100

        def _launch_work(widget):
            workthread = MyWorkingThread(loading)
            loading.show(steps, workthread)
            workthread.start()

        button = gtk.Button('Click me to start working.')
        button.connect('clicked', _launch_work)
        window.add(button)

        window.show_all()
        gtk.main()

    except KeyboardInterrupt:
        pass
