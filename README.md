# whatsapp-media-exif-fixer
Have you ever found your WhatsApp images and videos messed up with the timeline? 


This tool allows you to fix the EXIF time acquisition data (images only), last modified time and created time in such a way that it fixes media files' date and time in a best effort approach.<br>
It infers the media creation timeline from their names (eg. IMG-20201019-WA0001.jpg had been taken before than IMG-20201019-WA0002.jpg and both had been received/sent on 19th October 2020)<br>


## How to use

 1. Create a backup copy of your media folder.<br>
 2. If required, ```pip3.8 install -r requirements.txt```<br>
 3. Run ```python3.8 fix_exif.py your_whatsapp_media_folder```

Be careful, this is disk intensive, I would recommend you to run it over an SSD or an HDD, not on microSD. Use this tool at your own risk.

When called it looks for `./WhatsApp/Media/` folder (or `your_whatsapp_media_folder` if specified) for any WhatsApp image, then looks for the `WhatsApp Images` and `WhatsApp Video` subfolders if they exist, then in `Sent` subfolders. 

Tested on Linux only, may work on Mac too but I haven't tested it.
