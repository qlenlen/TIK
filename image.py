import os

import tikpath
from utils import gettype


class MyImage(object):
    def __init__(self, img_name: str):
        self.img_name = img_name
        self.img_path = os.path.join(tikpath.PROJECT_PATH, img_name)

    def get_type(self):
        return gettype(self.img_path)
