"""
Samsung S23 Ultra 一键生成 QyzROM
"""

import os
import pathlib
import custom
from src.image import Kernel, BootImg

from utils import MyPrinter

myprinter = MyPrinter()

work = pathlib.Path("../../TEST")
resource = pathlib.Path("../../resource")

WORK = work.absolute()
RESOURCE = resource.absolute()

ZIP_NAME = "S9180.zip"

# 1. 提取需要的文件
# prepare.main(f"./{WORK}/{ZIP_NAME}")
# myprinter.print_yellow("1. 镜像文件提取完毕")

# 2. 分门别类处理镜像
# 2.1 avb去除
custom.deal_with_vbmetaimg(f"{WORK}/BL/vbmeta.img")
custom.deal_with_vbmetaimg(f"{WORK}/AP/vbmeta_system.img")
myprinter.print_yellow("2.1 AVB处理完毕")

# 2.2 内核替换
resource_kernel = Kernel(f"{RESOURCE}/kernel/kernel")
myprinter.print_white(resource_kernel.read_version())

with BootImg(f"{WORK}/AP/boot.img") as origin_boot:
    # 此块内工作目录为 {WORK}/AP
    origin_boot.unpack()
    os.system(f"rm kernel")
    resource_kernel.copy_to(f"{WORK}/AP/kernel")
    origin_boot.repack()
    os.system(f"rm kernel")
    os.system(f"mv new-boot.img boot.img")
myprinter.print_yellow("2.2 内核替换完毕")

# 2.3 替换twrp
twrp = f"{RESOURCE}/twrp/dm3q.img"
os.system(f"cp {twrp} {WORK}/AP/recovery.img")
myprinter.print_yellow("2.3 twrp替换完毕")

# 2.4 处理vendor_boot
