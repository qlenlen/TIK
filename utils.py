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


formats: [bytes, str, int] = (
    [b"PK", "zip"],
    [b"OPPOENCRYPT!", "ozip"],
    [b"7z", "7z"],
    [b"\x53\xef", "ext", 1080],
    [b"\x10\x20\xF5\xF2", "f2fs", 1024],
    [b"\x3a\xff\x26\xed", "sparse"],
    [b"\xe2\xe1\xf5\xe0", "erofs", 1024],
    [b"CrAU", "payload"],
    [b"AVB0", "vbmeta"],
    [b"\xd7\xb7\xab\x1e", "dtbo"],
    [b"\xd0\x0d\xfe\xed", "dtb"],
    [b"MZ", "exe"],
    [b".ELF", "elf"],
    [b"ANDROID!", "boot"],
    [b"VNDRBOOT", "vendor_boot"],
    [b"AVBf", "avb_foot"],
    [b"BZh", "bzip2"],
    [b"CHROMEOS", "chrome"],
    [b"\x1f\x8b", "gzip"],
    [b"\x1f\x9e", "gzip"],
    [b"\x02\x21\x4c\x18", "lz4_legacy"],
    [b"\x03\x21\x4c\x18", "lz4"],
    [b"\x04\x22\x4d\x18", "lz4"],
    [b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03", "zopfli"],
    [b"\xfd7zXZ", "xz"],
    [b"]\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff", "lzma"],
    [b"\x02!L\x18", "lz4_lg"],
    [b"\x89PNG", "png"],
    [b"LOGO!!!!", "logo"],
    [b"\x28\xb5\x2f\xfd", "zstd"],
)


def gettype(file) -> str:
    def compare(header: bytes, number: int = 0) -> int:
        with open(file, "rb") as f:
            f.seek(number)
            return f.read(len(header)) == header

    def is_super(fil) -> bool:
        with open(fil, "rb") as f:
            try:
                f.seek(4096, 0)
            except Exception as e:
                print(e)
                return False
            buf = bytearray(f.read(4))
        return buf == b"\x67\x44\x6c\x61"

    if is_super(file):
        return "super"

    for _f in formats:
        match len(_f):
            case 2:
                if compare(_f[0]):
                    return _f[1]
            case 3:
                if compare(_f[0], int(_f[2])):
                    return _f[1]
    return "Unknown"


def qc(file_) -> None:
    if not os.path.exists(file_):
        return
    with open(file_, "r+", encoding="utf-8", newline="\n") as f:
        data = f.readlines()
        new_data = sorted(set(data), key=data.index)
        if len(new_data) == len(data):
            print("No need to handle")
            return
        f.seek(0)
        f.truncate()
        f.writelines(new_data)
    del data, new_data


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
