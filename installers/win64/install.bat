@echo off

rem Run as administrator check, from "https://stackoverflow.com/questions/2997578/how-do-i-comment-on-the-windows-command-line
if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit /b)
rem I know, this is bad but it should work


echo Downloading python 3.9.1 ...
@echo on
curl "https://www.python.org/ftp/python/3.9.1/python-3.9.1-amd64.exe" -o "%temp%\python-3.9.1-amd64.exe"

@echo off
echo Download finished. Launching python 3.9.1 installer...
@echo on
%temp%\python-3.9.1-amd64.exe

@echo off
echo Downloading requirements...
@echo on
curl "https://raw.githubusercontent.com/Focshole/whatsapp-media-exif-fixer/main/src/requirements.txt" -o "%temp%\requirementsWA.txt"

@echo off
echo Download finished. Installing requirements...
rem Dropping privileges for requirements installation
@echo on
runas /trustlevel:0x20000 "%LOCALAPPDATA%\Programs\Python\Python39\python.exe -m pip install -r \"%temp%\requirementsWA.txt\""


@echo off
echo Done.
echo Downloading code...
@echo on
mkdir "%PROGRAMFILES%\WhatsappMediaFixer"
curl "https://raw.githubusercontent.com/Focshole/whatsapp-media-exif-fixer/main/src/ui.py" -o "%PROGRAMFILES%\WhatsappMediaFixer\ui.py"
curl "https://raw.githubusercontent.com/Focshole/whatsapp-media-exif-fixer/main/src/backend.py" -o "%PROGRAMFILES%\WhatsappMediaFixer\backend.py"
curl "https://raw.githubusercontent.com/Focshole/whatsapp-media-exif-fixer/main/src/whatsapp-media-fixer.py" -o "%PROGRAMFILES%\WhatsappMediaFixer\whatsapp-media-fixer.py"

@echo off
echo Creating shortcuts...
@echo on
powershell "$startmenu=[environment]::GetFolderPath('StartMenu');$s=(New-object -COM WScript.Shell).CreateShortcut(\"$startmenu\Whatsapp Media Fixer.lnk\");$s.TargetPath='%PROGRAMFILES%\WhatsappMediaFixer\whatsapp-media-fixer.py';$s.Save()"
powershell "$desktop=[environment]::GetFolderPath('Desktop');$s=(New-object -COM WScript.Shell).CreateShortcut(\"$desktop\Whatsapp Media Fixer.lnk\");$s.TargetPath='%PROGRAMFILES%\WhatsappMediaFixer\whatsapp-media-fixer.py';$s.Save()"
@echo off
echo Finished! You can close this window.
pause
