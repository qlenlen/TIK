import os
import shutil
import subprocess
import time
from argparse import Namespace
from typing import Literal

from src.image.ImageUnpacker import ImageUnpacker

import tikpath
from src.util.TypeDetector import TypeDetector

from src.util.log import print_yellow
from src.util.utils import MyPrinter

myprinter = MyPrinter()


def calc_time(func):
    def wrapper(*args, **kwargs):
        st = time.time()
        func(*args, **kwargs)
        et = time.time()
        print_yellow(f"<{func.__name__}>耗时: {et - st:.4f}(s)")

    return wrapper


class SizeCalculator:
    def __init__(self, content_path: str):
        self.content_path = content_path

    def calculate_dir_size(self) -> int:
        total_size = 0
        for root, _, files in os.walk(self.content_path):
            for name in files:
                file_path = os.path.join(root, name)
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    def resize(self):
        return self.calculate_dir_size() * 1.1


class ImageSizeCalculator:
    def __init__(self, dir_path: str):
        self.dir_path = dir_path
        self.partition = os.path.basename(dir_path)

    def calculate_size(self, _type: Literal["ext4", "f2fs"]) -> int:
        """Calculate the size of the image, unit: Byte"""
        match _type:
            case "ext4":
                return self.calculate_size_ext4()
            case "f2fs":
                return self.calculate_size_f2fs()

    def calculate_size_ext4(self) -> int:
        """计算ext4镜像所需大小，单位为字节 Byte"""
        dir_size = SizeCalculator(self.dir_path).calculate_dir_size()
        match self.partition:
            case "system":
                return dir_size + 500 * 1024 * 1024
            case "system_ext":
                return dir_size + 120 * 1024 * 1024
            case "product":
                return dir_size + 50 * 1024 * 1024
            case "vendor":
                return dir_size + 100 * 1024 * 1024
            case _:
                return SizeCalculator(self.dir_path).resize()

    def calculate_size_f2fs(self) -> int:
        """计算f2fs镜像所需大小，单位为字节 Byte"""
        dir_size = SizeCalculator(self.dir_path).calculate_dir_size()
        min_size = 68 * 1024 * 1024
        if dir_size < min_size:
            return min_size
        match self.partition:
            case "system":
                return dir_size + 550 * 1024 * 1024
            case "system_ext":
                return dir_size + 120 * 1024 * 1024
            case "product":
                return dir_size + 60 * 1024 * 1024
            case "vendor":
                return dir_size + 110 * 1024 * 1024
            case _:
                return SizeCalculator(self.dir_path).resize()





class Kernel:
    def __init__(self, kernel_path: str):
        self.kernel_path = kernel_path

    def read_version(self):
        return os.system('strings resource/kernel/kernel | grep -i "Linux version"')

    def copy_to(self, target_path: str):
        shutil.copy(self.kernel_path, target_path)


class BootImg:
    def __init__(self, img_path: str):
        self.backup_dir = os.getcwd()
        self.img_path = img_path

    def __enter__(self):
        os.chdir(os.path.dirname(self.img_path))
        myprinter.print_red(f"work dir -> {os.getcwd()}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.backup_dir)
        myprinter.print_red(f"work dir -> {os.getcwd()}")

    def unpack(self):
        os.system(f"magiskboot unpack {self.img_path}")

    def repack(self):
        os.system(f"magiskboot repack {self.img_path}")


if __name__ == "__main__":
    tikpath.init()
    tikpath.set_project("TEST")
    ImageUnpacker("../../TEST/AP/vendor_boot.img").unpack_vendor_boot()
