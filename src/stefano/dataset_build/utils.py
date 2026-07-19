import random
import time
import exifread
from charset_normalizer import from_bytes
from datetime import datetime
from dateutil import parser


def detect_encoding(path):
    with open(path, "rb") as f:
        data = f.read()
    match = from_bytes(data).best()
    return match.encoding if match else None


def parse_timestamp(string_date:str) -> int:

    """ Simple function to process dates in various formats """

    try:
        return int(parser.parse(string_date).timestamp())
    except (ValueError, TypeError, OverflowError):
        return 0


def convert_timestamp(int_date:int, f_string:str) -> str:
    try:
        return datetime.fromtimestamp(int_date).strftime(f_string)
    except (OSError, OverflowError, ValueError, TypeError):
        return "00/00/00 00:00:00"


def load_translator(path, encoding="utf-8") -> {}:

    """ A useful function that builds a dictionary from a language configuration file """

    dictionary = {}

    with open(path, "r", encoding=encoding) as file:
        for line in file:
            i = line.index("=")
            key = line[:i]
            value = line[i + 1:]
            dictionary[key] = value.replace("\n", "")

    return dictionary


def bool_to_str(boolean:bool) -> str:
    if boolean:
        return "true"
    return "false"


def random_delay(milliseconds:int, delta:int):
    delta = random.randint(0, delta)  # noqa: F821
    time.sleep((milliseconds + delta) / 1000)


class ExifReader:

    """ A class to read EXIF data from a picture """

    def __init__(self, picture_path, stop_tag="", details=False):
        with open(picture_path, "rb") as file:
            if stop_tag == "":
                self.exif_tags = exifread.process_file(file, details=details)
            else:
                self.exif_tags = exifread.process_file(file, stop_tag=stop_tag, details=details)

    def get(self, info:str):
        match info.upper():
            case "ISO":
                try:
                    return str(self.exif_tags["EXIF ISOSpeedRatings"])
                except KeyError:
                    return "N/A"
            case "FSTOP":
                try:
                    return str(self.exif_tags["EXIF FNumber"])
                except KeyError:
                    return "N/A"
            case "SHUTTER":
                try:
                    return str(self.exif_tags["EXIF ExposureTime"])
                except KeyError:
                    return "N/A"
            case "FLASH":
                try:
                    flash = str(self.exif_tags["EXIF Flash"])
                    if flash.upper().find("NOT") != -1:
                        return "No"
                    return "Yes"
                except KeyError:
                    return "N/A"
            case "METERING":
                try:
                    return str(self.exif_tags["EXIF MeteringMode"])
                except KeyError:
                    return "N/A"
            case "EXP MODE":
                try:
                    return str(self.exif_tags["EXIF ExposureProgram"])
                except KeyError:
                    return "N/A"
            case "EXP COMP":
                try:
                    return str(self.exif_tags["EXIF ExposureBiasValue"])
                except KeyError:
                    return "N/A"
            case "CAMERA":
                try:
                    brand = str(self.exif_tags["Image Make"]).upper().strip()
                    model = str(self.exif_tags["Image Model"]).upper().strip()
                except KeyError:
                    brand = "N/A"
                    model = "N/A"
                if brand == "": brand = "N/A"
                if model == "": model = "N/A"
                return brand, model
            case "CREATION DATE":
                try:
                    time = str(self.exif_tags["EXIF DateTimeOriginal"])
                    return parse_timestamp(time)
                except KeyError:
                    return 0
            case "FOCAL LENGTH":
                try:
                    return str(self.exif_tags["EXIF FocalLength"])
                except KeyError:
                    return "N/A"
        return None