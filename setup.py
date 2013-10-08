NESTED_VERSION = '1.4'

long_description = \
"""\
Nested is a specialized editor focused on creating structured documents such \
as reports, publications, presentations, books, etc. It is designed to help the \
user concentrate on writing content without been distracted by format or \
markup. It offers a rich WYSIWYM interface where the user writes plain text \
with a lightweight markup language.\
"""


from distutils.core import setup
import os
import sys


def get_data(format_option=False):
    """Get recursively all the files from a directory without subversion control files"""

    package_data = ['config.ini', 'gui.glade', 'nested.svg', 'nested.png', 'logos.png']
    include_dirs = ['examples', 'icons', 'libraries', 'templates', 'themes', 'modules']


    base_dir = 'nested'
    
    if format_option:
        for index in range(len(package_data)):
            package_data[index] = os.path.join(base_dir, package_data[index])
        package_data = [('.', package_data)]
    
    def _list_clean_dir(dir):
        for dirname, subdirs, filenames in os.walk(dir, topdown=True):

            # Don't walk on subversion directories
            index = 0
            for subdir in subdirs:
                (parent, basename) = os.path.split(subdir)
                if basename == '.svn':
                    del subdirs[index]
                    break
                index = index + 1

            # Append clean filename
            if format_option:
                current_dir_files = []
                for filename in filenames:
                    filepath = os.path.join(base_dir, dirname, filename)
                    current_dir_files.append(filepath)
                package_data.append((dirname, current_dir_files))
                
            else:
                for filename in filenames:
                    filepath = os.path.join(dirname, filename)
                    package_data.append(filepath)
            

    current_dir = os.path.abspath(os.curdir)
    os.chdir(base_dir)
    for dir in include_dirs:
        _list_clean_dir(dir)
    os.chdir(current_dir)
    
    return package_data

kwargs = {}
if 'py2exe' in sys.argv:

    from distutils import log
    from distutils.errors import DistutilsError
 
    from py2exe.build_exe import py2exe as _py2exe
 
    class py2exe(_py2exe):
        def create_binaries(self, py_files, extensions, dlls):
            gtk_dlls = []
            for libdir in os.environ['PATH'].split(';'):
                if not os.path.exists(os.path.join(libdir, 'libgtk-win32-2.0-0.dll')):
                    continue
 
                for filename in os.listdir(libdir):
                    if os.path.splitext(filename)[1].lower() == '.dll':
                        gtk_dlls.append(os.path.join(libdir, filename))
 
            if not gtk_dlls:
                raise DistutilsError('could not find GTK+ to copy libraries and data files.')
 
            _py2exe.create_binaries(self, py_files, extensions, [l for l in dlls if l not in gtk_dlls])
 
            for dll in gtk_dlls:
                self.copy_file(dll, os.path.join(self.exe_dir, os.path.basename(dll)), preserve_mode=0)
 
            gtk_dir = os.path.dirname(os.path.dirname(gtk_dlls[0]))
            # subidr 'lib' and 'etc'
            for subdir in ('lib', 'etc'):
                self.copy_tree(os.path.join(gtk_dir, subdir), os.path.join(self.exe_dir, subdir))

            # subdir 'share'
            share_dir = os.path.join(self.exe_dir, 'share')
            if not os.path.exists(share_dir):
                os.mkdir(share_dir, 0755)
            for subdir in ('aclocal', 'glib-2.0', 'themes'):
                self.copy_tree(os.path.join(gtk_dir, 'share', subdir), os.path.join(share_dir, subdir))

    # This DLLs are included when building in Windows 7 and shoudn't
    dll_excludes = [     'w9xpopen.exe', 
                         'mswsock.dll', 
                         'powrprof.dll',
                         'API-MS-Win-Core-Debug-L1-1-0.dll',
                         'API-MS-Win-Core-DelayLoad-L1-1-0.dll',
                         'API-MS-Win-Core-ErrorHandling-L1-1-0.dll',
                         'API-MS-Win-Core-File-L1-1-0.dll',
                         'API-MS-Win-Core-Handle-L1-1-0.dll',
                         'API-MS-Win-Core-Heap-L1-1-0.dll',
                         'API-MS-Win-Core-Interlocked-L1-1-0.dll',
                         'API-MS-Win-Core-IO-L1-1-0.dll',
                         'API-MS-Win-Core-LibraryLoader-L1-1-0.dll',
                         'API-MS-Win-Core-Localization-L1-1-0.dll',
                         'API-MS-Win-Core-LocalRegistry-L1-1-0.dll',
                         'API-MS-Win-Core-Misc-L1-1-0.dll',
                         'API-MS-Win-Core-ProcessEnvironment-L1-1-0.dll',
                         'API-MS-Win-Core-ProcessThreads-L1-1-0.dll',
                         'API-MS-Win-Core-Profile-L1-1-0.dll',
                         'API-MS-Win-Core-String-L1-1-0.dll',
                         'API-MS-Win-Core-Synch-L1-1-0.dll',
                         'API-MS-Win-Core-SysInfo-L1-1-0.dll',
                         'DNSAPI.DLL',
                         'KERNELBASE.dll',
                         'NSI.dll',
                         'USP10.DLL'
                   ]
    
    kwargs = {'windows' : [{ 'script'         : 'nested.run',
                             'description'    : 'Nested - Editor for structured documents.',
                             'icon_resources' : [(0, 'dist/windows/installer/nested.ico')]
                           }],
              'zipfile' : None,
              'options' : { 'py2exe' : { 'dist_dir'     : os.path.join('dist', 'windows', 'executable'),
                                         #'packages'     : ['encodings'],
                                         'includes'     : ['cairo', 'pango', 'pangocairo', 'atk', 'gobject', 'gio', 'gtk', 'zlib', 'glib'],
                                         'excludes'     : ['webkit', 'Tkconstants', 'Tkinter', 'tcl'],
                                         'dll_excludes' : dll_excludes,
                                         #'skip_archive' : True, # Do not create Library.zip
                                         'bundle_files' : 3,    # Don't bundle
                                         'compressed'   : True,
                                         'optimize'     : 2
                                       }
                          },
              'data_files' : get_data(True),
              'cmdclass'   : { 'py2exe': py2exe }
             }

# Call main setup function
setup(name='nested',
      version=NESTED_VERSION,
      license='GPL2+',
      description='Specialized editor for structured documents.',
      long_description=long_description,
      author='Carlos Jenkns',
      author_email='cjenkins@softwarelibrecr.org',
      url='http://nestededitor.sourceforge.net/',
      packages=['nested'],
      package_data={'nested': get_data()},
      scripts=['nested.run'],
      **kwargs)
