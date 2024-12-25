import os
import shutil
import subprocess
import time
from argparse import Namespace

import extract_dtb
import rich
from rich.progress import track

import imgextractor
import lpunpack
import mkdtboimg
import tikpath
from lpunpack import SparseImage
from utils import MyPrinter, TypeDetector, SetUtils


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

    def pack_ext(self):
        pass

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

    def pack_f2fs(self):
        pass

    def pack(self):
        pass


class ImageUnpacker:
    def __init__(self, img_path: str):
        self.img_path = img_path
        self.content_path = img_path.rsplit(".", 1)[0]
        self.myprinter = MyPrinter()

    def unpack_ext(self):
        base_name = os.path.basename(self.img_path).split(".")[0]
        with rich.Console().status(
            f"[yellow]正在提取{os.path.basename(self.img_path)}[/]"
        ):
            imgextractor.Extractor().main(
                self.img_path, tikpath.PROJECT_PATH + base_name, tikpath.PROJECT_PATH
            )

    def unpack_erofs(self):
        bin_path = tikpath.get_binary_path("extract.erofs")
        subprocess.run(
            f"{bin_path} -x \
                -i {self.img_path} \
                -o {tikpath.PROJECT_PATH}",
            shell=True,
        )

    def unpack_f2fs(self):
        bin_path = tikpath.get_binary_path("extract.f2fs")
        subprocess.run(
            f"{bin_path} -o {tikpath.PROJECT_PATH} \
                {self.img_path}",
            shell=True,
        )

    def unpack_dtbo(self):
        # remove the old dir before unpacking
        shutil.rmtree(self.content_path)

        dtbo_files_path = os.path.join(self.content_path, "dtbo_files")
        dts_files_path = os.path.join(self.content_path, "dts_files")
        os.makedirs(dtbo_files_path)
        os.makedirs(dts_files_path)

        self.myprinter.print_yellow("正在解压dtbo.img")
        mkdtboimg.dump_dtbo(
            self.content_path, os.path.join(self.content_path, "dtbo_files", "dtbo")
        )

        for dtbo_files in os.listdir(dtbo_files_path):
            if dtbo_files.startswith("dtbo."):
                dts_files = dtbo_files.replace("dtbo", "dts")
                self.myprinter.print_yellow(f"正在反编译{dtbo_files}为{dts_files}")
                dtbofiles = os.path.join(dts_files_path, dtbo_files)
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
        pass

    def unpack(self):
        # judge the img type
        match TypeDetector(self.img_path):
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

    def get_type(self):
        return TypeDetector(self.img_path).get_type()

    def unpack(self):
        img_type = self.get_type()
        match img_type:
            case "ext":
                ImageUnpacker()
