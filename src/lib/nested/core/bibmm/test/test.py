import gtk
from nested.core.bibmm.bibmm import BibMM

# Run standalone
if __name__ == '__main__':
    try:
        bib = BibMM()
        bib.load_bib('test/test.bib')
        gtk.main()
    except KeyboardInterrupt:
        pass
