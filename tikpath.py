import os
import platform

TIK_PATH = ""
BIN_PATH = ""
PROJECT_PATH = ""


def init():
    global TIK_PATH, BIN_PATH
    TIK_PATH = os.getcwd()
    BIN_PATH = TIK_PATH + os.sep + "bin"


def get_project_name():
    return os.path.basename(PROJECT_PATH)


def set_project_path(project_name: str):
    global PROJECT_PATH
    PROJECT_PATH = os.path.join(os.getcwd(), project_name)


def get_binary_path(bname: str):
    arch_type = platform.machine()
    os_type = platform.system()

    # find binary from here
    bin_path = os.path.join(BIN_PATH, os_type, arch_type) + os.sep
    return os.path.join(bin_path, bname)


def get_file_contexts(img_name: str):
    return os.path.join(PROJECT_PATH, "config", f"{img_name}_file_contexts")


def get_fs_config(img_name: str):
    return os.path.join(PROJECT_PATH, "config", f"{img_name}_fs_config")


def get_output_path():
    return os.path.join(PROJECT_PATH, "TI_out")


def get_out_img_path(img_name: str):
    return os.path.join(PROJECT_PATH, "TI_out", f"{img_name}.img")


def get_input_for_image(img_name: str):
    return os.path.join(PROJECT_PATH, img_name)
