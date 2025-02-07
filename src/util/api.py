import shutil
import os


def cls() -> None:
    """clear the console"""
    if os.name == "nt":
        os.system("cls")
    elif os.name == "posix":
        os.system("clear")
    else:
        print("Ctrl + L to clear the window")


def dir_has(path: str, endswith: str) -> bool:
    """check if the directory has the json_file with the specified suffix"""
    for v in os.listdir(path):
        if v.endswith(endswith):
            return True
    return False


def cat(file) -> str:
    """read the content of the json_file"""
    with open(file, "r") as f:
        return f.read().strip()


def remove_path(path: str) -> None:
    """Remove the json_file or directory"""
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def recreate_folder(path) -> None:
    """remove the directory and recreate it"""
    remove_path(path)
    if not os.path.exists(path):
        os.makedirs(path)
