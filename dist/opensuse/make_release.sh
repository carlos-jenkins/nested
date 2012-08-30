#!/bin/bash

# Create Python sdist
echo "Entering to the distribution root..."
cd ../../
python setup.py sdist
echo "Entering to dist..."
cd dist/

# Transform source package
SDIST=`find . -maxdepth 1 -type f -name *.tar.gz`
CONSDIST=`echo $SDIST | sed s/.tar.gz/.tar.bz2/`
gunzip --to-stdout $SDIST | bzip2 > $CONSDIST
mv $CONSDIST opensuse/
