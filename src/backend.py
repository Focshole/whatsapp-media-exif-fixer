import os
import re
import time
from datetime import datetime, timedelta
import platform
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
    def same_creation_date(full_path, creat_time):
        # https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python#237084
        if platform.system() == 'Windows':
            return datetime.fromtimestamp(os.path.getctime(full_path)).date() == creat_time.date()
        else:
            stat = os.stat(full_path)
            try:
                return datetime.fromtimestamp(stat.st_birthtime).date() == creat_time.date()
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return datetime.fromtimestamp(stat.st_mtime).date() == creat_time.date()

    @staticmethod
    def same_modification_date(full_path, mod_time):
        return datetime.fromtimestamp(os.path.getmtime(full_path)).date() == mod_time.date()

    @staticmethod
    def set_last_access_modification_datetime(full_path, mod_time):
            os.utime(full_path, (mod_time, mod_time))

    def fix_last_access_modification_datetime(self, m_date_time, full_path):
        if not (self.same_modification_date(full_path, m_date_time)): # and self.same_creation_date(full_path, m_date_time)):
            self.set_last_access_modification_datetime(full_path,time.mktime(m_date_time.timetuple()))
            return True  # modified
        return False

    @staticmethod
    def same_exif_acquisition_date(date, full_path):
        # the original file's exif are much probably more reliable than
        # the ones which are generated if the date matches
        old_exif_data = piexif.load(full_path)
        if old_exif_data is not None and 'Exif' in old_exif_data:
            exif_dict = old_exif_data['Exif']
            if piexif.ExifIFD.DateTimeOriginal in exif_dict:
                exif_date = datetime.strptime(exif_dict[piexif.ExifIFD.DateTimeOriginal].decode(),"%Y:%m:%d %H:%M:%S")
                if exif_date.date() == date.date():
                    return True
        return False

    def fix_exif(self, acquisition_time, full_path):

        if not self.same_exif_acquisition_date(acquisition_time, full_path):
            exif_dict = piexif.load(full_path)
            if 'Exif' in exif_dict:
                exif_data = exif_dict['Exif']
                if piexif.ExifIFD.DateTimeOriginal in exif_data:
                    exif_time = exif_dict[piexif.ExifIFD.DateTimeOriginal]
                    if exif_time.date() == acquisition_time.date():
                        return False  
            exif_data[piexif.ExifIFD.DateTimeOriginal] = acquisition_time.strftime("%Y:%m:%d %H:%M:%S")  # simply edit that field
            exif_dict['Exif'] = exif_data  # update the exif data
            exif_bytes = piexif.dump(exif_dict)
            piexif.remove(full_path)  # If the program gets interrupted here, 
                                      #it may cause exif data loss and possible errors
            piexif.insert(exif_bytes, full_path)  # same there
            return True  # Modified
        return False

    def fix_video(self, filename, full_path):
        date = self.get_datetime(filename)
        return self.fix_last_access_modification_datetime(date, full_path)

    def fix_image(self, filename, full_path):
        date = self.get_datetime(filename)
        modif = self.fix_last_access_modification_datetime(date,
                                                        full_path)
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
                # self.Ui.print(f"Reading image {filename}...")
                modified = self.fix_image(filename, full_path)
            else:
                # self.Ui.print(f"Reading video {filename}...")
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
