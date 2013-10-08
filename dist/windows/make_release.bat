echo Building Nested for MS Windows

REM Build executable
cd ..\..\
python setup.py py2exe

REM Add locale
cd l10n\
python -B compile_mo.py
move mo ..\dist\windows\executable\l10n

REM Copy custom gtkrc
cd ..\dist\windows
copy /Y gtk\etc\gtk-2.0\gtkrc executable\etc\gtk-2.0\

REM Copy icons
xcopy /Y /I /E gtk\share\icons executable\share\icons

REM Install fonts configuration
xcopy /Y /I installer\dejavu-fonts\fontconfig executable\etc\fonts\conf.d

REM Add compiler dependencies
xcopy /Y /I installer\Microsoft.VC90.CRT executable\Microsoft.VC90.CRT

REM Call installer
cd installer
python create_installer.py
"C:\Program Files\NSIS\makensis.exe" nested_installer.nsi
move *.exe ..\

REM Clean Up
cd ..\
del installer\nested_installer.nsi
rd /S /Q ..\..\build

echo [DONE]
pause
