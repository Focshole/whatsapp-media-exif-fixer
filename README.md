# whatsapp-media-exif-fixer
Have you ever found your WhatsApp images and videos messed up with the timeline? 


This tool allows you to fix the last modified time (both images and videos), created time and the EXIF time acquisition data (images only) in such a way that it fixes media files' date and time in a best effort approach.<br>
It infers the media creation timeline from their names (eg. IMG-20201019-WA0001.jpg had been taken before than IMG-20201019-WA0002.jpg and both had been received/sent on 19th October 2020)<br>

## Changelog
 - Added a UI in wxPython, it works on Linux, haven't fully tested yet on Windows.
 - Provided a Windows batch installer.

## How to install
### Windows

If you have no experience with python, I have provided an "installer", a batch file that will install python and the required libraries, and provide a shortcut in the Start Menu and Desktop too. You can find it [here](https://github.com/Focshole/whatsapp-media-exif-fixer/blob/main/installers/win64/install.bat). Requires Windows 10 ([it has curl](https://devblogs.microsoft.com/commandline/windows10v1803#tar-and-curl-with-windows-10)) or newer/better.

### Linux
 1. Download and extract the repository
 2. Create a virtual environment or ```pip3.9 install -r src/requirements.txt```<br>

## How to use
 1. Create a backup copy of your media folder. Don't run it directly on microSDs.<br>
 2. Run the ```whatsapp-media-fixer.py``` script
    - If you have used the installer, double click on the shortcut. 
    - On Linux/if you didn't use the installer ```python3.9 src/whatsapp-media-fixer.py```

Be careful, this is I/O intensive, I would recommend you to run it over an SSD or an HDD. Use this tool at your own risk.
Tested on Linux only, still testing it on Windows, may work on Mac too but I haven't tested it.
