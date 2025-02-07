import os
import subprocess

import tikpath
from src.lib.lpunpack import SparseImage
from src.util.utils import MyPrinter


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
        bin_path = tikpath.get_binary("img2simg")
        command = f"{bin_path} {self.path} {self.path}.s"
        result = subprocess.run(command, shell=True)
        if result.returncode == 0:
            os.remove(self.path)
            os.rename(self.path + ".s", self.path)
        else:
            raise Exception(f"Command failed with return code {result.returncode}")
