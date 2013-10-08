#!/usr/bin/env python

import os
import shutil

where_am_i = os.path.normpath(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
os.chdir(where_am_i)

EXEC_DIR = '..\\executable\\'
INSTALL_SCRIPT = 'nested_installer.nsi'
INSTALL_TEMPLATE = 'nested_installer.nsi.in'

FILE_TEMPLATE = '  ${File} "${EXEC_DIR}'
SETOUTPATH_TEMPLATE = '  ${SetOutPath} "$INSTDIR\\'
ADDITEM_TEMPLATE = '  ${AddItem} "$INSTDIR\\'

def create_installer():
    """Create NSIS script based on a template"""
    
    # Check output file
    if not os.path.exists(EXEC_DIR):
        print('ERROR: The executable directory doesn\'t exists ' + EXEC_DIR)
    
    # Create file list
    lines = ['  !define EXEC_DIR "' + EXEC_DIR  + '"']
    os.chdir(EXEC_DIR)
    for dirname, subdirs, filenames in os.walk('.', topdown=True):

        dirname = os.path.normpath(dirname)
        if dirname == '.':
            dirname = ''
        
        if filenames:
            if dirname:
                lines.append(SETOUTPATH_TEMPLATE + dirname + '"')
            for filename in filenames:
                lines.append(FILE_TEMPLATE + dirname + '\\" "' + filename + '"')
        else:
            lines.append(ADDITEM_TEMPLATE + dirname + '"')

    content_generated = '\n'.join(lines)
    os.chdir(where_am_i)
    
    # Read template
    file_handler = open(INSTALL_TEMPLATE, 'r')
    try:
        content_template = file_handler.read()
    except:
        print('ERROR: Unable to read the template script ' + INSTALL_TEMPLATE)
        return
    finally:
        file_handler.close()
    
    # Write file
    content = content_template.replace('  ; FILE_PLACEHOLDER', content_generated, 1)
    
    file_handler = open(INSTALL_SCRIPT, 'w')
    try:
        file_handler.write(content)
    except:
        print('ERROR: Unable to open the install script ' + INSTALL_SCRIPT)
        print('Displaying generated file list:')
        print(content_generated)
        return
    finally:
        file_handler.close()

if __name__ == '__main__':
    create_installer()
