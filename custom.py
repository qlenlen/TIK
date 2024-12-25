import os
import re

from utils import MyPrinter

myprinter = MyPrinter()


def dis_avb(fstab: str):
    myprinter.print_yellow(f"正在处理: {fstab}")
    if not os.path.exists(fstab):
        return
    with open(fstab, "r") as sf:
        details = sf.read()
    details = re.sub("avb=vbmeta_system,", "", details)
    details = re.sub("avb,", "", details)
    details = re.sub(",avb_keys=.*avbpubkey", "", details)
    with open(fstab, "w") as tf:
        tf.write(details)


def dis_data_encryption(fstab): ...


def slim_partition(): ...
