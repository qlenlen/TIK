from __future__ import print_function

import json
import os
import platform as plat
import sys
from threading import Thread

from rich.console import Console
from rich.table import Table

from api import cls
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


def yellow(text, needN=True):
    return f"\033[33m{text}\033[0m\n" if needN else f"\033[33m{text}\033[0m"


def green(text, needN=True):
    return f"\033[32m{text}\033[0m\n" if needN else f"\033[32m{text}\033[0m"


def red(text, needN=True):
    return f"\033[31m{text}\033[0m\n" if needN else f"\033[31m{text}\033[0m"


def blue(text, needN=True):
    return f"\033[36m{text}\033[0m\n" if needN else f"\033[36m{text}\033[0m"


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


class SetUtils:
    def __init__(self, path):
        self.path = path
        self.supername = "super"
        self.brcom = "1"
        self.banner = "1"
        self.pack_e2 = "1"
        self.pack_sparse = "0"
        self.autoslotsuffixing = ""
        self.fullsuper = "-F"
        self.BLOCKSIZE = "4096"
        self.SBLOCKSIZE = "4096"
        self.metadatasize = "65536"
        self.super_group = "qti_dynamic_partitions"
        self.erofslim = "lz4hc,8"
        self.utcstamp = "1722470400"
        self.diysize = ""
        self.diyimgtype = "1"
        self.online = "true"
        self.erofs_old_kernel = "0"
        self.context = "false"
        self.version = "5.121"

    def load_set(self):
        with open(self.path, "r") as ss:
            data = json.load(ss)
            [setattr(self, v, data[v]) for v in data]

    def change(self, name, value):
        with open(self.path, "r") as ss:
            data = json.load(ss)
        with open(self.path, "w", encoding="utf-8") as ss:
            data[name] = value
            json.dump(data, ss, ensure_ascii=False, indent=4)
        self.load_set()


def error(exception_type, exception, traceback):
    cls()
    table = Table()
    table.add_column(f"[red]ERROR:{exception_type.__name__}[/]", justify="center")
    table.add_row(f"[yellow]Describe:{exception}")
    table.add_row(
        f'[yellow]Lines:{exception.__traceback__.tb_lineno}\tModule:{exception.__traceback__.tb_frame.f_globals["__name__"]}'
    )
    table.add_section()
    table.add_row(
        f"[blue]Platform:[purple]{plat.machine()}\t[blue]System:[purple]{plat.uname().system} {plat.uname().release}"
    )
    table.add_section()
    table.add_row(f"[green]Report:https://github.com/ColdWindScholar/TIK/issues")
    Console().print(table)
    input()
    sys.exit(1)


formats = (
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
    if not os.path.exists(file):
        return "fne"

    def compare(header: bytes, number: int = 0) -> int:
        with open(file, "rb") as f:
            f.seek(number)
            return f.read(len(header)) == header

    def is_super(fil) -> bytes | bool:
        with open(fil, "rb") as file_:
            buf = bytearray(file_.read(4))
            if len(buf) < 4:
                return False
            file_.seek(0, 0)

            while buf[0] == 0x00:
                buf = bytearray(file_.read(1))
            try:
                file_.seek(-1, 1)
            except:
                return False
            buf += bytearray(file_.read(4))
        return buf[1:] == b"\x67\x44\x6c\x61"

    def is_super2(fil) -> bytes | bool:
        with open(fil, "rb") as file_:
            try:
                file_.seek(4096, 0)
            except:
                return False
            buf = bytearray(file_.read(4))
        return buf == b"\x67\x44\x6c\x61"

    try:
        if is_super(file) or is_super2(file):
            return "super"
    except IndexError:
        pass
    for f_ in formats:
        if len(f_) == 2:
            if compare(f_[0]):
                return f_[1]
        elif len(f_) == 3:
            if compare(f_[0], f_[2]):
                return f_[1]
    return "unknow"


def dynamic_list_reader(path):
    data = {}
    with open(path, "r", encoding="utf-8") as l_f:
        for p in l_f.readlines():
            if p[:1] == "#":
                continue
            tmp = p.strip().split()
            if tmp[0] == "remove_all_groups":
                data.clear()
            elif tmp[0] == "add_group":
                data[tmp[1]] = {}
                data[tmp[1]]["size"] = tmp[2]
                data[tmp[1]]["parts"] = []
            elif tmp[0] == "add":
                data[tmp[2]]["parts"].append(tmp[1])
            else:
                print(f"Skip {tmp}")
    return data


def generate_dynamic_list(dbfz, size, set_, lb, work):
    data = [
        "# Remove all existing dynamic partitions and groups before applying full OTA",
        "remove_all_groups",
    ]
    with open(
        work + "dynamic_partitions_op_list", "w", encoding="utf-8", newline="\n"
    ) as d_list:
        if set_ == 1:
            data.append(f"# Add group {dbfz} with maximum size {size}")
            data.append(f"add_group {dbfz} {size}")
        elif set_ in [2, 3]:
            data.append(f"# Add group {dbfz}_a with maximum size {size}")
            data.append(f"add_group {dbfz}_a {size}")
            data.append(f"# Add group {dbfz}_b with maximum size {size}")
            data.append(f"add_group {dbfz}_b {size}")
        for part in lb:
            if set_ == 1:
                data.append(f"# Add partition {part} to group {dbfz}")
                data.append(f"add {part} {dbfz}")
            elif set_ in [2, 3]:
                data.append(f"# Add partition {part}_a to group {dbfz}_a")
                data.append(f"add {part}_a {dbfz}_a")
                data.append(f"# Add partition {part}_b to group {dbfz}_b")
                data.append(f"add {part}_b {dbfz}_b")
        for part in lb:
            if set_ == 1:
                data.append(
                    f'# Grow partition {part} from 0 to {os.path.getsize(work + part + ".img")}'
                )
                data.append(f'resize {part} {os.path.getsize(work + part + ".img")}')
            elif set_ in [2, 3]:
                data.append(
                    f'# Grow partition {part}_a from 0 to {os.path.getsize(work + part + ".img")}'
                )
                data.append(f'resize {part}_a {os.path.getsize(work + part + ".img")}')
        d_list.writelines([key + "\n" for key in data])
        data.clear()


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


def cz(func, *args):
    Thread(target=func, args=args, daemon=True).start()


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


# ----CLASSES


class vbpatch:
    def __init__(self, file_):
        self.file = file_

    def checkmagic(self):
        if os.access(self.file, os.F_OK):
            magic = b"AVB0"
            with open(self.file, "rb") as f:
                buf = f.read(4)
                return magic == buf
        else:
            print("File dose not exist!")

    def readflag(self):
        if not self.checkmagic():
            return False
        if os.access(self.file, os.F_OK):
            with open(self.file, "rb") as f:
                f.seek(123, 0)
                flag = f.read(1)
                if flag == b"\x00":
                    return 0  # Verify boot and dm-verity is on
                elif flag == b"\x01":
                    return 1  # Verify boot but dm-verity is off
                elif flag == b"\x02":
                    return 2  # All verity is off
                else:
                    return flag
        else:
            print("File does not exist!")

    def patchvb(self, flag):
        if not self.checkmagic():
            return False
        if os.access(self.file, os.F_OK):
            with open(self.file, "rb+") as f:
                f.seek(123, 0)
                f.write(flag)
            print("Done!")
        else:
            print("File not Found")

    def restore(self):
        self.patchvb(b"\x00")

    def disdm(self):
        self.patchvb(b"\x01")

    def disavb(self):
        self.patchvb(b"\x02")
