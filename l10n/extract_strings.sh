#!/bin/bash
xgettext --keyword=translatable --sort-output -o nested.pot \
../nested/gui.glade ../nested/nested_gui.py \
../nested/modules/oxt_import/oxt_import.py \
../nested/modules/textviews/spellcheck.py \
../nested/modules/latex/log/viewer.glade ../nested/modules/latex/log/viewer.py \
../nested/modules/bibmm/bibmm.glade ../nested/modules/bibmm/bibmm.py ../nested/modules/bibmm/bibtexdef.py

echo "Done!"
