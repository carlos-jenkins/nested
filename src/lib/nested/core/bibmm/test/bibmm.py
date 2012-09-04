import sys
import gtk
from os.path import normpath, dirname, abspath, realpath, join
from nested.core.bibmm.bibmm import BibMM

WHERE_AM_I = normpath(dirname(abspath(realpath(__file__))))

if __name__ == '__main__':

    if len(sys.argv) == 2:
        bib_file = sys.argv[1]
    else:
        bib_file = join(WHERE_AM_I, 'test.bib')

    try:
        bib = BibMM()
        bib.load_bib(bib_file)
        gtk.main()
    except KeyboardInterrupt:
        pass
