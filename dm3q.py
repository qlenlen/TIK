"""
Samsung S23 Ultra 一键生成 QyzROM
"""

import os
import prepare
import custom
from image import Kernel, BootImg

from utils import MyPrinter

myprinter = MyPrinter()

WORK_FOLDER = "TEST"
ZIP_NAME = "S9180.zip"

# 1. 提取需要的文件
# prepare.main(f"./{WORK_FOLDER}/{ZIP_NAME}")
# myprinter.print_yellow("1. 镜像文件提取完毕")

# 2. 分门别类处理镜像
# 2.1 avb去除
custom.deal_with_vbmetaimg(f"{WORK_FOLDER}/BL/vbmeta.img")
custom.deal_with_vbmetaimg(f"{WORK_FOLDER}/AP/vbmeta_system.img")
myprinter.print_yellow("2.1 AVB处理完毕")

# 2.2 内核替换
resource_kernel = Kernel("./resource/kernel/kernel")
myprinter.print_white(resource_kernel.read_version())

with BootImg(f"{WORK_FOLDER}/AP/boot.img") as origin_boot:
    origin_boot.unpack()
    os.system(f"rm {WORK_FOLDER}/AP/kernel")
    resource_kernel.copy_to(f"{WORK_FOLDER}/AP/kernel")
    origin_boot.repack()
    os.system(f"rm {WORK_FOLDER}/AP/kernel")
    os.system(f"mv f'{WORK_FOLDER}/AP/new-boot.img' 
              f'{WORK_FOLDER}/AP/boot.img")
