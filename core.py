import json
import os
import re
import shutil
import subprocess
import sys
import time
from argparse import Namespace

import extract_dtb
import requests
from rich.progress import track

import banner
import contextpatch
import fspatch
import lpunpack
import mkdtboimg
import tikpath
import utils
from api import cls, dir_has, dirsize
from image import ImageConverter, ImageUnpacker
from log import *
from utils import JsonEdit, gettype, simg2img, versize, SetUtils


def write_project_path(project_path: str):
    with open("config/project_path", "w") as f:
        f.write(project_path)


def get_project_path() -> str:
    """
    获取当前项目路径
    :return: 项目路径
    """
    return os.getcwd()


def dis_avb(fstab: str):
    print(f"正在处理: {fstab}")
    if not os.path.exists(fstab):
        return
    with open(fstab, "r") as sf:
        details = sf.read()
    details = re.sub("avb=vbmeta_system,", "", details)
    details = re.sub("avb,", "", details)
    details = re.sub(",avb_keys=.*avbpubkey", "", details)
    with open(fstab, "w") as tf:
        tf.write(details)


def greet():
    print(f"\033[31m {banner.banner1} \033[0m")
    print("\033[93;44m Alpha Edition \033[0m")

    try:
        content = json.loads(
            requests.get(
                "https://v1.jinrishici.com/all.json", timeout=2
            ).content.decode()
        )
        shiju = content.get("content")
        fr = content.get("origin")
        another = content.get("author")
    except (Exception, BaseException):
        print(f"\033[36m “开源，是一场无问西东的前行”\033[0m\n")
    else:
        print(f"\033[36m “{shiju}”")
        print(f"\033[36m---{another}《{fr}》\033[0m\n")


class Tool:
    """
    主程序的主循环
    """
    printer = utils.MyPrinter()

    def __init__(self):
        self.local_dir = os.getcwd()
        print_yellow(f"TIK根目录：{self.local_dir}")

        # current working project
        self.project_name = ""
        # the absolute path of the project
        self.project_root = ""
        # skip them when recognize projects
        self.WHITELIST = ["bin", "ksu-derviers", "__pycache__", "config"]

    def user_continue(self):
        input("任意按钮继续")

    def main(self):
        # key-value pairs of the projects(number: project_name)
        project_num = 0
        projects = {}

        # clear the screen and show the banner
        cls()
        greet()

        self.printer.print_white(" > 项目列表\n")
        self.printer.print_red("   [00]  删除项目\n")
        self.printer.print_green("   [0]  新建项目\n")

        # list all the projects
        for project_dir in os.listdir(self.local_dir):
            # neglect the directories in the whitelist
            if project_dir in self.WHITELIST or project_dir.startswith("."):
                continue
            # make sure it is a directory
            if os.path.isdir(os.path.join(self.local_dir, project_dir)):
                project_num += 1
                print(f"   [{project_num}]  {project_dir}\n")
                projects.update({str(project_num): project_dir})

        print("  --------------------------------------")
        print("\033[33m  [77] 设置  [88] 退出\033[0m\n")

        op_pro = input("  请输入序号：")

        if op_pro == "00":
            # delete the project
            if (
                delete_index := input("  请输入你要删除的项目序号:").strip()
            ) in projects.keys():
                if input(f"  确认删除{projects[delete_index]}？[1/0]") == "1":
                    shutil.rmtree(os.path.join(tikpath.TIK_PATH, projects[delete_index]))
                else:
                    print_red("取消删除")
            else:
                print_red("  项目不存在！")
                self.user_continue()

        elif op_pro == "0":
            new_project_name = input("请输入项目名称(非中文)：")
            if new_project_name:
                if os.path.exists(os.path.join(self.local_dir, new_project_name)):
                    wrap_red(f"项目已存在！请更换名称")
                    self.user_continue()
                os.makedirs(os.path.join(self.local_dir, new_project_name, "config"))
                os.makedirs(os.path.join(self.local_dir, new_project_name, "TI_out"))
                print_green(f"项目{new_project_name}创建成功！")
            else:
                print_red("  Input error!")
                self.user_continue()

        elif op_pro == "88":
            cls()
            print_green("\n感谢使用TI-KITCHEN5, 再见！")
            sys.exit(0)

        elif op_pro == "77":
            print_red("设计中...")
            self.user_continue()

        # enter to the working project
        elif op_pro.isdigit():
            if op_pro in projects.keys():
                # initialize the project
                self.project_name = projects.get(op_pro, "")
                self.project_root = os.path.join(self.local_dir, self.project_name)
                self.project()
            else:
                print_red("  Input error!")
                self.user_continue()

        else:
            print_red("  Input error!")
            self.user_continue()

        # back to the main menu
        self.main()

    @staticmethod
    def dis_data_encryption(fstab):
        ...

    def project(self):
        cls()

        tikpath.set_project_path(self.project_name)

        print(utils.red("> 项目菜单"))
        (
            print(f"  项目：{self.project_name}\033[91m(不完整)\033[0m\n")
            if not os.path.exists(os.path.abspath("config"))
            else print(f"  项目：{self.project_name}\n")
        )

        # create the necessary directories if not exists
        os.makedirs(self.project_root + os.sep + "TI_out", exist_ok=True)
        os.makedirs(self.project_root + os.sep + "config", exist_ok=True)

        self.printer.print_yellow("    1> 解包菜单     2> 打包菜单\n")
        self.printer.print_blue("    3> 定制功能     4> 精简分区\n")
        self.printer.print_green("    00> 返回主页    88> 退出TIK\n")

        op_menu = input("    请输入编号: ")

        if op_menu == "00":
            self.main()
            return

        elif op_menu == "1":
            unpack_choo()

        elif op_menu == "2":
            pack_choo()

        elif op_menu == "3":
            self.custom_rom()

        elif op_menu == "4":
            self.slim_partition()

        elif op_menu == "88":
            cls()
            print_green("\n感谢使用TI-KITCHEN5,再见！")
            sys.exit(0)

        else:
            wrap_red("   Input error!")
            self.user_continue()

        self.project()

    def slim_partition(self):
        print_red("暂未支持")
        self.user_continue()
        pass

    def custom_rom(self):
        cls()
        print(" \033[31m>定制菜单 \033[0m\n")
        print(f"  项目：{self.project_name}\n")
        print("\033[33m    0> 返回上级  1> xxxx\033[0m\n")
        print("\033[33m    2> KSU修补   3> Apatch修补\033[0m\n")
        print("\033[33m    4> 去除avb   5> 去除data加密\033[0m\n")
        op_menu = input("    请输入编号: ")
        if op_menu == "0":
            return
        elif op_menu == "1":
            pass
        elif op_menu == "2":
            self.ksu_patch()
        elif op_menu == "3":
            self.apatch_patch()
        elif op_menu == "4":
            for root, dirs, files in os.walk(tikpath.TIK_PATH + os.sep + self.project_name):
                for file in files:
                    if file.startswith("fstab."):
                        dis_avb(os.path.join(root, file))
        elif op_menu == "5":
            wrap_red("暂未支持")
            ...
        else:
            wrap_red("   Input error!")
        self.user_continue()
        self.custom_rom()

    def ksu_patch(self):
        cls()
        cs = 0
        project = self.local_dir + os.sep + self.project_name
        os.chdir(self.local_dir)
        print(" \n\033[31m>ksu修补 \033[0m\n")
        print(f"  项目：{self.project_name}\n")
        print(f"  请将要修补的镜像放入{project}")

        boots = {}
        for i in os.listdir(project):
            if os.path.isdir(os.path.join(project, i)):
                continue
            if gettype(os.path.join(project, i)) in ["boot", "init_boot"]:
                cs += 1
                boots[str(cs)] = os.path.join(project, i)
                print(f"  [{cs}]--{i}")
        print("\033[33m-------------------------------\033[0m")
        print("\033[33m    [00] 返回\033[0m\n")
        op_menu = input("    请输入需要修补的boot的序号: ")

        if op_menu in boots.keys():
            kmi = {"1": "android13-5.15", "2": "android14-5.15", "3": "android14-6.1"}
            print("\033[33m-------------------------------\033[0m")
            print("\033[33m    [00] 取消修补\033[0m\n")
            for i in kmi.keys():
                print(f"    {i}: {kmi[i]}\n")
            kmi_choice = input("\033[33m请选择内核镜像需要的kmi: \033[0m")

            if kmi_choice == "00":
                return

            os.system(
                rf"{tikpath.get_binary_path('ksud')} boot-patch \
                    -b {boots[op_menu]} \
                    --magiskboot {tikpath.get_binary_path('magiskboot')} \
                    --kmi={kmi.get(kmi_choice)} \
                    --out {project}"
            )

        elif op_menu == "00":
            os.chdir(project)
            return
        else:
            wrap_red("Input Error!")
        self.user_continue()
        self.project()

    def apatch_patch(self):
        ...


def unpack_choo():
    """解包前端"""
    cls()
    project_dir = tikpath.PROJECT_PATH

    print(" \033[31m >分解 \033[0m\n")
    filen = 0
    files = {}
    infos = {}
    wrap_red(f"  请将文件放于{project_dir}根目录下！\n")
    print(" [0]- 分解所有文件\n")

    if dir_has(project_dir, ".img"):
        print("\033[33m [Img]文件\033[0m\n")
        for img0 in os.listdir(project_dir):
            if img0.endswith(".img"):
                if os.path.isfile(os.path.abspath(img0)):
                    filen += 1
                    info = gettype(os.path.abspath(img0))
                    (
                        wrap_red(f"   [{filen}]- {img0} <UNKNOWN>\n")
                        if info == "unknow"
                        else print(f"   [{filen}]- {img0} <{info.upper()}>\n")
                    )
                    files[filen] = img0
                    infos[filen] = "img" if info != "sparse" else "sparse"

    print("\n\033[33m  [00] 返回  [77] 循环解包  \033[0m")
    print("  --------------------------------------")
    filed = input("  请输入对应序号：")

    if filed == "0":
        for v in files.keys():
            unpack(files[v], infos[v], project_dir)

    elif filed == "77":
        imgcheck = 0
        upacall = input("  是否解包所有文件？ [1/0]")
        for v in files.keys():
            if upacall != "1":
                imgcheck = input(f"  是否解包{files[v]}?[1/0]")
            if upacall == "1" or imgcheck != "0":
                unpack(files[v], infos[v], project_dir)

    elif filed == "00":
        return

    elif filed.isdigit():
        (
            unpack(files[int(filed)], infos[int(filed)], project_dir)
            if int(filed) in files.keys()
            else wrap_red("Input error!")
        )

    else:
        wrap_red("Input error!")

    input("任意按钮继续")
    unpack_choo()


def pack_choo():
    """打包前端"""
    cls()

    project_dir = tikpath.PROJECT_PATH
    print(" \033[31m >打包 \033[0m\n")
    partn = 0
    parts, types = {}, {}
    json_ = JsonEdit(project_dir + os.sep + "config" + os.sep + "parts_info").read()
    if not os.path.exists(project_dir + os.sep + "config"):
        os.makedirs(project_dir + os.sep + "config")
    if project_dir:
        print("   [0]- 打包所有镜像\n")
        for packs in os.listdir(project_dir):
            if os.path.isdir(project_dir + os.sep + packs):
                if os.path.exists(
                    project_dir + os.sep + "config" + os.sep + packs + "_fs_config"
                ):
                    partn += 1
                    parts[partn] = packs
                    if packs in json_.keys():
                        typeo = json_[packs]
                    else:
                        typeo = "ext"
                    types[partn] = typeo
                    print(f"   [{partn}]- {packs} <{typeo}>\n")
                elif os.path.exists(project_dir + os.sep + packs + os.sep + "comp"):
                    partn += 1
                    parts[partn] = packs
                    types[partn] = "bootimg"
                    print(f"   [{partn}]- {packs} <bootimg>\n")
                elif os.path.exists(
                    project_dir + os.sep + "config" + os.sep + "dtbinfo_" + packs
                ):
                    partn += 1
                    parts[partn] = packs
                    types[partn] = "dtb"
                    print(f"   [{partn}]- {packs} <dtb>\n")
                elif os.path.exists(
                    project_dir + os.sep + "config" + os.sep + "dtboinfo_" + packs
                ):
                    partn += 1
                    parts[partn] = packs
                    types[partn] = "dtbo"
                    print(f"   [{partn}]- {packs} <dtbo>\n")

        print("\n\033[33m [66] 打包Super [00]返回\033[0m")
        print("  --------------------------------------")
        filed = input("  请输入对应序号：")
        # default
        form = "img"
        # default is raw
        israw = True

        # pack all images
        if filed == "0":
            print_yellow("您的选择是：打包所有镜像")
            op_menu = input("  输出文件格式[1]raw [2]sparse:")
            if op_menu == "2":
                israw = False
            imgtype = input("  手动打包所有分区格式为：[1]ext4 [2]erofs [3]f2fs:")
            if imgtype == "1":
                imgtype = "ext"
            elif imgtype == "2":
                imgtype = "erofs"
            else:
                imgtype = "f2fs"

            for f in track(parts.keys()):
                print_yellow(f"打包{parts[f]}...")
                if types[f] == "bootimg":
                    dboot(
                        project_dir + os.sep + parts[f],
                        project_dir + os.sep + parts[f] + ".img",
                    )
                elif types[f] == "dtb":
                    makedtb(parts[f], project_dir)
                elif types[f] == "dtbo":
                    makedtbo(parts[f], project_dir)
                else:
                    pack_img(parts[f], imgtype, israw)
        elif filed == "66":
            packsuper(project_dir)
        elif filed == "00":
            return
        elif filed.isdigit():
            if int(filed) in parts.keys():
                if types[int(filed)] not in [
                    "bootimg",
                    "dtb",
                    "dtbo",
                ]:
                    imgtype = input(
                        "  手动打包所有分区格式为：[1]ext4 [2]erofs [3]f2fs:"
                    )
                    if imgtype == "1":
                        imgtype = "ext"
                    elif imgtype == "2":
                        imgtype = "erofs"
                    else:
                        imgtype = "f2fs"

                    if input("  输出文件格式[1]raw [2]sparse:") == "2":
                        israw = False

                print_yellow(f"打包{parts[int(filed)]}")
                if types[int(filed)] == "bootimg":
                    dboot(
                        project_dir + os.sep + parts[int(filed)],
                        project_dir + os.sep + parts[int(filed)] + ".img",
                    )
                elif types[int(filed)] == "dtb":
                    makedtb(parts[int(filed)], project_dir)
                elif types[int(filed)] == "dtbo":
                    makedtbo(parts[int(filed)], project_dir)
                else:
                    pack_img(parts[int(filed)], imgtype, israw)
            else:
                wrap_red("Input error!")
        else:
            wrap_red("Input error!")
        input("任意按钮继续")
        pack_choo()


def dboot(infile, orig):
    flag = ""
    if not os.path.exists(infile):
        print(f"Cannot Find {infile}...")
        return
    if os.path.isdir(infile + os.sep + "ramdisk"):
        try:
            os.chdir(infile + os.sep + "ramdisk")
        except Exception as e:
            print("Ramdisk Not Found.. %s" % e)
            return

        os.system(
            'busybox ash -c "find | sed 1d | %s -H newc -R 0:0 -o -F ../ramdisk-new.cpio"'
            % {tikpath.get_binary_path("cpio")},
        )
        os.chdir(infile)
        with open("comp", "r", encoding="utf-8") as compf:
            comp = compf.read()
        print("Compressing:%s" % comp)
        if comp != "unknow":
            if os.system("magiskboot compress=%s ramdisk-new.cpio" % comp) != 0:
                print("Pack Ramdisk Fail...")
                os.remove("ramdisk-new.cpio")
                return
            else:
                print("Pack Ramdisk Successful..")
                try:
                    os.remove("ramdisk.cpio")
                except (Exception, BaseException):
                    ...
                os.rename("ramdisk-new.cpio.%s" % comp.split("_")[0], "ramdisk.cpio")
        else:
            print("Pack Ramdisk Successful..")
            os.remove("ramdisk.cpio")
            os.rename("ramdisk-new.cpio", "ramdisk.cpio")
        if comp == "cpio":
            flag = "-n"
    else:
        os.chdir(infile)
    if os.system("magiskboot repack %s %s" % (flag, orig)) != 0:
        print("Pack boot Fail...")
        return
    else:
        os.remove(orig)
        os.rename(infile + os.sep + "new-boot.img", orig)
        try:
            shutil.rmtree(infile)
        except (Exception, BaseException):
            print("删除错误...")
        print("Pack Successful...")


def unpackboot(file, project):
    name = os.path.basename(file).replace(".img", "")
    shutil.rmtree(project + os.sep + name)
    os.makedirs(project + os.sep + name)
    os.chdir(project + os.sep + name)
    if os.system("magiskboot unpack -h %s" % file) != 0:
        print("Unpack %s Fail..." % file)
        shutil.rmtree(project + os.sep + name)
        return
    if os.access(project + os.sep + name + os.sep + "ramdisk.cpio", os.F_OK):
        comp = gettype(project + os.sep + name + os.sep + "ramdisk.cpio")
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


def undtb(project, infile):
    dtbdir = project + os.sep + os.path.basename(infile).split(".")[0]
    shutil.rmtree(dtbdir)
    if not os.path.exists(dtbdir):
        os.makedirs(dtbdir)
    extract_dtb.extract_dtb.split(
        Namespace(filename=infile, output_dir=dtbdir + os.sep + "dtb_files", extract=1)
    )
    print_yellow("正在反编译dtb...")
    for i in track(os.listdir(dtbdir + os.sep + "dtb_files")):
        if i.endswith(".dtb"):
            name = i.split(".")[0]
            dtb = os.path.join(dtbdir, "dtb_files", name + ".dtb")
            dts = os.path.join(dtbdir, "dtb_files", name + ".dts")
            os.system(f"dtc -@ -I dtb -O dts {dtb} -o {dts}")
    open(
        project
        + os.sep
        + os.sep
        + "config"
        + os.sep
        + "dtbinfo_"
        + os.path.basename(infile).split(".")[0],
        "w",
    ).close()
    print_green("反编译完成!")


def makedtb(sf, project):
    dtbdir = project + os.sep + sf
    shutil.rmtree(dtbdir + os.sep + "new_dtb_files")
    os.makedirs(dtbdir + os.sep + "new_dtb_files")
    for dts_files in os.listdir(dtbdir + os.sep + "dtb_files"):
        new_dtb_files = dts_files.split(".")[0]
        print_yellow(f"正在回编译{dts_files}为{new_dtb_files}.dtb")
        dtb_ = dtbdir + os.sep + "dtb_files" + os.sep + dts_files
        if (
            os.system(
                f'dtc -@ -I "dts" -O "dtb" "{dtb_}" -o "{dtbdir + os.sep}new_dtb_files{os.sep}{new_dtb_files}.dtb"'
            )
            != 0
        ):
            wrap_red("回编译dtb失败")
    with open(project + os.sep + "TI_out" + os.sep + sf, "wb") as sff:
        for dtb in os.listdir(dtbdir + os.sep + "new_dtb_files"):
            if dtb.endswith(".dtb"):
                with open(os.path.abspath(dtb), "rb") as f:
                    sff.write(f.read())
    print_green("回编译完成！")


def undtbo(project, infile):
    dtbodir = project + os.sep + os.path.basename(infile).split(".")[0]
    open(
        project
        + os.sep
        + "config"
        + os.sep
        + "dtboinfo_"
        + os.path.basename(infile).split(".")[0],
        "w",
    ).close()
    shutil.rmtree(dtbodir)
    if not os.path.exists(dtbodir + os.sep + "dtbo_files"):
        os.makedirs(dtbodir + os.sep + "dtbo_files")
        try:
            os.makedirs(dtbodir + os.sep + "dts_files")
        except (Exception, BaseException):
            ...
    print_yellow("正在解压dtbo.img")
    mkdtboimg.dump_dtbo(infile, dtbodir + os.sep + "dtbo_files" + os.sep + "dtbo")
    for dtbo_files in os.listdir(dtbodir + os.sep + "dtbo_files"):
        if dtbo_files.startswith("dtbo."):
            dts_files = dtbo_files.replace("dtbo", "dts")
            print_yellow(f"正在反编译{dtbo_files}为{dts_files}")
            dtbofiles = dtbodir + os.sep + "dtbo_files" + os.sep + dtbo_files
            command = [
                tikpath.get_binary_path("dtc"),
                "-@",
                "-I dtb",
                "-O dts",
                dtbofiles,
                f"-o {os.path.join(dtbodir, 'dts_files', dts_files)}",
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
                wrap_red(f"反编译{dtbo_files}失败！")
                return
    print_green("完成！")
    shutil.rmtree(dtbodir + os.sep + "dtbo_files")


def makedtbo(sf, project):
    dtbodir = project + os.sep + os.path.basename(sf).split(".")[0]
    if os.path.exists(dtbodir + os.sep + "new_dtbo_files"):
        shutil.rmtree(dtbodir + os.sep + "new_dtbo_files")
    if os.path.exists(project + os.sep + os.path.basename(sf).split(".")[0] + ".img"):
        os.remove(project + os.sep + os.path.basename(sf).split(".")[0] + ".img")
    os.makedirs(dtbodir + os.sep + "new_dtbo_files")
    for dts_files in os.listdir(dtbodir + os.sep + "dts_files"):
        new_dtbo_files = dts_files.replace("dts", "dtbo")
        print_yellow(f"正在回编译{dts_files}为{new_dtbo_files}")
        dtb_ = dtbodir + os.sep + "dts_files" + os.sep + dts_files
        command = [
            tikpath.get_binary_path("dtc"),
            "-@",
            "-I dts",
            "-O dtb",
            dtb_,
            f"-o {dtbodir + os.sep + 'new_dtbo_files' + os.sep + new_dtbo_files}",
        ]
        subprocess.call(
            " ".join(command),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print_yellow("正在生成dtbo.img...")
    list_: list[str] = []
    for b in os.listdir(dtbodir + os.sep + "new_dtbo_files"):
        if b.startswith("dtbo."):
            list_.append(dtbodir + os.sep + "new_dtbo_files" + os.sep + b)
    list_ = sorted(list_, key=lambda x: int(float(x.rsplit(".", 1)[1])))
    try:
        mkdtboimg.create_dtbo(
            project + os.sep + os.path.basename(sf).split(".")[0] + ".img", list_, 4096
        )
    except (Exception, BaseException):
        wrap_red(f"{os.path.basename(sf).split('.')[0]}.img生成失败!")
    else:
        print_green(f"{os.path.basename(sf).split('.')[0]}.img生成完毕!")


def pack_img(
    img_name: str,
    img_type: str,
    israw: bool,
):
    """
    打包镜像的核心方法
    """
    project_dir = tikpath.PROJECT_PATH
    # 根据镜像名称获取对应的配置文件
    file_contexts = tikpath.get_file_contexts(img_name)
    fs_config = tikpath.get_fs_config(img_name)
    # 时间戳
    utc = int(time.time())
    # 生成路径与待打包的内容
    out_img = tikpath.get_out_img_path(img_name)
    in_files = tikpath.get_input_for_image(img_name)

    img_size0 = dirsize(
        in_files, 1, 3, project_dir + os.sep + "dynamic_partitions_op_list"
    ).rsize_v

    # patch file_contexts and fs_config
    fspatch.main(in_files, fs_config)
    utils.remove_duplicate_lines(fs_config)

    if os.path.exists(file_contexts):
        contextpatch.main(in_files, file_contexts)
        utils.remove_duplicate_lines(file_contexts)

    size = img_size0 / int(SetUtils.BLOCKSIZE)
    size = int(size)

    if img_type == "erofs":
        os.system(
            rf"{tikpath.get_binary_path('mkfs.erofs')} \
                -z{SetUtils.erofslim} \
                -T {utc} \
                --mount-point=/{img_name} \
                --fs-config-file={fs_config} \
                --file-contexts={file_contexts} \
                {out_img} \
                {in_files}"
        )

    elif img_type == "f2fs":
        size_f2fs = (54 * 1024 * 1024) + img_size0
        size_f2fs = int(size_f2fs * 1.15) + 1
        with open(out_img, "wb") as f:
            f.truncate(size_f2fs)
        os.system(
            rf"{tikpath.get_binary_path('mkfs.f2fs')} {out_img} \
                -O extra_attr \
                -O inode_checksum \
                -O sb_checksum \
                -O compression \
                -f"
        )
        os.system(
            rf"{tikpath.get_binary_path('sload.f2fs')} \
                -f {in_files} \
                -C {fs_config} \
                -s {file_contexts} \
                -t /{img_name} \
                {out_img} \
                -c"
        )

    else:
        os.system(
            rf"{tikpath.get_binary_path('mke2fs')} \
                -O ^has_journal \
                -L {img_name} \
                -I 256 \
                -M /{img_name} \
                -m 0 \
                -t ext4 \
                -b {SetUtils.BLOCKSIZE} \
                {out_img} \
                {size}"
        )
        os.system(
            rf"{tikpath.get_binary_path('e2fsdroid')} -e \
                -T {utc} \
                -S {file_contexts} \
                -C {fs_config} \
                -a /{img_name} \
                -f {in_files} \
                {out_img}"
        )

    if not israw:
        ImageConverter(out_img).img2simg()


def packsuper(project):
    if os.path.exists(project + os.sep + "TI_out" + os.sep + "super.img"):
        os.remove(project + os.sep + "TI_out" + os.sep + "super.img")
    if not os.path.exists(project + os.sep + "super"):
        os.makedirs(project + os.sep + "super")
    cls()
    wrap_red(f"请将需要打包的分区镜像放置于{project}{os.sep}super中！")
    supertype = input("请输入Super类型：[1]A_only [2]AB [3]V-AB-->")
    if supertype == "3":
        supertype = "VAB"
    elif supertype == "2":
        supertype = "AB"
    else:
        supertype = "A_only"
    isreadonly = input("是否设置为只读分区？[1/0]")
    ifsparse = input("是否打包为sparse镜像？[1/0]")
    if not os.listdir(project + os.sep + "super"):
        print("您似乎没有要打包的分区，要移动下列分区打包吗：")
        move_list = []
        for i in os.listdir(project + os.sep + "TI_out"):
            if os.path.isfile(os.path.join(project + os.sep + "TI_out", i)):
                if gettype(os.path.join(project + os.sep + "TI_out", i)) in [
                    "ext",
                    "erofs",
                ]:
                    if i.startswith("dsp"):
                        continue
                    move_list.append(i)
        print("\n".join(move_list))
        if input("确定操作吗[Y/N]") in ["Y", "y", "1"]:
            for i in move_list:
                shutil.move(
                    os.path.join(project + os.sep + "TI_out", i),
                    os.path.join(project + os.sep + "super", i),
                )
    tool_auto_size = (
        sum(
            [
                os.path.getsize(os.path.join(project + os.sep + "super", p))
                for p in os.listdir(project + os.sep + "super")
                if os.path.isfile(os.path.join(project + os.sep + "super", p))
            ]
        )
        + 409600
    )
    tool_auto_size = versize(tool_auto_size)
    checkssize = input(
        f"请设置Super.img大小:[1]9126805504 [2]10200547328 [3]16106127360 [4]工具推荐：{tool_auto_size} [5]自定义"
    )
    if checkssize == "1":
        supersize = 9126805504
    elif checkssize == "2":
        supersize = 10200547328
    elif checkssize == "3":
        supersize = 16106127360
    elif checkssize == "4":
        supersize = tool_auto_size
    else:
        supersize = input("请输入super分区大小（字节数）:")
    print_yellow("打包到TI_out/super.img...")
    insuper(
        project + os.sep + "super",
        project + os.sep + "TI_out" + os.sep + "super.img",
        supersize,
        supertype,
        ifsparse,
        isreadonly,
    )


def insuper(imgdir, outputimg, ssize, stype, sparsev, isreadonly):
    attr = "readonly" if isreadonly == "1" else "none"
    group_size_a = 0
    group_size_b = 0
    for root, dirs, files in os.walk(imgdir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
                os.remove(file_path)
    superpa = (
        f"--metadata-size {SetUtils.metadatasize} --super-name {SetUtils.supername} "
    )
    if sparsev == "1":
        superpa += "--sparse "
    if stype == "VAB":
        superpa += "--virtual-ab "
    superpa += f"-block-size={SetUtils.SBLOCKSIZE} "
    for imag in os.listdir(imgdir):
        if imag.endswith(".img"):
            image = imag.replace("_a.img", "").replace("_b.img", "").replace(".img", "")
            if (
                f"partition {image}:{attr}" not in superpa
                and f"partition {image}_a:{attr}" not in superpa
            ):
                if stype in ["VAB", "AB"]:
                    if os.path.isfile(
                        imgdir + os.sep + image + "_a.img"
                    ) and os.path.isfile(imgdir + os.sep + image + "_b.img"):
                        img_sizea = os.path.getsize(imgdir + os.sep + image + "_a.img")
                        img_sizeb = os.path.getsize(imgdir + os.sep + image + "_b.img")
                        group_size_a += img_sizea
                        group_size_b += img_sizeb
                        superpa += f"--partition {image}_a:{attr}:{img_sizea}:{SetUtils.super_group}_a --image {image}_a={imgdir}{os.sep}{image}_a.img --partition {image}_b:{attr}:{img_sizeb}:{SetUtils.super_group}_b --image {image}_b={imgdir}{os.sep}{image}_b.img "
                    else:
                        if not os.path.exists(
                            imgdir + os.sep + image + ".img"
                        ) and os.path.exists(imgdir + os.sep + image + "_a.img"):
                            os.rename(
                                imgdir + os.sep + image + "_a.img",
                                imgdir + os.sep + image + ".img",
                            )

                        img_size = os.path.getsize(imgdir + os.sep + image + ".img")
                        group_size_a += img_size
                        group_size_b += img_size
                        superpa += f"--partition {image}_a:{attr}:{img_size}:{SetUtils.super_group}_a --image {image}_a={imgdir}{os.sep}{image}.img --partition {image}_b:{attr}:0:{SetUtils.super_group}_b "
                else:
                    if not os.path.exists(
                        imgdir + os.sep + image + ".img"
                    ) and os.path.exists(imgdir + os.sep + image + "_a.img"):
                        os.rename(
                            imgdir + os.sep + image + "_a.img",
                            imgdir + os.sep + image + ".img",
                        )

                    img_size = os.path.getsize(imgdir + os.sep + image + ".img")
                    superpa += f"--partition {image}:{attr}:{img_size}:{SetUtils.super_group} --image {image}={imgdir}{os.sep}{image}.img "
                    group_size_a += img_size
                print(f"已添加分区:{image}")
    supersize = ssize
    if not supersize:
        supersize = group_size_a + 4096000
    superpa += f"--device super:{supersize} "
    if stype in ["VAB", "AB"]:
        superpa += "--metadata-slots 3 "
        superpa += f" --group {SetUtils.super_group}_a:{supersize} "
        superpa += f" --group {SetUtils.super_group}_b:{supersize} "
    else:
        superpa += "--metadata-slots 2 "
        superpa += f" --group {SetUtils.super_group}:{supersize} "
    superpa += f"{SetUtils.fullsuper} {SetUtils.autoslotsuffixing} --output {outputimg}"
    (
        wrap_red("创建super.img失败！")
        if os.system(f"lpmake {superpa}") != 0
        else print_green("成功创建super.img!")
    )


def unpack(file, info, project):
    if not os.path.exists(file):
        file = os.path.join(project, file)

    print_yellow(f"[{info}]解包{os.path.basename(file)}中...")

    if info == "sparse":
        simg2img(os.path.join(project, file))
        unpack(file, gettype(file), project)
    elif info == "dtbo":
        undtbo(project, os.path.abspath(file))
    elif info == "dtb":
        undtb(project, os.path.abspath(file))
    elif info == "img":
        unpack(file, gettype(file), project)
    elif info == "ext":
        ImageUnpacker(file).unpack_ext()
    elif info == "erofs":
        ImageUnpacker(file).unpack_erofs()
    elif info == "f2fs" and os.name == "posix":
        ImageUnpacker(file).unpack_f2fs()
    elif info == "super":
        lpunpack.unpack(os.path.abspath(file), project)
        for v in os.listdir(project):
            if os.path.isfile(project + os.sep + v):
                if os.path.getsize(project + os.sep + v) == 0:
                    os.remove(project + os.sep + v)
                else:
                    if os.path.exists(
                        project + os.sep + v.replace("_a", "")
                    ) or os.path.exists(project + os.sep + v.replace("_b", "")):
                        continue
                    if v.endswith("_a.img"):
                        shutil.move(
                            project + os.sep + v, project + os.sep + v.replace("_a", "")
                        )
                    elif v.endswith("_b.img"):
                        shutil.move(
                            project + os.sep + v, project + os.sep + v.replace("_b", "")
                        )
    elif info in ["boot", "vendor_boot"]:
        unpackboot(os.path.abspath(file), project)
    else:
        wrap_red("未知格式！")
