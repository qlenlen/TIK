import os
import re

from utils import MyPrinter

myprinter = MyPrinter()


import re


class Fstab:
    patterns = [
        re.compile(r"(avb=.*?,)"),
        re.compile(r"(,avb_keys=.*avbpubkey)"),
        re.compile(r"(avb,)"),
    ]

    enc_pattern = re.compile(
        r"(,fileencryption=.*?,keydirectory=.*?metadata_encryption)"
    )

    def __init__(self, fp: str):
        self.fp = fp
        self.__fstr = None

    def __enter__(self):
        self.file = open(self.fp, "w+", encoding="utf-8")
        self.__fstr = self.file.read()
        return self

    @property
    def fstr(self):
        with open(self.fp, "r", encoding="utf-8") as file:
            return file.read()

    @fstr.setter
    def fstr(self, value):
        self.__fstr = value

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def __write_file(self):
        self.file.write(self.fstr)

    def remove_avb(self):
        for pattern in self.patterns:
            self.fstr = pattern.sub("", self.fstr)
        self.__write_file()

    def remove_encryption(self):
        self.fstr = self.enc_pattern.sub("", self.fstr)
        self.__write_file()

    def fill_mount_point(self):
        def build_pattern(partition: str):
            return re.compile(rf"{partition}\t/{partition}.*first_stage_mount")

        def deal_with_matchlis(matchlis: list[str]):
            if not matchlis:
                print("Blank matchlis")
                return
            model = matchlis[0]
            mount_type = matchlis[0].split()[2]
            required_mount_types = {"erofs", "f2fs", "ext4"}
            for matchstr in matchlis:
                mount_type = set(matchstr.split()[2])
                required_mount_types -= mount_type

            if required_mount_types:
                for mount_type in required_mount_types:
                    matchlis.append(model.replace("erofs", mount_type))
            return matchlis

        for partition in [
            "system",
            "system_ext",
            "product",
            "vendor",
            "vendor_dlkm",
            "odm",
            "system_dlkm",
        ]:
            matchlis = build_pattern(partition).findall(self.fstr)
            origin_str = "\n".join(matchlis)
            ok_lis = deal_with_matchlis(matchlis)
            ok_str = "\n".join(ok_lis)
            self.fstr = self.fstr.replace(origin_str, ok_str)
        self.__write_file()


# 使用示例
with Fstab("fstab.qcom") as fstab:
    fstab.remove_avb()
    fstab.remove_encryption()
    fstab.fill_mount_point()


def slim_partition(): ...
