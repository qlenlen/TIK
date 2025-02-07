import os
import platform as plat
import sys
from dataclasses import dataclass

import json5
from rich.console import Console

from src.lib.lpunpack import SparseImage

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


class JsonUtil:
    def __init__(self, json_file: str):
        self.json_file = json_file

    @staticmethod
    def read(json_file: str) -> dict:
        """从json文件中读取数据"""
        with open(json_file, "r", encoding="utf-8") as file:
            return json5.load(file)

    def update(self, k, v):
        """更新"""
        data = JsonUtil.read(self.json_file)
        data.update({k: v})
        with open(self.json_file, "w", encoding="utf-8") as file:
            json5.dump(data, file, ensure_ascii=False, indent=4)

    def write(self, data: dict):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json5.dump(data, file, ensure_ascii=False, indent=4)


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
