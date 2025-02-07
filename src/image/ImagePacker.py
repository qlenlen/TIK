import os
import shutil
import subprocess
import time

import tikpath
from src.image.ImageConverter import ImageConverter
from src.image.image import calc_time, ImageSizeCalculator
from src.lib import mkdtboimg
from src.patch import fspatch, contextpatch
from src.util.TypeDetector import TypeDetector
from src.util.log import print_yellow, wrap_red, print_green
from src.util.utils import SetUtils, remove_duplicate_lines


class ImagePacker:
    def __init__(self, content_path: str):
        self.content_path = content_path
        self.img_path = content_path + ".img"
        self.img_name = os.path.basename(content_path)

    def get_img_type(self):
        return TypeDetector(self.img_path).get_type()

    def convert2simg(self):
        ImageConverter(self.img_path).img2simg()

    @calc_time
    def pack_ext(self):
        self.deal_with_fsconfig()
        self.deal_with_file_contexts()

        ext_size = ImageSizeCalculator(self.content_path).calculate_size("ext4")
        size = int(ext_size / int(SetUtils.BLOCKSIZE))
        utc = int(time.time())
        subprocess.run(
            rf"{tikpath.get_binary('mke2fs')} \
                -O ^has_journal \
                -L {self.img_name} \
                -I 256 \
                -M /{self.img_name} \
                -m 0 \
                -t ext4 \
                -b {SetUtils.BLOCKSIZE} \
                {self.img_path} \
                {size}",
            shell=True,
        )
        subprocess.run(
            rf"{tikpath.get_binary('e2fsdroid')} -e \
                -T {utc} \
                -S {tikpath.get_file_contexts(self.img_name)} \
                -C {tikpath.get_fs_config(self.img_name)} \
                -a /{self.img_name} \
                -f {self.content_path} \
                {self.img_path}",
            shell=True,
        )

    @calc_time
    def pack_erofs(self):
        utc = int(time.time())
        subprocess.run(
            rf"{tikpath.get_binary('mkfs.erofs')} \
                -z{SetUtils.erofslim} \
                -T {utc} \
                --mount-point=/{self.img_name} \
                --fs-config-file={tikpath.get_fs_config(self.img_name)} \
                --file-contexts={tikpath.get_file_contexts(self.img_name)} \
                {self.img_path} \
                {self.content_path}",
            shell=True,
        )

    def deal_with_fsconfig(self):
        # patch file_contexts and fs_config
        fspatch.main(self.content_path, tikpath.get_fs_config(self.img_name))
        remove_duplicate_lines(tikpath.get_fs_config(self.img_name))

    def deal_with_file_contexts(self):
        file_contexts_path = tikpath.get_file_contexts(self.img_name)
        if os.path.exists(file_contexts_path):
            contextpatch.main(self.content_path, file_contexts_path)
            remove_duplicate_lines(file_contexts_path)

    @calc_time
    def pack_f2fs(self):
        self.deal_with_fsconfig()
        self.deal_with_file_contexts()

        size_f2fs = ImageSizeCalculator(self.content_path).calculate_size("f2fs")

        with open(self.img_path, "wb") as f:
            f.truncate(size_f2fs)

        subprocess.run(
            rf"{tikpath.get_binary('mkfs.f2fs')} {self.img_path} \
                -O extra_attr \
                -O inode_checksum \
                -O sb_checksum \
                -O compression \
                -f",
            shell=True,
        )

        subprocess.run(
            rf"{tikpath.get_binary('sload.f2fs')} \
                -f {self.content_path} \
                -C {tikpath.get_fs_config(self.img_name)} \
                -s {tikpath.get_file_contexts(self.img_name)} \
                -t /{self.img_name} \
                {self.img_path} \
                -c"
        )

    @calc_time
    def pack_dtbo(self):
        dtbo_dir = self.content_path
        dts_files_dir = os.path.join(dtbo_dir, "dts_files")
        dtbo_files_dir = os.path.join(dtbo_dir, "new_dtbo_files")
        if os.path.exists(dtbo_dir + os.sep + "new_dtbo_files"):
            shutil.rmtree(dtbo_dir + os.sep + "new_dtbo_files")
        os.makedirs(dtbo_dir + os.sep + "new_dtbo_files")

        for dts_files in os.listdir(dts_files_dir):
            new_dtbo_files = dts_files.replace("dts", "dtbo")
            dtbo_abs = os.path.join(dtbo_files_dir, new_dtbo_files)
            dts_abs = os.path.join(dts_files_dir, dts_files)
            print_yellow(f"正在回编译{dts_files}为{new_dtbo_files}")
            command = [
                tikpath.get_binary("dtc"),
                "-@",
                "-I dts",
                "-O dtb",
                dts_abs,
                f"-o {dtbo_abs}",
            ]
            subprocess.call(
                " ".join(command),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        print_yellow("正在生成dtbo.img...")
        list_: list[str] = []
        for b in os.listdir(dtbo_dir + os.sep + "new_dtbo_files"):
            if b.startswith("dtbo."):
                list_.append(dtbo_dir + os.sep + "new_dtbo_files" + os.sep + b)
        list_ = sorted(list_, key=lambda x: int(float(x.rsplit(".", 1)[1])))
        try:
            mkdtboimg.create_dtbo(self.img_path, list_, 4096)
        except (Exception, BaseException):
            wrap_red(f"{self.img_name}.img生成失败!")
        else:
            print_green(f"{self.img_name}.img生成完毕!")

    @calc_time
    def pack_vendor_boot(self):
        pass

    @calc_time
    def pack(self):
        pass
