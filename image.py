import os
import pathlib
import shutil
import subprocess
import time
from argparse import Namespace

import extract_dtb
import rich
from rich.progress import track

import contextpatch
import fspatch
from lib import lpunpack, mkdtboimg, imgextractor
import tikpath
import utils
from lib.lpunpack import SparseImage
from log import print_yellow, wrap_red, print_green
from utils import MyPrinter, TypeDetector, SetUtils, JsonUtil


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


class ImageConverter:
    def __init__(self, path: str):
        self.path = path
        self.myprinter = MyPrinter()

    def simg2img(self):
        """Convert sparse img to raw img
        If succeeded, delete the sparse one"""
        with open(self.path, "rb") as fd:
            if SparseImage(fd).check():
                self.myprinter.print_white("Sparse image detected.")
                self.myprinter.print_white("Process conversion to non sparse image...")
                unsparse_file = SparseImage(fd).unsparse()
                self.myprinter.print_green("Result: [ok]")
            else:
                self.myprinter.print_red(f"{self.path} != Sparse. Skip!")

        if os.path.exists(unsparse_file):
            os.remove(self.path)
            os.rename(unsparse_file, self.path)

    def img2simg(self):
        """Convert raw img to sparse img"""
        bin_path = tikpath.get_binary_path("img2simg")
        command = f"{bin_path} {self.path} {self.path}.s"
        result = subprocess.run(command, shell=True)
        if result.returncode == 0:
            os.remove(self.path)
            os.rename(self.path + ".s", self.path)
        else:
            print(f"Command failed with return code {result.returncode}")


class ImagePacker:
    def __init__(self, content_path: str):
        self.content_path = content_path
        self.img_path = content_path + ".img"
        self.img_name = os.path.basename(content_path)

    def get_img_type(self):
        return TypeDetector(self.img_path).get_type()

    def convert2simg(self):
        ImageConverter(self.img_path).img2simg()

    def pack_ext(self):
        self.deal_with_fsconfig()
        self.deal_with_file_contexts()

        ext_size = SizeCalculator(self.content_path).resize()
        size = int(ext_size / int(SetUtils.BLOCKSIZE))
        utc = int(time.time())
        subprocess.run(
            rf"{tikpath.get_binary_path('mke2fs')} \
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
            rf"{tikpath.get_binary_path('e2fsdroid')} -e \
                -T {utc} \
                -S {tikpath.get_file_contexts(self.img_name)} \
                -C {tikpath.get_fs_config(self.img_name)} \
                -a /{self.img_name} \
                -f {self.content_path} \
                {self.img_path}",
            shell=True,
        )

    def pack_erofs(self):
        utc = int(time.time())
        subprocess.run(
            rf"{tikpath.get_binary_path('mkfs.erofs')} \
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
        utils.remove_duplicate_lines(tikpath.get_fs_config(self.img_name))

    def deal_with_file_contexts(self):
        file_contexts_path = tikpath.get_file_contexts(self.img_name)
        if os.path.exists(file_contexts_path):
            contextpatch.main(self.content_path, file_contexts_path)
            utils.remove_duplicate_lines(file_contexts_path)

    def pack_f2fs(self):
        self.deal_with_fsconfig()
        self.deal_with_file_contexts()

        size_f2fs = (54 * 1024 * 1024) + SizeCalculator(self.content_path).resize()
        size_f2fs = int(size_f2fs)

        with open(self.img_path, "wb") as f:
            f.truncate(size_f2fs)

        subprocess.run(
            rf"{tikpath.get_binary_path('mkfs.f2fs')} {self.img_path} \
                -O extra_attr \
                -O inode_checksum \
                -O sb_checksum \
                -O compression \
                -f",
            shell=True,
        )

        subprocess.run(
            rf"{tikpath.get_binary_path('sload.f2fs')} \
                -f {self.content_path} \
                -C {tikpath.get_fs_config(self.img_name)} \
                -s {tikpath.get_file_contexts(self.img_name)} \
                -t /{self.img_name} \
                {self.img_path} \
                -c"
        )

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
                tikpath.get_binary_path("dtc"),
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

    def pack(self):
        pass


class ImageUnpacker:
    def __init__(self, img_path: str):
        self.img_path = img_path
        self.img_name = os.path.basename(img_path)
        self.content_path = img_path.rsplit(".", 1)[0]
        self.myprinter = MyPrinter()

    def record_parts_info(self, img_type: str):
        JsonUtil(tikpath.get_parts_info()).update(self.img_name, img_type)

    def unpack_ext(self):
        self.record_parts_info("ext")
        base_name = os.path.basename(self.img_path).split(".")[0]
        with rich.Console().status(
            f"[yellow]正在提取{os.path.basename(self.img_path)}[/]"
        ):
            imgextractor.Extractor().main(
                self.img_path, tikpath.PROJECT_PATH + base_name, tikpath.PROJECT_PATH
            )

    def unpack_erofs(self):
        self.record_parts_info("erofs")
        bin_path = tikpath.get_binary_path("extract.erofs")
        subprocess.run(
            f"{bin_path} -x \
                -i {self.img_path} \
                -o {tikpath.PROJECT_PATH}",
            shell=True,
        )

    def unpack_f2fs(self):
        self.record_parts_info("f2fs")
        bin_path = tikpath.get_binary_path("extract.f2fs")
        subprocess.run(
            f"{bin_path} -o {tikpath.PROJECT_PATH} \
                {self.img_path}",
            shell=True,
        )

    def unpack_dtbo(self):
        self.record_parts_info("dtbo")
        # remove the old dir before unpacking
        if os.path.exists(self.content_path):
            shutil.rmtree(self.content_path)

        dtbo_files_path = os.path.join(self.content_path, "dtbo_files")
        dts_files_path = os.path.join(self.content_path, "dts_files")
        os.makedirs(dtbo_files_path)
        os.makedirs(dts_files_path)

        self.myprinter.print_yellow("正在解压dtbo.img")
        mkdtboimg.dump_dtbo(
            self.img_path, os.path.join(self.content_path, "dtbo_files", "dtbo")
        )

        for dtbo_files in os.listdir(dtbo_files_path):
            if dtbo_files.startswith("dtbo."):
                dts_files = dtbo_files.replace("dtbo", "dts")
                self.myprinter.print_yellow(f"正在反编译{dtbo_files}为{dts_files}")
                dtbofiles = os.path.join(dtbo_files_path, dtbo_files)
                command = [
                    tikpath.get_binary_path("dtc"),
                    "-@",
                    "-I dtb",
                    "-O dts",
                    dtbofiles,
                    f"-o {os.path.join(dts_files_path, dts_files)}",
                ]
                if (
                    subprocess.call(
                        " ".join(command),
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    != 0
                ):
                    self.myprinter.print_red(f"反编译{dtbo_files}失败！")
                    return
        self.myprinter.print_green("完成！")
        shutil.rmtree(dtbo_files_path)

    def unpack_dtb(self):
        self.record_parts_info("dtb")
        dtbdir = self.img_path
        shutil.rmtree(dtbdir)
        if not os.path.exists(dtbdir):
            os.makedirs(dtbdir)
        extract_dtb.extract_dtb.split(
            Namespace(
                filename=self.content_path,
                output_dir=os.path.join(dtbdir, "dtb_files"),
                extract=1,
            )
        )
        self.myprinter.print_yellow("正在反编译dtb...")
        for i in track(os.listdir(dtbdir + os.sep + "dtb_files")):
            if i.endswith(".dtb"):
                name = i.split(".")[0]
                dtb = os.path.join(dtbdir, "dtb_files", name + ".dtb")
                dts = os.path.join(dtbdir, "dtb_files", name + ".dts")
                os.system(f"dtc -@ -I dtb -O dts {dtb} -o {dts}")
        self.myprinter.print_green("反编译完成!")

    def unpack_super(self):
        lpunpack.unpack(self.img_path, tikpath.PROJECT_PATH)

    def unpack_boot(self):
        bin_path = tikpath.get_binary_path("magiskboot")
        subprocess.run(f"{bin_path} unpack {self.img_path}", shell=True)

    def unpack(self):
        # judge the img type
        match TypeDetector(self.img_path).get_type():
            case "sparse":
                ImageConverter(self.img_path).simg2img()
                self.unpack()
            case "dtbo":
                self.unpack_dtbo()
            case "ext":
                self.unpack_ext()
            case "erofs":
                self.unpack_erofs()
            case "f2fs":
                self.unpack_f2fs()
            case "super":
                self.unpack_super()
            case "boot":
                self.unpack_boot()


class MyImage(object):
    def __init__(self, img_name: str):
        self.img_name = img_name
        self.img_path = os.path.join(tikpath.PROJECT_PATH, img_name)
        self.img_type = TypeDetector(self.img_path).get_type().upper()
