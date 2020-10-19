import os
import re
import sys
import time
from datetime import datetime, timedelta

import piexif

import signal

# To avoid data corruption, detect ^C and handle it properly
QUIT = False


def graceful_quit(sign, frame):
    global QUIT
    QUIT = True


def get_date(filename):
    date_str = filename.split('-')[1]
    return datetime.strptime(date_str, '%Y%m%d')


def get_datetime(filename):
    splitted = filename.split('-')  # IMG-20201018-WA0018.jpg
    date_str = splitted[1]
    seq_num = int(splitted[2][2:].split('.')[0])  # strip WA and .whatever
    if seq_num > 9999:
        print(
            f"Warning: time order won't be preserved for file {filename}, how did you took 9999+ photos or video in a "
            f"day?")
        seq_num = 9999
    d = datetime.strptime(date_str, '%Y%m%d')
    return d + timedelta(
        seconds=8 * seq_num)  # if 9999 photos have been taken, this sets the timing of each picture fairly
    # distributed during the day. It is not accurate but at least the sorting between wa files is coherent


def is_allowed_ext(fn):
    allowedExt = ['MP4', 'AVI', 'MKV', 'MOV', 'FLV', '3GP',
                  'JPG', 'JPEG', 'PNG']  # atm, only jpg should be supported
    return fn.split('.')[-1].upper() in allowedExt


def is_a_wa_file(fn):
    valid_file = r"^((IMG)|(VID))-[0-9]{8}-WA[0-9]{4}"  # eg IMG-20201018-WA0018 or VID-20201018-WA0018, i ignore
    # here the file extension
    return re.match(valid_file, fn.split('/')[-1])


def get_all_files(root_folder='./WhatsApp/Media/'):
    subfolders = ["WhatsApp Images/", "WhatsApp Video/"]
    all_folders = list()
    all_folders.append(root_folder)
    for path in subfolders:
        f = root_folder + path
        if os.path.isdir(f):
            all_folders.append(f)
        f = f + "Sent/"
        if os.path.isdir(f):
            all_folders.append(f)
    return [[folder_path, file_name] for folder_path in all_folders for file_name in os.listdir(folder_path) if
            is_a_wa_file(file_name) and is_allowed_ext(file_name)]


def same_modification_time(full_path, mod_time):
    return os.path.getmtime(full_path) == mod_time and os.path.getctime(full_path) == mod_time


def fix_modification_time(date, full_path):
    modTime = time.mktime(date.timetuple())
    if not same_modification_time(full_path, modTime):
        os.utime(full_path, (modTime, modTime))
        return True  # modified
    return False


def same_exif_creation_time(date, full_path):
    old_exif_data = piexif.load(full_path)
    if old_exif_data is not None and 'Exif' in old_exif_data:
        exif_dict = old_exif_data['Exif']
        if piexif.ExifIFD.DateTimeOriginal in exif_dict and \
                exif_dict[piexif.ExifIFD.DateTimeOriginal] == bytes(date, "UTF-8"):
            return True
    return False


def fix_exif(date, full_path):
    date = date.strftime("%Y:%m:%d %H:%M:%S")
    if not same_exif_creation_time(date, full_path):
        exif_dict = piexif.load(full_path)
        if 'Exif' not in exif_dict:
            # no exif, add them
            exif_dict['Exif'] = {piexif.ExifIFD.DateTimeOriginal: date}
        else:
            exif_data = exif_dict['Exif']
            if piexif.ExifIFD.DateTimeOriginal in exif_data and exif_data[piexif.ExifIFD.DateTimeOriginal][:8] == bytes(
                    date, "UTF-8")[:8]:
                return False  # the original file's exif are much probably more reliable than
                # the ones which are generated if the day matches
            else:
                exif_data[piexif.ExifIFD.DateTimeOriginal] = date  # simply edit that field
                exif_dict['Exif'] = exif_data  # update the exif data
        exif_bytes = piexif.dump(exif_dict)
        piexif.remove(
            full_path)  # If the program gets interrupted here, it may cause data loss and possible errors
        piexif.insert(exif_bytes, full_path)  # same there
        return True  # Modified
    return False


def fix_video(filename, full_path):
    date = get_datetime(filename)
    return fix_modification_time(date, full_path)


def fix_image(filename, full_path):
    date = get_datetime(filename)
    modif = fix_modification_time(date, full_path)
    modif2 = fix_exif(date, full_path)
    return modif or modif2


def fix_files():
    filenames = None
    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            if sys.argv[1][:-1]=="/":
                filenames = get_all_files(sys.argv[1])
            else:
                filenames = get_all_files(sys.argv[1]+"/")
        else:
            print(f"Usage: {sys.argv[0]} path_to_Whatsapp_media_directory")
            exit(1)
    else:
        filenames = get_all_files()
    num_files = len(filenames)
    print("Number of files: {}".format(num_files))

    for i, filename in enumerate(filenames):
        full_path = "".join(filename)
        filename = filename[1]
        modified = False
        initial_size = os.path.getsize(full_path)
        if filename.endswith('jpg') or filename.endswith('jpeg'):
            print("Reading image", filename, "...")
            modified = fix_image(filename, full_path)
        elif filename.endswith('mp4') or filename.endswith('3gp') or filename.endswith('mov'):
            print("Reading video", filename, "...")
            modified = fix_video(filename, full_path)
        else:
            print("WARNING: Skipping unknown file", filename)
        num_digits = len(str(num_files))
        final_size = os.path.getsize(full_path)
        if final_size - initial_size < 0 or final_size - initial_size > 52:
            print(
                f"ERROR: file {full_path} got probably corrupted! Initial size was {initial_size / 1024} Kb,",
                f"final size was {final_size / 1024} Kb.",
                f"Change in size: {final_size - initial_size} bytes",
                f"\nTry to open it to check if it is fine or not, especially the EXIF metadata.",
                f"\nIf it is fine, simply rerun: \n{sys.argv[0]} {sys.argv[1] if len(sys.argv) > 1 else ''}")
            exit(-1)
        if modified:
            print("{num:{width}}/{max} Modified {filename}".format(num=i + 1, width=num_digits,
                                                                   max=num_files, filename=full_path))
        else:
            print("{num:{width}}/{max} Skipped {filename}".format(num=i + 1, width=num_digits,
                                                                  max=num_files, filename=filename))
        if QUIT:
            print("Exiting gracefully...")
            exit(2)
    print('\nDone!')


if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_quit)
    fix_files()
