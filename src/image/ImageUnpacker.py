import os
import shutil
import subprocess
from argparse import Namespace

import rich
from extract_dtb import extract_dtb
from rich.progress import track

import tikpath
from src.image.Image import MyImage
from src.image.ImageConverter import ImageConverter
from src.image.image import calc_time
from src.lib import mkdtboimg, lpunpack, imgextractor
from src.util.TypeDetector import TypeDetector
from src.util.utils import JsonUtil


class ImageUnpacker(MyImage):
    def __init__(self, img_name: str):
        super().__init__(img_name)

    def init_parts_info(self):
        JsonUtil(tikpath.get_parts_info()).write({})
        self.myprinter.print_yellow("初始化分区信息表")

    def record_parts_info(self, img_type: str):
        if not os.path.exists(tikpath.get_parts_info()):
            self.init_parts_info()
        JsonUtil(tikpath.get_parts_info()).update(self.img_name, img_type)

    @calc_time
    def unpack_ext(self):
        base_name = os.path.basename(self.img_path).split(".")[0]
        with rich.Console().status(
            f"[yellow]正在提取{os.path.basename(self.img_path)}[/]"
        ):
            imgextractor.Extractor().main(
                self.img_path, tikpath.PROJECT_PATH + base_name, tikpath.PROJECT_PATH
            )

    @calc_time
    def unpack_erofs(self):
        bin_path = tikpath.get_binary("extract.erofs")
        subprocess.run(
            f"{bin_path} -x \
                -i {self.img_path} \
                -o {tikpath.PROJECT_PATH}",
            shell=True,
        )

    @calc_time
    def unpack_f2fs(self):
        self.record_parts_info("f2fs")
        bin_path = tikpath.get_binary("extract.f2fs")
        subprocess.run(
            f"{bin_path} -o {tikpath.PROJECT_PATH} \
                {self.img_path}",
            shell=True,
        )

    @calc_time
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
                    tikpath.get_binary("dtc"),
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

    @calc_time
    def unpack_dtb(self):
        self.record_parts_info("dtb")
        dtbdir = self.img_path
        shutil.rmtree(dtbdir)
        if not os.path.exists(dtbdir):
            os.makedirs(dtbdir)
        extract_dtb.split(
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

    @calc_time
    def unpack_super(self):
        lpunpack.unpack(self.img_path, tikpath.PROJECT_PATH)

    @calc_time
    def unpack_vendor_boot(self):
        project = tikpath.PROJECT_PATH
        name = self.img_name
        shutil.rmtree(project + os.sep + name)
        os.makedirs(project + os.sep + name)
        os.chdir(project + os.sep + name)
        file = ""
        if os.system("magiskboot unpack -h %s" % file) != 0:
            print("Unpack %s Fail..." % file)
            shutil.rmtree(project + os.sep + name)
            return
        if os.access(project + os.sep + name + os.sep + "ramdisk.cpio", os.F_OK):
            comp = TypeDetector.get_type(
                project + os.sep + name + os.sep + "ramdisk.cpio"
            )
            print(f"Ramdisk is {comp}")
            with open(project + os.sep + name + os.sep + "comp", "w") as f:
                f.write(comp)
            if comp != "unknow":
                os.rename(
                    project + os.sep + name + os.sep + "ramdisk.cpio",
                    project + os.sep + name + os.sep + "ramdisk.cpio.comp",
                )
                if (
                    os.system(
                        "magiskboot decompress %s %s"
                        % (
                            project + os.sep + name + os.sep + "ramdisk.cpio.comp",
                            project + os.sep + name + os.sep + "ramdisk.cpio",
                        )
                    )
                    != 0
                ):
                    print("Decompress Ramdisk Fail...")
                    return
            if not os.path.exists(project + os.sep + name + os.sep + "ramdisk"):
                os.mkdir(project + os.sep + name + os.sep + "ramdisk")
            os.chdir(project + os.sep + name + os.sep)
            print("Unpacking Ramdisk...")
            os.system("cpio -i -d -F ramdisk.cpio -D ramdisk")
        else:
            print("Unpack Done!")

    @calc_time
    def unpack_boot(self):
        bin_path = tikpath.get_binary("magiskboot")
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
