#!/usr/bin/env python
import os
import json
import sys

from api import cls, dir_has
import time
import platform as plat
import shutil
from utils import gettype
import requests

LOCALDIR = os.getcwd()
binner = LOCALDIR + os.sep + "bin"
setfile = LOCALDIR + os.sep + "bin" + os.sep + "settings.json"
tempdir = LOCALDIR + os.sep + 'TEMP'
tiklog = LOCALDIR + os.sep + f'TIK4_{time.strftime("%Y%m%d")}.log'
AIK = binner + os.sep + 'AIK'
MBK = binner + os.sep + 'AIK'
platform = plat.machine()
ostype = plat.system()
PIP_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple/"
ebinner = binner + os.sep + ostype + os.sep + platform
dtc = ebinner + os.sep + "dtc"
mkdtimg_tool = binner + os.sep + "mkdtboimg.py"


def yecho(info): print(f"\033[36m[{time.strftime('%H:%M:%S')}]{info}\033[0m")


def ywarn(info): print(f"\033[31m{info}\033[0m")


def ysuc(info): print(f"\033[32m[{time.strftime('%H:%M:%S')}]{info}\033[0m")


def rmdire(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def getsize(file):
    return os.path.getsize(file)


def cleantemp():
    rmdire(tempdir)
    os.mkdir(tempdir)


if os.name == 'posix':
    os.system(f'chmod -R 777 {binner}')


def getprop(name, path):
    with open(path, 'r') as prop:
        for s in prop.readlines():
            if s[:1] == '#':
                continue
            if name in s:
                return s.strip().split('=')[1]


class set_utils:
    def __init__(self, path):
        self.path = path

    def load_set(self):
        with open(self.path, 'r') as ss:
            data = json.load(ss)
            for v in data:
                setattr(self, v, data[v])

    def change(self, name, value):
        with open(self.path, 'r') as ss:
            data = json.load(ss)
        with open(self.path, 'w', encoding='utf-8') as ss:
            data[name] = value
            json.dump(data, ss, ensure_ascii=False, indent=4)
        self.load_set()


settings = set_utils(setfile)
settings.load_set()


class setting:
    def settings4(self):
        cls()
        print('''
        \033[33m  > 打包设置 \033[0m
           1>Brotli 压缩等级\n
           2>[EXT4] Size处理\n
           3>[EXT4] 打包工具\n
           4>[EXT4]打包RO/RW\n
           5>[Erofs]压缩方式\n
           6>[EXT4]UTC时间戳\n
           7>[EXT4]InodeSize\n
           8>[Img]创建sparse\n
           9>[~4]Img文件系统\n
           10> 补全fs_config\n
           11>默认BOOT打包Tool\n
           12>返回上一级菜单
           --------------------------
        ''')
        op_pro = input("   请输入编号: ")
        if op_pro == "12":
            return 1
        try:
            getattr(self, 'packset%s' % op_pro)()
            self.settings5()
        except AttributeError:
            print("Input error!")
            self.settings4()

    def settings5(self):
        cls()
        print('''
        \033[33m  > 动态分区设置 \033[0m
           1> dynamic_partitions簇名\n
           2> [Metadata]元数据插槽数\n
           3> [Metadata]最大保留Size\n
           4> [分区] 默认扇区/块大小\n
           5> [Super] 指定/block大小\n
           6> [Super] 更改物理分区名\n
           7> [Super] 更改逻辑分区表\n
           8> [Super]强制烧写完整Img\n
           9> [Super] 标记分区槽后缀\n
           10>[Payload]靶定HeaderVer\n
           11>返回上一级菜单
           --------------------------
        ''')
        op_pro = input("   请输入编号: ")
        if op_pro == "11":
            return 1
        elif op_pro == '10':
            input('维护中。。。')
        try:
            getattr(self, 'dyset%s' % op_pro)()
            self.settings5()
        except AttributeError:
            print("Input error!")
            self.settings5()

    def settings2(self):
        print(f"修改安卓端在内置存储识别ROM的路径。当前为/sdcard/{settings.mydir}")
        mydir = input('   请输入文件夹名称(英文):')
        if mydir:
            settings.change('mydir', mydir)

    def settings3(self):
        if os.name == "posix":
            for age in ['python3', 'simg2img', 'img2simg', 'cpio', 'sed', 'libnss3-tools', 'python3-pip', 'brotli',
                        'curl', 'bc', 'cpio', 'default-jre', 'android-sdk-libsparse-utils', 'openjdk-11-jre', 'aria2',
                        'p7zip-full']:
                print(f"\033[31m  修复安装{age}\033[0m")
                os.system(f"apt-get install {age} -y")
                print(f"\033[36m  {age}已安装\033[0m")
        else:
            print("非LINUX，无法修复")

    def settings6(self):
        print(f"  打包时ROM作者为：{settings.Romer}")
        Romer = input("  请输入（无特殊字符）: ")
        if Romer:
            settings.change('Romer', Romer)

    def settings7(self):
        print("  首页banner: [1]TIK3 [2]爷 [3]电摇嘲讽 [4]镰刀斧头 [5]镰刀斧头(大) [6]TIK2旧 ")
        banner = input("  请输入序号: ")
        if banner.isdigit():
            if 0 < int(banner) < 7:
                settings.change('banner', banner)

    def settings8(self):
        plugromlit = input("  设置区分ROM/Plug的Size界限[1]125829120 [2]自定义: ")
        if plugromlit == '2':
            plugromlit = input("  请输入：")
            if plugromlit.isdigit():
                settings.change('plugromlit', plugromlit)
        else:
            settings.change('plugromlit', '125829120')

    def packset1(self):
        print(f"  调整brotli压缩等级（整数1-9，级别越高，压缩率越大，耗时越长），当前为：{settings.brcom}级")
        brcom = input("  请输入（1-9）: ")
        if brcom.isdigit():
            if 0 < int(brcom) < 10:
                settings.change('brcom', brcom)

    def packset2(self):
        sizediy = input("  打包Ext镜像大小[1]动态最小 [2]手动改: ")
        if sizediy == '2':
            settings.change('diysize', '1')
        else:
            settings.change('diysize', '')

    def packset3(self):
        print("  ext4打包方案: [1]make_ext4fs [2]mke2fs+e2fsdroid ")
        pack_op = input("  请输入序号: ")
        if pack_op == '1':
            settings.change('pack_e2', '0')
        else:
            settings.change('pack_e2', '1')

    def packset4(self):
        extrw = input("  打包EXT是否可读[1]RW [2]RO: ")
        if extrw == '2':
            settings.change('ext4rw', '')
        else:
            settings.change('ext4rw', '-s')

    def packset5(self):
        erofslim = input("  选择erofs压缩方式[1]是 [2]否: ")
        if erofslim == '1':
            erofslim = input("  选择erofs压缩方式：lz4/lz4hc和压缩等级[1-9](数字越大耗时更长体积更小) 例如 lz4hc,8: ")
            if erofslim:
                settings.change("erofslim", erofslim)
        else:
            settings.change("erofslim", '')

    def packset6(self):
        utcstamp = input("  设置打包UTC时间戳[1]live [2]自定义: ")
        if utcstamp == "2":
            utcstamp = input("  请输入: ")
            if utcstamp.isdigit():
                settings.change('utcstamp', utcstamp)
        else:
            settings.change('utcstamp', '')

    def packset8(self):
        print("  Img是否打包为sparse(压缩体积)[1/0]")
        ifpsparse = input("  请输入序号: ")
        if ifpsparse == '1':
            settings.change('pack_sparse', '1')
        elif ifpsparse == '0':
            settings.change('pack_sparse', '0')

    def packset7(self):
        inodesize = input("  设置EXT分区inode-size: ")
        if inodesize:
            settings.change('inodesize', inodesize)

    def packset9(self):
        typediy = input("  打包镜像格式[1]同解包格式 [2]可选择: ")
        if typediy == '2':
            settings.change('diyimgtype', '1')
        else:
            settings.change('diyimgtype', '')

    def packset10(self):
        pack_op = input("  是否自动补全fs_config[谨慎!]: [1]是 [2]否\n请输入序号: ")
        if pack_op == '2':
            settings.change('auto_fsconfig', '0')
        else:
            settings.change('auto_fsconfig', '1')

    def packset11(self):
        chboottool = input("  默认Boot解、打包工具[1]AndroidImageKitchen [2]MagiskBootKitchen: ")
        if chboottool == '1':
            settings.change('default_boot_tool', 'AIK')
        else:
            settings.change('default_boot_tool', 'MBK')

    def dyset1(self):
        super_group = input(f"  当前动态分区簇名/GROUPNAME：{settings.super_group}\n  请输入（无特殊字符）: ")
        if super_group:
            settings.change('super_group', super_group)

    def dyset2(self):
        slotnumber = input("  强制Metadata插槽数：[2] [3]: ")
        if slotnumber == '3':
            settings.change('slotnumber', '3')
        else:
            settings.change('slotnumber', '2')

    def dyset3(self):
        metadatasize = input("  设置metadata最大保留size(默认为65536，至少512) ")
        if metadatasize:
            settings.change('metadatasize', metadatasize)

    def dyset4(self):
        BLOCKSIZE = input(f"  分区打包扇区/块大小：{settings.BLOCKSIZE}\n  请输入: ")
        if BLOCKSIZE:
            settings.change('BLOCKSIZE', BLOCKSIZE)

    def dyset5(self):
        SBLOCKSIZE = input(f"  分区打包扇区/块大小：{settings.SBLOCKSIZE}\n  请输入: ")
        if SBLOCKSIZE:
            settings.change('SBLOCKSIZE', SBLOCKSIZE)

    def dyset6(self):
        supername = input(f'  当前动态分区物理分区名(默认super)：{settings.supername}\n  请输入（无特殊字符）: ')
        if supername:
            settings.change('supername', supername)

    def dyset7(self):
        superpart_list = input(f'  当前动态分区内逻辑分区表：{settings.superpart_list}\n  请输入（无特殊字符）: ')
        if superpart_list:
            settings.change('superpart_list', superpart_list)

    def dyset8(self):
        iffullsuper = input("  是否创建强制刷入的Full镜像？[1/0]")
        if not iffullsuper == '1':
            settings.change('fullsuper', '')
        else:
            settings.change('fullsuper', '-F')

    def dyset9(self):
        autoslotsuffix = input("  是否标记需要Slot后缀的分区？[1/0]")
        if not autoslotsuffix == '1':
            settings.change('autoslotsuffixing', '')
        else:
            settings.change('autoslotsuffixing', '-x')

    def __init__(self):
        cls()
        print('''
    \033[33m  > 设置 \033[0m
       1> 待定
       2>[Droid]存储ROM目录
       3>[修复]工具部分依赖
       4>[打包]相关细则设置
       5>[动态分区]相关设置
       6>自定义 ROM作者信息
       7>自定义 首页Banner
       8>修改Plug/ROM限Size
       9>返回主页
       --------------------------
    ''')
        op_pro = input("   请输入编号: ")
        if op_pro == "9":
            return
        try:
            getattr(self, 'settings%s' % op_pro)()
            self.__init__()
        except AttributeError as e:
            print(f"Input error!{e}")
            self.__init__()


def promenu():
    gs = 1
    projects = {}
    cls()
    try:
        content = json.loads(requests.get('https://v1.jinrishici.com/all.json').content.decode())
        shiju = content['content']
        fr = content['origin']
        another = content['author']
    except:
        gs = 0
    with open(binner + os.sep + 'banners' + os.sep + settings.banner, 'r') as banner:
        print(f'\033[31m {banner.read()} \033[0m')
    print("\033[92;44m Beta Edition \033[0m")
    if gs == 1:
        print(f"\033[36m “{shiju}”")
        print(f"\033[36m---{another}《{fr}》\033[0m\n")
    print(" >\033[33m 项目列表 \033[0m\n")
    print("\033[31m   [00]  删除项目\033[0m\n")
    print("   [0]  新建项目\n")
    pro = 0
    del_ = 0
    if os.listdir(LOCALDIR + os.sep):
        for pros in os.listdir(LOCALDIR + os.sep):
            if pros.startswith('TI_') and os.path.isdir(LOCALDIR + os.sep + pros):
                pro += 1
                print(f"   [{pro}]  {pros}\n")
                projects['%s' % pro] = pros
    print("  --------------------------------------")
    print("\033[33m  [55] 解压  [66] 退出  [77] 设置  [88] TIK实验室\033[0m")
    print("")
    print(" \n")
    op_pro = input("  请输入序号：")
    if op_pro == '55':
        pass
        # unpackrom
    elif op_pro == '88':
        print('\n"维护中..."\n')
    elif op_pro == '00':
        op_pro = input("  请输入你要删除的项目序号：")
        if op_pro in projects.keys():
            delr = input(f"  确认删除{projects[op_pro]}？[1/0]")
            if delr == '1':
                rmdire(LOCALDIR + os.sep + projects[op_pro])
                ysuc("  删除成功！")
            else:
                print(" 取消删除")
        time.sleep(2)
    elif op_pro == '0':
        projec = input("请输入项目名称(非中文)：TI_")
        if not projec:
            ywarn("Input Error!")
            time.sleep(2)
        else:
            project = 'TI_%s' % projec
            if os.path.exists(LOCALDIR + os.sep + project):
                project = f'{project}_{time.strftime("%m%d%H%M%S")}'
                ywarn(f"项目已存在！自动命名为：{project}")
                time.sleep(2)
            os.makedirs(LOCALDIR + os.sep + project + os.sep + "config")
            menu(project)
    elif op_pro == '66':
        cls()
        sys.exit(0)
    elif op_pro == '77':
        setting()
    elif op_pro.isdigit():
        menu(projects[op_pro])
    else:
        ywarn("  Input error!")
        time.sleep(2)
    promenu()


def menu(project):
    PROJECT_DIR0 = LOCALDIR + os.sep + project
    PROJECT_DIR = PROJECT_DIR0
    cls()
    os.chdir(PROJECT_DIR)
    if not os.path.exists(os.path.abspath('config')):
        ywarn("项目已损坏！")
    if not os.path.exists(PROJECT_DIR + os.sep + 'TI_out'):
        os.makedirs(PROJECT_DIR + os.sep + 'TI_out')
    print('\n')
    print(" \033[31m>ROM菜单 \033[0m\n")
    print(f"  项目：{project}")
    if os.path.exists(PROJECT_DIR + os.sep + 'system' + os.sep + 'system' + os.sep + "build.prop"):
        SYSTEM_DIR0 = PROJECT_DIR0 + os.sep + "system" + os.sep + ("system")
        SYSTEM_DIR = SYSTEM_DIR0
    elif os.path.exists(PROJECT_DIR + os.sep + "system" + os.sep + "build.prop"):
        SYSTEM_DIR0 = PROJECT_DIR0 + os.sep + "system"
        SYSTEM_DIR = SYSTEM_DIR0
    else:
        SYSTEM_DIR = 0
        ywarn("  非完整ROM项目")
    print('')
    print('\033[33m    1> 项目主页     2> 解包菜单\033[0m\n')
    print('\033[36m    3> 打包菜单     4> 插件菜单\033[0m\n')
    print('\033[32m    5> 一键封装\033[0m\n')
    print()
    op_menu = input("    请输入编号: ")
    if op_menu == '1':
        return
    elif op_menu == '2':
        unpackChoo(PROJECT_DIR)
    elif op_menu == '3':
        pass
        # packChoo
    elif op_menu == '4':
        pass
        # subbed
    elif op_menu == '5':
        ywarn("维护中...")
        time.sleep(2)
    else:
        ywarn('   Input error!"')
        time.sleep(2)
    menu(project)


def unpackChoo(project):
    print(" \033[31m >分解 \033[0m\n")
    filen = 0
    files = {}
    infos = {}
    ywarn(f" 请将文件放于{project}根目录下！")
    print()
    print(" [0]- 分解所有文件\n")
    if dir_has(project, '.br'):
        print("\033[33m [Br]文件\033[0m\n")
        for br0 in os.listdir(project):
            if br0.endswith('.br'):
                if os.path.isfile(os.path.abspath(br0)):
                    filen += 1
                    print(f"   [{filen}]- {br0}\n")
                    files[filen] = br0
                    infos[filen] = 'br'
    if dir_has(project, '.new.dat'):
        print("\033[33m [Dat]文件\033[0m\n")
        for dat0 in os.listdir(project):
            if dat0.endswith('.new.dat'):
                if os.path.isfile(os.path.abspath(dat0)):
                    filen += 1
                    print(f"   [{filen}]- {dat0}\n")
                    files[filen] = dat0
                    infos[filen] = 'dat'
    if dir_has(project, '.new.dat.1'):
        for dat10 in os.listdir(project):
            if dat10.endswith('.dat.1'):
                if os.path.isfile(os.path.abspath(dat10)):
                    filen += 1
                    print(f"   [{filen}]- {dat10} <分段DAT>\n")
                    files[filen] = dat10
                    infos[filen] = 'dat.1'
    if dir_has(project, '.img'):
        print("\033[33m [Img]文件\033[0m\n")
        for img0 in os.listdir(project):
            if img0.endswith('.img'):
                if os.path.isfile(os.path.abspath(img0)):
                    filen += 1
                    info = gettype(os.path.abspath(img0))
                    if info == "unknow":
                        ywarn(f"   [{filen}]- {img0} <UNKNOWN>\n")
                    else:
                        print(f'   [{filen}]- {img0} <{info.upper()}>\n')
                    files[filen] = img0
                    if info != 'sparse':
                        infos[filen] = 'img'
                    else:
                        infos[filen] = 'sparse'
    if dir_has(project, '.bin'):
        for bin0 in os.listdir(project):
            if bin0.endswith('.bin'):
                if os.path.isfile(os.path.abspath(bin0)) and gettype(os.path.abspath(bin0)) == 'payload':
                    filen += 1
                    print(f"   [{filen}]- {bin0} <BIN>\n")
                    files[filen] = bin0
                    infos[filen] = 'payload'
    if dir_has(project, '.ozip'):
        print("\033[33m [Ozip]文件\033[0m\n")
        for ozip0 in os.listdir(project):
            if ozip0.endswith('.ozip'):
                if os.path.isfile(os.path.abspath(ozip0)) and gettype(os.path.abspath(ozip0)) == 'ozip':
                    filen += 1
                    print(f"   [{filen}]- {ozip0}\n")
                    files[filen] = ozip0
                    infos[filen] = 'ozip'
    if dir_has(project, '.ofp'):
        print("\033[33m [Ofp]文件\033[0m\n")
        for ofp0 in os.listdir(project):
            if ofp0.endswith('.ofp'):
                if os.path.isfile(os.path.abspath(ofp0)):
                    filen += 1
                    print(f"   [{filen}]- {ofp0}\n")
                    files[filen] = ofp0
                    infos[filen] = 'ofp'
    if dir_has(project, '.ops'):
        print("\033[33m [Ops]文件\033[0m\n")
        for ops0 in os.listdir(project):
            if ops0.endswith('.ops'):
                if os.path.isfile(os.path.abspath(ops0)):
                    filen += 1
                    print(f'   [{filen}]- {ops0}\n')
                    files[filen] = ops0
                    infos[filen] = 'ops'


promenu()