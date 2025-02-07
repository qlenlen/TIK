import os

import tikpath
from src.util.TypeDetector import TypeDetector
from src.util.utils import MyPrinter


class MyImage(object):
    def __init__(self, img_name: str):
        self.img_name = img_name
        self.img_path = os.path.join(tikpath.PROJECT_PATH, img_name)
        self.content_path = self.img_path.rsplit(".", 1)[0]
        self.img_type = TypeDetector(self.img_path).get_type().upper()
        self.myprinter = MyPrinter()

    def __str__(self):
        return f"Img: {self.img_path} {self.img_type}"
