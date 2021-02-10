import os
import re
import time
from datetime import datetime, timedelta

import piexif

import signal

QUIT = False


def graceful_quit(sign, frame):
    global QUIT
    QUIT = True


class FixExif:

    def __init__(self, ui, folders=None):
        self.folders = folders
        self.Ui = ui

    def set_folders(self, folders):
        self.folders = folders

    @staticmethod
    def get_date(filename):
        date_str = filename.split('-')[1]
        return datetime.strptime(date_str, '%Y%m%d')

    def get_datetime(self, filename):
        splitted = filename.split('-')  # IMG-20201018-WA0018.jpg
        date_str = splitted[1]
        seq_num = int(splitted[2][2:].split('.')[0])  # strip WA and .whatever
        if seq_num > 9999:
            self.Ui.warn(
                f"Warning: time order won't be preserved for file {filename}, how did you took 9999+ photos or video "
                f"in a day?")
            seq_num = 9999
        d = datetime.strptime(date_str, '%Y%m%d')
        return d + timedelta(
            seconds=8 * seq_num)  # if 9999 photos have been taken, this sets the timing of each picture fairly
        # distributed during the day. It is not accurate but at least the sorting between wa files should be coherent
        # 8 = floor(24*60*60/9999) 

    @staticmethod
    def is_allowed_ext(fn):
        allowedExt = ['MP4', 'AVI', 'MKV', 'MOV', 'FLV', '3GP',
                      'JPG', 'JPEG', 'PNG']  # atm, only jpg should be supported
        return fn.split('.')[-1].upper() in allowedExt

    @staticmethod
    def is_a_wa_file(fn):
        valid_file = r"^((IMG)|(VID))-[0-9]{8}-WA[0-9]{4}"  # eg IMG-20201018-WA0018 or VID-20201018-WA0018, i ignore
        # here the file extension
        return re.match(valid_file, fn.split('/')[-1])

    def get_all_files(self, folders):
        return [[folder_path, file_name] for folder_path in folders for file_name in os.listdir(folder_path) if
                self.is_a_wa_file(file_name) and self.is_allowed_ext(file_name)]

    @staticmethod
    def same_modification_time(full_path, mod_time):
        return os.path.getmtime(full_path) == mod_time and os.path.getctime(full_path) == mod_time

    def fix_modification_time(self, date, full_path):
        modTime = time.mktime(date.timetuple())
        if not self.same_modification_time(full_path, modTime):
            os.utime(full_path, (modTime, modTime))
            return True  # modified
        return False

    @staticmethod
    def same_exif_creation_time(date, full_path):
        old_exif_data = piexif.load(full_path)
        if old_exif_data is not None and 'Exif' in old_exif_data:
            exif_dict = old_exif_data['Exif']
            if piexif.ExifIFD.DateTimeOriginal in exif_dict and \
                    exif_dict[piexif.ExifIFD.DateTimeOriginal] == bytes(date, "UTF-8"):
                return True
        return False

    def fix_exif(self, date, full_path):
        date = date.strftime("%Y:%m:%d %H:%M:%S")
        if not self.same_exif_creation_time(date, full_path):
            exif_dict = piexif.load(full_path)
            if 'Exif' not in exif_dict:
                # no exif, add them
                exif_dict['Exif'] = {piexif.ExifIFD.DateTimeOriginal: date}
            else:
                exif_data = exif_dict['Exif']
                if piexif.ExifIFD.DateTimeOriginal in exif_data and exif_data[piexif.ExifIFD.DateTimeOriginal][
                                                                    :8] == bytes(
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

    def fix_video(self, filename, full_path):
        date = self.get_datetime(filename)
        return self.fix_modification_time(date, full_path)

    def fix_image(self, filename, full_path):
        date = self.get_datetime(filename)
        modif = self.fix_modification_time(date,
                                           full_path)
        # TODO: check which parameter won't get modified (running twice shouldn't touch the same files again)
        modif2 = self.fix_exif(date, full_path)
        return modif or modif2

    def fix_files(self):
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, graceful_quit)  # Avoid possible data corruption by interrupting during execution

        filenames = self.get_all_files(self.folders)
        num_files = len(filenames)
        for i, filename in enumerate(filenames):
            full_path = os.path.join(filename[0], filename[1])
            filename = filename[1]
            initial_size = os.path.getsize(full_path)
            if filename.endswith('jpg') or filename.endswith('jpeg'):
                self.Ui.print(f"Reading image {filename}...")
                modified = self.fix_image(filename, full_path)
            else:
                self.Ui.print(f"Reading video {filename}...")
                modified = self.fix_video(filename, full_path)
            num_digits = len(str(num_files))
            final_size = os.path.getsize(full_path)
            diff_size = final_size - initial_size
            if diff_size < 0 or diff_size > 60:
                self.Ui.error(
                    f"ERROR: file {full_path} got possibly corrupted! Initial size was {initial_size / 1024} Kb,",
                    f"final size was {final_size / 1024} Kb.",
                    f"Change in size: {diff_size} bytes",
                    f"\nTry to open it to check if it is fine or not, especially the EXIF metadata.")
            if modified:
                self.Ui.print("{num:{width}}/{max} Modified {filename}".format(num=i + 1, width=num_digits,
                                                                               max=num_files, filename=full_path))
            else:
                self.Ui.print("{num:{width}}/{max} Skipped {filename}".format(num=i + 1, width=num_digits,
                                                                              max=num_files, filename=filename))
            if QUIT:
                self.Ui.print("Exiting gracefully...")
                exit(2)
        self.Ui.print("Finished!")
        signal.signal(signal.SIGINT, original_sigint_handler)  # reset the signal handler
