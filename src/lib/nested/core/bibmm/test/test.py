import gtk
from os.path import normpath, dirname, abspath, realpath, join
from nested.core.bibmm.bibmm import BibMM

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

# Run standalone
if __name__ == '__main__':
    try:
        bib = BibMM()
        bib.load_bib(join(WHERE_AM_I, 'test.bib'))
        gtk.main()
    except KeyboardInterrupt:
        pass
