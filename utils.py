import json
import os
import platform as plat
import sys
from dataclasses import dataclass

from rich.console import Console
from rich.text import Text

from lpunpack import SparseImage

try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass
elocal = os.getcwd()
platform = plat.machine()
ostype = plat.system()
binner = elocal + os.sep + "bin"
ebinner = binner + os.sep + ostype + os.sep + platform + os.sep


class MyPrinter:
    def __init__(self):
        self.console = Console(highlighter=None)

    def print_white(self, text: str):
        self.console.print(text, style="white")

    def print_yellow(self, text: str):
        self.console.print(text, style="yellow")

    def print_red(self, text: str):
        self.console.print(text, style="red")

    def print_green(self, text: str):
        self.console.print(text, style="green")

    def print_cyan(self, text: str):
        self.console.print(text, style="cyan")

    def print_blue(self, text: str):
        self.console.print(text, style="blue")


def yellow(text, needN=True):
    return Text(text, style="yellow")
    # return f"\033[33m{text}\033[0m" + ("\n" if needN else "")


def green(text, needN=True):
    return f"\033[32m{text}\033[0m" + ("\n" if needN else "")


def red(text, needN=True):
    return f"\033[31m{text}\033[0m" + ("\n" if needN else "")


def blue(text, needN=True):
    return f"\033[36m{text}\033[0m" + ("\n" if needN else "")


class JsonEdit:
    def __init__(self, j_f):
        self.file = j_f

    def read(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file, "r+", encoding="utf-8") as pf:
            try:
                return json.loads(pf.read())
            except (Exception, BaseException):
                return {}

    def write(self, data):
        with open(self.file, "w+", encoding="utf-8") as pf:
            json.dump(data, pf, indent=4)

    def edit(self, name, value):
        data = self.read()
        data[name] = value
        self.write(data)


def versize(size):
    size_gb = size / (1024 * 1024 * 1024)
    closest_half_gb = (int(size_gb * 2) + 1) / 2.0
    return int(closest_half_gb * 1024 * 1024 * 1024)


@dataclass
class SetUtils:
    supername = "super"
    brcom = "1"
    banner = "1"
    pack_e2 = "1"
    pack_sparse = "0"
    autoslotsuffixing = ""
    fullsuper = "-F"
    BLOCKSIZE = "4096"
    SBLOCKSIZE = "4096"
    metadatasize = "65536"
    super_group = "qti_dynamic_partitions"
    erofslim = "lz4hc,8"
    utcstamp = "1722470400"
    diysize = ""
    diyimgtype = "1"
    online = "true"
    erofs_old_kernel = "0"
    context = "false"
    version = "5.121"

    def load_set(self):
        with open(self.path, "r") as ss:
            data = json.load(ss)
            [setattr(self, v, data[v]) for v in data]


@dataclass
class TypeFlag:
    flag: bytes
    typeStr: str
    offset: int = 0


class TypeDetector:
    """
    文件类型获取
    """

    path: str = ""

    formats: tuple[TypeFlag] = (
        TypeFlag(b"PK", "zip"),
        TypeFlag(b"OPPOENCRYPT!", "ozip"),
        TypeFlag(b"7z", "7z"),
        TypeFlag(b"\x53\xef", "ext", 1080),
        TypeFlag(b"\x10\x20\xF5\xF2", "f2fs", 1024),
        TypeFlag(b"\x3a\xff\x26\xed", "sparse"),
        TypeFlag(b"\xe2\xe1\xf5\xe0", "erofs", 1024),
        TypeFlag(b"CrAU", "payload"),
        TypeFlag(b"AVB0", "vbmeta"),
        TypeFlag(b"\xd7\xb7\xab\x1e", "dtbo"),
        TypeFlag(b"\xd0\x0d\xfe\xed", "dtb"),
        TypeFlag(b"MZ", "exe"),
        TypeFlag(b".ELF", "elf"),
        TypeFlag(b"ANDROID!", "boot"),
        TypeFlag(b"VNDRBOOT", "vendor_boot"),
        TypeFlag(b"AVBf", "avb_foot"),
        TypeFlag(b"BZh", "bzip2"),
        TypeFlag(b"CHROMEOS", "chrome"),
        TypeFlag(b"\x1f\x8b", "gzip"),
        TypeFlag(b"\x1f\x9e", "gzip"),
        TypeFlag(b"\x02\x21\x4c\x18", "lz4_legacy"),
        TypeFlag(b"\x03\x21\x4c\x18", "lz4"),
        TypeFlag(b"\x04\x22\x4d\x18", "lz4"),
        TypeFlag(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03", "zopfli"),
        TypeFlag(b"\xfd7zXZ", "xz"),
        TypeFlag(b"]\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff", "lzma"),
        TypeFlag(b"\x02!L\x18", "lz4_lg"),
        TypeFlag(b"\x89PNG", "png"),
        TypeFlag(b"LOGO!!!!", "logo"),
        TypeFlag(b"\x28\xb5\x2f\xfd", "zstd"),
    )

    def __init__(self, path: str):
        self.path = path

    def compare(self, type_flag: TypeFlag) -> bool:
        with open(self.path, "rb") as f:
            f.seek(type_flag.offset)
            return f.read(len(type_flag.flag)) == type_flag.flag

    @staticmethod
    def inner_compare(fileObj, type_flag: TypeFlag) -> bool:
        """
        优化速度，不重复开启文件
        """
        fileObj.seek(type_flag.offset)
        return fileObj.read(len(type_flag.flag)) == type_flag.flag

    def get_type(self) -> str:
        with open(self.path, "rb") as file:
            for f in self.formats:
                if self.inner_compare(file, f):
                    return f.typeStr
            return "Unknown"


def remove_duplicate_lines(file_path: str) -> None:
    if not os.path.exists(file_path):
        return
    with open(file_path, "r+", encoding="utf-8", newline="\n") as f:
        data = f.readlines()
        new_data = list(dict.fromkeys(data))  # 去重并保持顺序
        if len(new_data) == len(data):
            print("No need to handle")
            return
        f.seek(0)
        f.truncate()
        f.writelines(new_data)


def simg2img(path):
    with open(path, "rb") as fd:
        if SparseImage(fd).check():
            print("Sparse image detected.")
            print("Process conversion to non sparse image...")
            unsparse_file = SparseImage(fd).unsparse()
            print("Result:[ok]")
        else:
            print(f"{path} not Sparse.Skip!")
    try:
        if os.path.exists(unsparse_file):
            os.remove(path)
            os.rename(unsparse_file, path)
    except Exception as e:
        print(e)
