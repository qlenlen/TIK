import os
import zipfile
import tarfile
import shutil
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor  # 使用线程池而非进程池

NEEDED_TARS = ["AP", "BL", "CSC"]

TARGETS = {
    "BL": ["vbmeta"],
    "AP": [
        "boot",
        "dtbo",
        "init_boot",
        "recovery",
        "super",
        "vbmeta_system",
        "vendor_boot",
    ],
    "CSC": ["optics", "prism"],
    "CP": [],
    "HOME": [],
}


def main(abs_zippath: str = "9180.zip"):
    """传入压缩包绝对路径，提取其中的 .img 文件并解压 .lz4 文件"""
    start_time = time.time()  # 记录总耗时开始

    backup_dir = os.getcwd()
    workdir = os.path.dirname(abs_zippath)
    os.chdir(workdir)

    prepare_folder()
    extract_tar_from_zip(os.path.basename(abs_zippath))

    # 提取 tar 文件中的 .img 文件
    with ThreadPoolExecutor(max_workers=4) as executor:
        extract_start_time = time.time()  # 记录提取 img 文件的耗时
        executor.map(
            extract_img_from_tar,
            (
                tarname
                for tarname in pathlib.Path("tars").iterdir()
                if tarname.is_file()
            ),
        )
        extract_end_time = time.time()
        print(
            f"Extract .img files: {extract_end_time - extract_start_time:.2f} seconds"
        )

    # 解压 .lz4 文件
    with ThreadPoolExecutor(max_workers=4) as executor:
        decompress_start_time = time.time()  # 记录解压 .lz4 文件的耗时
        executor.map(
            decompress_lz4_by_binary,
            (
                f"{folder}/{imgname}"
                for folder in NEEDED_TARS
                for imgname in os.listdir(folder)
                if imgname.endswith(".lz4")
            ),
        )
        decompress_end_time = time.time()
        print(
            f"Decompress .lz4 files: {decompress_end_time - decompress_start_time:.2f} seconds"
        )

    shutil.rmtree("tars")
    os.chdir(backup_dir)

    end_time = time.time()  # 记录总耗时结束
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


def prepare_folder():
    """创建必要的文件夹，并清理旧数据"""
    for folder in ["AP", "BL", "CSC", "tars"]:
        shutil.rmtree(folder, ignore_errors=True)
        os.mkdir(folder)


def extract_tar_from_zip(zipname: str):
    """从 zip 文件中提取 tar 文件"""
    zip_start_time = time.time()  # 记录提取 tar 文件的耗时
    with zipfile.ZipFile(zipname, "r") as zip:
        for name in zip.namelist():
            if name.endswith(".tar.md5") or name.endswith(".tar"):
                zip.extract(name, path="./tars")
                print(f"Extracted {name}")
    zip_end_time = time.time()
    print(f"Extract tar files from zip: {zip_end_time - zip_start_time:.2f} seconds")


def extract_img_from_tar(tarname: pathlib.Path):
    """从 tar 文件中提取 .img 文件"""
    tar_dir = tarname.name.split("_")[0]

    with tarfile.open(tarname.absolute(), "r") as tar:
        for raw_name in TARGETS[tar_dir]:
            for actual_name in tar.getnames():
                if actual_name.startswith(raw_name):
                    target_path = os.path.join(tar_dir, actual_name)
                    if not os.path.exists(target_path):  # 确保线程安全的写入
                        tar.extract(actual_name, path=tar_dir)
                        print(f"Extracted {actual_name} from {tarname}")


def decompress_lz4_by_binary(imgname: str):
    """解压 .lz4 文件"""
    try:
        out_name = imgname.rsplit(".", 1)[0]
        os.system(f"lz4 {imgname}")
        print(f"Decompressed {imgname} to {out_name}")
        os.remove(imgname)
    except Exception as e:
        print(f"Failed to decompress {imgname}: {e}")


if __name__ == "__main__":
    main()
