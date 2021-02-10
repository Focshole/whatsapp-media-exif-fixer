# whatsapp-media-exif-fixer
Have you ever found your WhatsApp images and videos messed up with the timeline? 


This tool allows you to fix the last modified time (both images and videos), created time and the EXIF time acquisition data (images only) in such a way that it fixes media files' date and time in a best effort approach.<br>
It infers the media creation timeline from their names (eg. IMG-20201019-WA0001.jpg had been taken before than IMG-20201019-WA0002.jpg and both had been received/sent on 19th October 2020)<br>

## Changelog
 - Added a UI in wxPython, it works on Linux, haven't tested yet on Windows, I'll probably test it and fix it very soon, by also providing an installer.

## How to use

 1. Create a backup copy of your media folder. Don't run it directly on microSDs.<br>
 2. If required, ```pip3.9 install -r requirements.txt```<br>
 3. Run ```python3.9 whatsapp-media-fixer.py```

Be careful, this is I/O intensive, I would recommend you to run it over an SSD or an HDD, not on microSD. Use this tool at your own risk.

Tested on Linux only, may work on Mac too but I haven't tested it. I'll try to make it Windows compatible.
