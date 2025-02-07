"""统一路径管理

"""

import os
import platform
import pathlib

from src.util.utils import MyPrinter

myprinter = MyPrinter()

TIK_PATH = pathlib.Path(__file__).parent.absolute()
BIN_PATH = os.path.join(TIK_PATH, "bin", platform.machine(), platform.system())

PROJECT_PATH = ""
OUTPUT_PATH = ""


def init():
    myprinter.print_red(f"TIK_PATH -> {TIK_PATH}")
    myprinter.print_red(f"BIN_PATH -> {BIN_PATH}")


def get_project_path():
    if PROJECT_PATH:
        return PROJECT_PATH
    else:
        raise ProjectNotSetError()


def get_project_name():
    if PROJECT_PATH:
        return os.path.basename(PROJECT_PATH)
    else:
        raise ProjectNotSetError()


def get_img_within_project(img_name: str) -> str:
    if PROJECT_PATH:
        return os.path.join(PROJECT_PATH, f"{img_name}.img")
    else:
        raise ProjectNotSetError()


def set_project(project_name: str):
    global PROJECT_PATH, OUTPUT_PATH
    PROJECT_PATH = os.path.join(TIK_PATH, project_name)
    OUTPUT_PATH = os.path.join(PROJECT_PATH, "TI_out")
    myprinter.print_red(f"PROJECT_PATH -> {PROJECT_PATH}")
    myprinter.print_red(f"OUTPUT_PATH -> {OUTPUT_PATH}")


def get_binary(bname: str):
    return os.path.join(BIN_PATH, bname)


def get_parts_info():
    return os.path.join(PROJECT_PATH, "config", "parts_info")


def get_file_contexts(img_name: str):
    return os.path.join(PROJECT_PATH, "config", f"{img_name}_file_contexts")


def get_fs_config(img_name: str):
    return os.path.join(PROJECT_PATH, "config", f"{img_name}_fs_config")


def get_out_img_path(img_name: str):
    if OUTPUT_PATH:
        return os.path.join(OUTPUT_PATH, f"{img_name}.img")
    else:
        raise ProjectNotSetError()


def get_image_content(img_name: str):
    return os.path.join(PROJECT_PATH, img_name)


class ProjectNotSetError(Exception):
    def __init__(self):
        super().__init__("项目尚未初始化")


if __name__ == "__main__":
    set_project("TEST")
    get_project_name()
