import json
import os
import shutil
import sys

import requests

from src.custom import banner
import custom
import tikpath
from src.util import utils
from src.util.api import cls, dir_has
from src.image.image import ImageUnpacker, ImagePacker, MyImage
from src.util.log import *
from src.util.utils import JsonUtil, simg2img, versize, SetUtils, TypeDetector


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


class UserInterface:
    """
    与用户交互的主循环
    """

    printer = utils.MyPrinter()

    def __init__(self):
        # skip them when recognize projects
        self.WHITELIST: list[str] = ["bin", "ksu-derviers", "__pycache__", "config"]
        self.user_projects: dict[str, str] = self.get_user_projects()

    def user_continue(self):
        self.printer.print_yellow("任意按钮继续")
        input("")

    def get_user_projects(self) -> dict[str, str]:
        """获取用户的所有现存项目"""
        project_num = 1
        projects = {}

        for project_dir in os.listdir(tikpath.TIK_PATH):

            # neglect the directories in the whitelist
            if project_dir in self.WHITELIST or project_dir.startswith("."):
                continue

            if os.path.isdir(os.path.join(tikpath.TIK_PATH, project_dir)):
                # add key-pair into the dict
                projects.update({str(project_num): project_dir})
                project_num += 1

        return projects

    def delete_project(self):
        if (
            delete_index := input("  请输入你要删除的项目序号:").strip()
        ) in self.user_projects.keys():
            if input(f"  确认删除{self.user_projects[delete_index]}？[1/0]") == "1":
                shutil.rmtree(
                    os.path.join(tikpath.TIK_PATH, self.user_projects[delete_index])
                )
            else:
                print_red("取消删除")
        else:
            print_red("  项目不存在！")
            self.user_continue()

    def create_project(self):
        new_project_name = input("请输入项目名称(非中文)：").strip()
        if new_project_name:
            if os.path.exists(os.path.join(tikpath.TIK_PATH, new_project_name)):
                wrap_red(f"项目已存在！请更换名称")
                self.user_continue()
            os.makedirs(os.path.join(tikpath.TIK_PATH, new_project_name, "config"))
            os.makedirs(os.path.join(tikpath.TIK_PATH, new_project_name, "TI_out"))
            print_green(f"项目{new_project_name}创建成功！")
            self.user_projects = self.get_user_projects()
        else:
            print_red("  Input error!")
            self.user_continue()

    def main(self):
        # clear the screen and show the banner
        cls()
        greet()

        self.printer.print_white(" > 项目列表\n")
        self.printer.print_red("   [00]  删除项目\n")
        self.printer.print_green("   [0]  新建项目\n")

        # list all the projects
        for project_num, project_dir in self.get_user_projects().items():
            self.printer.print_white(f"   [{project_num}]  {project_dir}\n")

        self.printer.print_white("  --------------------------------------")
        self.printer.print_yellow("  [77] 设置  [88] 退出\n")

        op_pro = input("  请输入序号：")

        match op_pro:
            case "00":
                self.delete_project()
            case "0":
                self.create_project()
            case "88":
                cls()
                print_green("\n感谢使用TI-KITCHEN5, 再见！")
                sys.exit(0)
            case _ if op_pro.isdigit():
                if op_pro in self.user_projects.keys():
                    # initialize the project
                    project_name = self.user_projects.get(op_pro, "")
                    tikpath.set_project(project_name)
                    self.project()
                else:
                    print_red("  Input error!")
                    self.user_continue()
            case _:
                print_red("  Input error!")
                self.user_continue()

        # back to the main menu
        self.main()

    def project(self):
        cls()
        project_name = tikpath.get_project_name()
        project_root = tikpath.PROJECT_PATH

        self.printer.print_red("> 项目菜单\n")
        (
            print(f"  项目：{project_name}\033[91m(不完整)\033[0m\n")
            if not os.path.exists(os.path.abspath("../config"))
            else print(f"  项目：{project_name}\n")
        )

        # create the necessary directories if not exists
        os.makedirs(project_root + os.sep + "TI_out", exist_ok=True)
        os.makedirs(project_root + os.sep + "config", exist_ok=True)

        self.printer.print_yellow("    1> 解包菜单     2> 打包菜单\n")
        self.printer.print_blue("    3> 定制功能     4> 精简分区\n")
        self.printer.print_green("    00> 返回主页    88> 退出TIK\n")

        op_menu = input("    请输入编号: ")

        match op_menu:
            case "00":
                self.main()
                return
            case "1":
                self.unpack_choo()
            case "2":
                self.pack_choo()
            case "3":
                self.custom_rom()
            case "4":
                custom.slim_partition()
            case "88":
                cls()
                print_green("\n感谢使用TI-KITCHEN5,再见！")
                sys.exit(0)
            case _:
                wrap_red("   Input error!")
                self.user_continue()

        self.project()

    def custom_rom(self):
        cls()

        print(" \033[31m>定制菜单 \033[0m\n")
        print(f"  项目：{tikpath.get_project_name()}\n")
        print("\033[33m    0> 返回上级  1> xxxx\033[0m\n")
        print("\033[33m    2> KSU修补   3> Apatch修补\033[0m\n")
        print("\033[33m    4> 去除avb   5> 去除data加密\033[0m\n")
        op_menu = input("    请输入编号: ")
        if op_menu == "0":
            return
        elif op_menu == "1":
            pass
        elif op_menu == "5":
            wrap_red("暂未支持")
            ...
        else:
            wrap_red("   Input error!")
            self.user_continue()
        self.custom_rom()

    @staticmethod
    def get_imgs_can_be_unpacked() -> list[MyImage]:
        ret: list[MyImage] = []

        for img in os.listdir(tikpath.PROJECT_PATH):
            if img.endswith(".img"):
                ret.append(MyImage(img))
        return ret

    def unpack_choo(self):
        """解包前端"""
        cls()
        project_dir = tikpath.PROJECT_PATH

        self.printer.print_red(" > 分解 \n")

        num_imgpath = {}

        if dir_has(project_dir, ".img"):
            imgs = self.get_imgs_can_be_unpacked()
            print("\033[33m [Img] 文件\033[0m\n")
            for n, img in enumerate(imgs, 1):
                self.printer.print_white(f"   [{n}]- {img.img_name} <{img.img_type}>\n")
                num_imgpath.update({str(n): img.img_path})

        print("\n\033[33m  [00] 返回  [77] 循环解包  \033[0m")
        print("  --------------------------------------")
        op = input("  请输入对应序号：")

        match op:
            case "00":
                self.project()
            case _ if op.isdigit():
                ImageUnpacker(num_imgpath.get(op)).unpack()

        input("任意按钮继续")
        self.unpack_choo()

    @staticmethod
    def get_parts_can_be_packing() -> dict:
        """获取项目内可以被打包的镜像"""
        parts_info = tikpath.get_parts_info()
        return JsonUtil.read(parts_info)

    def pack_choo(self):
        """打包前端"""
        cls()

        project_dir = tikpath.PROJECT_PATH
        self.printer.print_red(" > 打包 \n")

        parts = self.get_parts_can_be_packing()

        # 展示所有可打包分区
        num_imgname = {}
        for n, (k, v) in enumerate(parts.items(), 1):
            self.printer.print_green(f"{n}. {k} <{v}>\n")
            num_imgname.update({str(n): k})

        self.printer.print_green("\n\033[33m [66] 打包Super [00]返回\033[0m")
        self.printer.print_white("  --------------------------------------")
        op = input("  请输入对应序号：")

        match op:
            case "00":
                return

            case "66":
                packsuper(project_dir)

            case _ if op.isdigit():
                img_name = num_imgname.get(op, "")
                content_path = os.path.join(tikpath.PROJECT_PATH, img_name)

                packer = ImagePacker(content_path)
                img_type = packer.get_img_type()

                match img_type:
                    case "dtbo":
                        packer.pack_dtbo()
                        self.user_continue()
                        self.pack_choo()
                    case "vendor_boot":
                        packer.pack_vendor_boot()
                        self.user_continue()
                        self.pack_choo()

                imgtype = input("  打包分区格式为：[1]ext4 [2]erofs [3]f2fs:")
                match imgtype:
                    case "1":
                        packer.pack_ext()
                    case "2":
                        packer.pack_erofs()
                    case "3":
                        packer.pack_f2fs()

                if input("  输出文件格式[1]raw [2]sparse:") == "2":
                    packer.convert2simg()

        self.pack_choo()


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
            % {tikpath.get_binary("cpio")},
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
                if TypeDetector(
                    os.path.join(project + os.sep + "TI_out", i)
                ).get_type() in [
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
    pass
