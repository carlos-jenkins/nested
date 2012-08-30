
# Run standalone
if __name__ == '__main__':
    import logging
    logger.setLevel(level=logging.DEBUG)
    logger.info(_('Starting LaTeX Log Viewer standalone...'))
    try:
        log = LaTeXLogViewer()
        log.load_log('test/test.log')
        gtk.main()
    except KeyboardInterrupt:
        pass
