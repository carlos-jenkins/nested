
# Run standalone
if __name__ == '__main__':
    logger.info(_('Starting Bibliography Managment Module standalone...'))
    try:
        bib = BibMM()
        bib.load_bib('test/test.bib')
        gtk.main()
    except KeyboardInterrupt:
        pass
