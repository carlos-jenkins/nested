= ABOUT =

Nested is a specialized editor focused on creating structured documents such 
as reports, publications, presentations, books, etc. It is designed to help the
user concentrate on writing content without been distracted by format or 
markup. It offers a rich WYSIWYM interface where the user writes plain text 
with a lightweight markup language.

    http://nestededitor.sourceforge.net/

= AUTHOR =

    Carlos Jenkins <cjenkins@softwarelibrecr.org>

= DEPENDENCIES =

This software depends on the following python libraries (as Ubuntu package name):

    + python (>= 2.7)
    + python-gtk2 (>= 2.24)
    + python-webkit (optional)
    + python-gtkspellcheck (optional)

For LaTeX functionality the following packages are required:

    + texlive-publishers (IEEEtran style)
    + texlive (LaTeX, fonts, etc)
    + texlive-latex-extra (To use paralist package)

To improve LaTeX export install rubber compilation system:
    + rubber

To have spell checking languages translated install:
    + iso-codes

= SCRIPTS =

To run Nested:
    cd nested
    ./nested

To create a Python source distribution:
    python setup.py sdist
    
To extract l10n strings:
    cd po/
    extract_strings.sh

To create a Debian package:
    cd dist/debian/
    ./make_release.sh

To create a Windows executable (On a Windows Machine):
    cd dist\windows\
    make_release.bat

= TODO =

TODO v2.0:

    - Link dialog should load to the Label the currently selected word. - DONE
    - Improve Undo/Redo to include timed and action based modifications, not token based - DONE
    - Support rubber in GNU/Linux, instead of directly calling pdflatex. - DONE
    - Spell checking - DONE
    - Footnotes support - DONE

    - References support - IN PROGRESS
        - Finish BibMM : Undo/Redo, Modified/Saved, Errors
    - Modularize source code - IN PROGRESS
        - Refactoring footnotes, etc, to export.py (publish module)
    - Commad line publish - IN PROGRESS

    - Do not publish check in section.
    - Portable mode.
    - Fix preproc/postproc.
    - Percent in images.

    - Buttons for superscript and subscript
    - TreeView Copy/Cut/Paste
    - Find and replace
    - Hide emails to base64 images
    - Bookmarks
    - Document statistics
    - Undo/Redo stack for whole application (stack per section, stack for tree)
    - Add description, metatags
    - Extended themes that include syntax highlight.
    - epub publishing. (txt2tags > docbook > epub via epub-tools?)
    - Improve default/avalaible filters (@see textallion)
    - Consider Slidy target / theme

    - Bump to Gtk3 - POSTPONED
    - Bump to Python3 - POSTPONED

= KNOWN BUGS =

    - Name and selected path on dialog when creating new file/opening example/opening file is not changed.
    - Publishing might take a while, and no visual feedback is given.
    - The gallery can only handle raster images (gif, png, jpg), but vectorial ones like eps, svg, pdf 
      are more suitable for LaTeX targets.
    - Common procs (%!preproc:, %!postproc:) will be correctly interpreted and saved, 
      but when file is re-opened they will appear present in all targets. This is known
      limitation because a the way txt2tags process the file.
    - Website theme: content of section with commented title will not be avalaible. Feature?
    - All the content of a theme folder is published, but just style, script and images should be exported.

