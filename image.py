import os
import subprocess

import rich

import imgextractor
import tikpath
from lpunpack import SparseImage
from utils import MyPrinter, TypeDetector


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
    def __init__(self, path: str):
        self.path = path

    def pack_ext(self):
        pass

    def pack_erofs(self):
        pass

    def pack_f2fs(self):
        pass

    def pack(self):
        pass


class ImageUnpacker:
    def __init__(self, path: str):
        self.path = path

    def unpack_ext(self):
        base_name = os.path.basename(self.path).split(".")[0]
        with rich.Console().status(f"[yellow]正在提取{os.path.basename(self.path)}[/]"):
            imgextractor.Extractor().main(
                self.path, tikpath.PROJECT_PATH + base_name, tikpath.PROJECT_PATH
            )

    def unpack_erofs(self):
        bin_path = tikpath.get_binary_path('extract.erofs')
        subprocess.run(
            f"{bin_path} -x \
                -i {self.path} \
                -o {tikpath.PROJECT_PATH}"
            , shell=True
        )

    def unpack_f2fs(self):
        bin_path = tikpath.get_binary_path('extract.f2fs')
        subprocess.run(
            f"{bin_path} -o {tikpath.PROJECT_PATH} \
                {self.path}"
        )

    def unpack(self):
        # judge the img type
        match TypeDetector(self.path):
            case "ext":
                self.unpack_ext()
            case "erofs":
                self.unpack_erofs()
            case "f2fs":
                self.unpack_f2fs()


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
