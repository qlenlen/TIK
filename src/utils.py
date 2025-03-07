from __future__ import print_function

import errno
import os
import platform as plat
import struct
import subprocess
import sys
import tempfile
import zipfile
from os import getcwd
from os.path import exists
from random import randint, choice
from shutil import move, rmtree
from threading import Thread

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from . import blockimgdiff
from . import sparse_img
from . import update_metadata_pb2 as um
from .lpunpack import SparseImage


def u64(x):
    return struct.unpack(">Q", x)[0]


DataImage = blockimgdiff.DataImage
# -----
# ====================================================
#          FUNCTION: sdat2img img2sdat
#       AUTHORS: xpirt - luxi78 - howellzhu
#          DATE: 2018-10-27 10:33:21 CEST | 2018-05-25 12:19:12 CEST
# ====================================================
# -----
# ----VALUES
try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass
elocal = getcwd()
platform = plat.machine()
ostype = plat.system()
binner = elocal + os.sep + "bin"
ebinner = binner + os.sep + ostype + os.sep + platform + os.sep

def call(exe, extra_path=True, out=0):
    if isinstance(exe, list):
        cmd = exe
        if extra_path:
            cmd[0] = f"{ebinner}{exe[0]}"
        cmd = [i for i in cmd if i]
    else:
        cmd = f'{ebinner}{exe}' if extra_path else exe
        if os.name == 'posix':
            cmd = cmd.split()
    conf = subprocess.CREATE_NO_WINDOW if os.name != 'posix' else 0
    try:
        ret = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, creationflags=conf)
        for i in iter(ret.stdout.readline, b""):
            if out == 0:
                try:
                    out_put = i.decode("utf-8").strip()
                except (Exception, BaseException):
                    out_put = i.decode("gbk").strip()
                print(out_put)
    except subprocess.CalledProcessError as e:
        for i in iter(e.stdout.readline, b""):
            if out == 0:
                try:
                    out_put = i.decode("utf-8").strip()
                except (Exception, BaseException):
                    out_put = i.decode("gbk").strip()
                print(out_put)
        return 2
    except FileNotFoundError:
        return 2
    ret.wait()
    return ret.returncode

dn = None
formats = ([b'PK', "zip"], [b'OPPOENCRYPT!', "ozip"], [b'7z', "7z"], [b'\x53\xef', 'ext', 1080],
           [b'\x10\x20\xF5\xF2', 'f2fs', 1024],
           [b'\x3a\xff\x26\xed', "sparse"], [b'\xe2\xe1\xf5\xe0', "erofs", 1024], [b"CrAU", "payload"],
           [b"AVB0", "vbmeta"], [b'\xd7\xb7\xab\x1e', "dtbo"],
           [b'\xd0\x0d\xfe\xed', "dtb"], [b"MZ", "exe"], [b".ELF", 'elf'],
           [b"ANDROID!", "boot"], [b"VNDRBOOT", "vendor_boot"],
           [b'AVBf', "avb_foot"], [b'BZh', "bzip2"],
           [b'CHROMEOS', 'chrome'], [b'\x1f\x8b', "gzip"],
           [b'\x1f\x9e', "gzip"], [b'\x02\x21\x4c\x18', "lz4_legacy"],
           [b'\x03\x21\x4c\x18', 'lz4'], [b'\x04\x22\x4d\x18', 'lz4'],
           [b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03', "zopfli"], [b'\xfd7zXZ', 'xz'],
           [b']\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff', 'lzma'], [b'\x02!L\x18', 'lz4_lg'],
           [b'\x89PNG', 'png'], [b"LOGO!!!!", 'logo'], [b'\x28\xb5\x2f\xfd', 'zstd'])


# ----DEFS
def payload_reader(payloadfile):
    if payloadfile.read(4) != b'CrAU':
        print(f"Magic Check Fail\n")
        payloadfile.close()
        return
    file_format_version = u64(payloadfile.read(8))
    assert file_format_version == 2
    manifest_size = u64(payloadfile.read(8))
    metadata_signature_size = struct.unpack('>I', payloadfile.read(4))[0] if file_format_version > 1 else 0
    manifest = payloadfile.read(manifest_size)
    payloadfile.read(metadata_signature_size)
    dam = um.DeltaArchiveManifest()
    dam.ParseFromString(manifest)
    return dam


class aesencrypt:
    @staticmethod
    def encrypt(key, file_path, outfile):
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        with open(outfile, "wb") as f, open(file_path, 'rb') as fd:
            f.write(cipher.encrypt(pad(fd.read(), AES.block_size)))

    @staticmethod
    def decrypt(key, file_path, outfile):
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        with open(file_path, "rb") as f:
            data = cipher.decrypt(f.read())
        data = data[:-data[-1]]
        with open(outfile, "wb") as f:
            f.write(data)


class dbkxyt:
    def __init__(self, work, code, extra):
        if not work:
            print('文件夹不存在')
            return
        if os.path.exists((dir_ := work) + "firmware-update"):
            os.rename(dir_ + "firmware-update", dir_ + "images")
        if not os.path.exists(dir_ + "images"):
            os.makedirs(dir_ + 'images')
        if os.path.exists(dir_ + 'META-INF'):
            rmtree(dir_ + 'META-INF')
        zipfile.ZipFile(extra).extractall(dir_)
        right_device = code
        with open(dir_ + "bin" + os.sep + "right_device", 'w', encoding='gbk') as rd:
            rd.write(right_device + "\n")
        with open(
                dir_ + 'META-INF' + os.sep + "com" + os.sep + "google" + os.sep + "android" + os.sep + "update-binary",
                'r+', encoding='utf-8', newline='\n') as script:
            lines = script.readlines()
            lines.insert(45, f'right_device="{right_device}"\n')
            add_line = self.get_line_num(lines, '#Other images')
            for t in os.listdir(dir_ + "images"):
                if t.endswith('.img') and not os.path.isdir(dir_ + t):
                    print("Add Flash method {} to update-binary".format(t))
                    if os.path.getsize(os.path.join(dir_ + 'images', t)) > 209715200:
                        self.zstd_compress(os.path.join(dir_ + 'images', t))
                        lines.insert(add_line,
                                     'package_extract_zstd "images/{}.zst" "/dev/block/by-name/{}"\n'.format(t, t[:-4]))
                    else:
                        lines.insert(add_line,
                                     'package_extract_file "images/{}" "/dev/block/by-name/{}"\n'.format(t, t[:-4]))
            for t in os.listdir(dir_):
                if not t.startswith("preloader_") and not os.path.isdir(dir_ + t) and t.endswith('.img'):
                    print("Add Flash method {} to update-binary".format(t))
                    if os.path.getsize(dir_ + t) > 209715200:
                        self.zstd_compress(dir_ + t)
                        move(os.path.join(dir_, t + ".zst"), os.path.join(dir_ + "images", t + ".zst"))
                        lines.insert(add_line,
                                     'package_extract_zstd "images/{}.zst" "/dev/block/by-name/{}"\n'.format(t, t[:-4]))
                    else:
                        lines.insert(add_line,
                                     'package_extract_file "images/{}" "/dev/block/by-name/{}"\n'.format(t, t[:-4]))
                        move(os.path.join(dir_, t), os.path.join(dir_ + "images", t))
            script.seek(0)
            script.truncate()
            script.writelines(lines)

    def zstd_compress(self, path):
        if os.path.exists(path):
            if gettype(path) == "sparse":
                print(f"[INFO] {os.path.basename(path)} is (sparse), converting to (raw)")
                simg2img(path)
            try:
                print(f"[Compress] {os.path.basename(path)}...")
                call("zstd -5 --rm {} -o {}".format(path, path + ".zst"))
            except Exception as e:
                print(f"[Fail] Compress {os.path.basename(path)} Fail:{e}")

    @staticmethod
    def get_line_num(data, text):
        for i, t_ in enumerate(data):
            if text in t_:
                return i


class sdat2img:
    def __init__(self, TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE):
        print('sdat2img binary - version: 1.3\n')
        self.TRANSFER_LIST_FILE = TRANSFER_LIST_FILE
        self.NEW_DATA_FILE = NEW_DATA_FILE
        self.OUTPUT_IMAGE_FILE = OUTPUT_IMAGE_FILE
        self.list_file = self.parse_transfer_list_file()
        block_size = 4096
        version = next(self.list_file)
        self.version = str(version)
        next(self.list_file)
        show = "Android {} detected!\n"
        if version == 1:
            print(show.format("Lollipop 5.0"))
        elif version == 2:
            print(show.format("Lollipop 5.1"))
        elif version == 3:
            print(show.format("Marshmallow 6.x"))
        elif version == 4:
            print(show.format("Nougat 7.x / Oreo 8.x / Pie 9.x"))
        else:
            print(show.format('Unknown Android version {version}!\n'))

        # Don't clobber existing files to avoid accidental data loss
        try:
            output_img = open(self.OUTPUT_IMAGE_FILE, 'wb')
        except IOError as e:
            if e.errno == errno.EEXIST:
                print('Error: the output file "{}" already exists'.format(e.filename))
                print('Remove it, rename it, or choose a different file name.')
                return
            else:
                raise

        new_data_file = open(self.NEW_DATA_FILE, 'rb')
        max_file_size = 0

        for command in self.list_file:
            max_file_size = max(pair[1] for pair in [i for i in command[1]]) * block_size
            if command[0] == 'new':
                for block in command[1]:
                    begin = block[0]
                    block_count = block[1] - begin
                    print('\rCopying {} blocks into position {}...'.format(block_count, begin), end="")

                    # Position output file
                    output_img.seek(begin * block_size)

                    # Copy one block at a time
                    while block_count > 0:
                        output_img.write(new_data_file.read(block_size))
                        block_count -= 1
            else:
                print('\rSkipping command {}...'.format(command[0]), end="")

        # Make file larger if necessary
        if output_img.tell() < max_file_size:
            output_img.truncate(max_file_size)

        output_img.close()
        new_data_file.close()
        print('\nDone! Output image: {}'.format(os.path.realpath(output_img.name)))

    @staticmethod
    def rangeset(src):
        src_set = src.split(',')
        num_set = [int(item) for item in src_set]
        if len(num_set) != num_set[0] + 1:
            print('Error on parsing following data to rangeset:\n{}'.format(src))
            return

        return tuple([(num_set[i], num_set[i + 1]) for i in range(1, len(num_set), 2)])

    def parse_transfer_list_file(self):
        with open(self.TRANSFER_LIST_FILE, 'r') as trans_list:
            # First line in transfer list is the version number
            # Second line in transfer list is the total number of blocks we expect to write
            if (version := int(trans_list.readline())) >= 2 and (new_blocks := int(trans_list.readline())):
                # Third line is how many stash entries are needed simultaneously
                trans_list.readline()
                # Fourth line is the maximum number of blocks that will be stashed simultaneously
                trans_list.readline()
            # Subsequent lines are all individual transfer commands
            yield version
            yield new_blocks
            for line in trans_list:
                line = line.split(' ')
                cmd = line[0]
                if cmd in ['erase', 'new', 'zero']:
                    yield [cmd, self.rangeset(line[1])]
                else:
                    # Skip lines starting with numbers, they are not commands anyway
                    if not cmd[0].isdigit():
                        print('Command "{}" is not valid.'.format(cmd))
                        return


def gettype(file) -> str:
    if not os.path.exists(file):
        return "fne"

    def compare(header: bytes, number: int = 0) -> int:
        with open(file, 'rb') as f:
            f.seek(number)
            return f.read(len(header)) == header

    def is_super(fil) -> any:
        with open(fil, 'rb') as file_:
            buf = bytearray(file_.read(4))
            if len(buf) < 4:
                return False
            file_.seek(0, 0)

            while buf[0] == 0x00:
                buf = bytearray(file_.read(1))
            try:
                file_.seek(-1, 1)
            except:
                return False
            buf += bytearray(file_.read(4))
        return buf[1:] == b'\x67\x44\x6c\x61'

    def is_super2(fil) -> any:
        with open(fil, 'rb') as file_:
            try:
                file_.seek(4096, 0)
            except:
                return False
            buf = bytearray(file_.read(4))
        return buf == b'\x67\x44\x6c\x61'

    try:
        if is_super(file) or is_super2(file):
            return 'super'
    except IndexError:
        pass
    for f_ in formats:
        if len(f_) == 2:
            if compare(f_[0]):
                return f_[1]
        elif len(f_) == 3:
            if compare(f_[0], f_[2]):
                return f_[1]
    return "unknow"


def dynamic_list_reader(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as l_f:
        for p in l_f.readlines():
            if p[:1] == '#':
                continue
            tmp = p.strip().split()
            if tmp[0] == 'remove_all_groups':
                data.clear()
            elif tmp[0] == 'add_group':
                data[tmp[1]] = {}
                data[tmp[1]]['size'] = tmp[2]
                data[tmp[1]]['parts'] = []
            elif tmp[0] == 'add':
                data[tmp[2]]['parts'].append(tmp[1])
            else:
                print(f"Skip {tmp}")
    return data


def generate_dynamic_list(dbfz, size, set_, lb, work):
    data = ['# Remove all existing dynamic partitions and groups before applying full OTA', 'remove_all_groups']
    with open(work + "dynamic_partitions_op_list", 'w', encoding='utf-8', newline='\n') as d_list:
        if set_ == 1:
            data.append(f'# Add group {dbfz} with maximum size {size}')
            data.append(f'add_group {dbfz} {size}')
        elif set_ in [2, 3]:
            data.append(f'# Add group {dbfz}_a with maximum size {size}')
            data.append(f'add_group {dbfz}_a {size}')
            data.append(f'# Add group {dbfz}_b with maximum size {size}')
            data.append(f'add_group {dbfz}_b {size}')
        for part in lb:
            if set_ == 1:
                data.append(f'# Add partition {part} to group {dbfz}')
                data.append(f'add {part} {dbfz}')
            elif set_ in [2, 3]:
                data.append(f'# Add partition {part}_a to group {dbfz}_a')
                data.append(f'add {part}_a {dbfz}_a')
                data.append(f'# Add partition {part}_b to group {dbfz}_b')
                data.append(f'add {part}_b {dbfz}_b')
        for part in lb:
            if set_ == 1:
                data.append(f'# Grow partition {part} from 0 to {os.path.getsize(work + part + ".img")}')
                data.append(f'resize {part} {os.path.getsize(work + part + ".img")}')
            elif set_ in [2, 3]:
                data.append(f'# Grow partition {part}_a from 0 to {os.path.getsize(work + part + ".img")}')
                data.append(f'resize {part}_a {os.path.getsize(work + part + ".img")}')
        d_list.writelines([key + "\n" for key in data])
        data.clear()


def v_code(num=6) -> str:
    ret = ""
    for i in range(num):
        num = randint(0, 9)
        # num = chr(random.randint(48,57))#ASCII表示数字
        letter = chr(randint(97, 122))  # 取小写字母
        Letter = chr(randint(65, 90))  # 取大写字母
        s = str(choice([num, letter, Letter]))
        ret += s
    return ret


def qc(file_) -> None:
    if not exists(file_):
        return
    with open(file_, 'r+', encoding='utf-8', newline='\n') as f:
        data = f.readlines()
        new_data = sorted(set(data), key=data.index)
        if len(new_data) == len(data):
            print("No need to handle")
            return
        f.seek(0)
        f.truncate()
        f.writelines(new_data)
    del data, new_data


def cz(func, *args):
    Thread(target=func, args=args, daemon=True).start()


def simg2img(path):
    with open(path, 'rb') as fd:
        if SparseImage(fd).check():
            print('Sparse image detected.')
            print('Process conversion to non sparse image...')
            unsparse_file = SparseImage(fd).unsparse()
            print('Result:[ok]')
        else:
            print(f"{path} not Sparse.Skip!")
    try:
        if os.path.exists(unsparse_file):
            os.remove(path)
            os.rename(unsparse_file, path)
    except Exception as e:
        print(e)


def img2sdat(input_image, out_dir='.', version=None, prefix='system'):
    print('img2sdat binary - version: %s\n' % 1.7)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
        '''            
        1. Android Lollipop 5.0
        2. Android Lollipop 5.1
        3. Android Marshmallow 6.0
        4. Android Nougat 7.0/7.1/8.0/8.1
        '''

    blockimgdiff.BlockImageDiff(sparse_img.SparseImage(input_image, tempfile.mkstemp()[1], '0'), None, version).Compute(
        out_dir + '/' + prefix)


def findfile(file, dir_) -> str:
    for root, dirs, files in os.walk(dir_, topdown=True):
        if file in files:
            if os.name == 'nt':
                return (root + os.sep + file).replace("\\", '/')
            else:
                return root + os.sep + file
        else:
            pass


def findfolder(dir__, folder_name):
    for root, dirnames, filenames in os.walk(dir__):
        for dirname in dirnames:
            if dirname == folder_name:
                return os.path.join(root, dirname).replace("\\", '/')
    return None


# ----CLASSES


class vbpatch:
    def __init__(self, file_):
        self.file = file_

    def checkmagic(self):
        if os.access(self.file, os.F_OK):
            magic = b'AVB0'
            with open(self.file, "rb") as f:
                buf = f.read(4)
                return magic == buf
        else:
            print("File dose not exist!")

    def readflag(self):
        if not self.checkmagic():
            return False
        if os.access(self.file, os.F_OK):
            with open(self.file, "rb") as f:
                f.seek(123, 0)
                flag = f.read(1)
                if flag == b'\x00':
                    return 0  # Verify boot and dm-verity is on
                elif flag == b'\x01':
                    return 1  # Verify boot but dm-verity is off
                elif flag == b'\x02':
                    return 2  # All verity is off
                else:
                    return flag
        else:
            print("File does not exist!")

    def patchvb(self, flag):
        if not self.checkmagic():
            return False
        if os.access(self.file, os.F_OK):
            with open(self.file, 'rb+') as f:
                f.seek(123, 0)
                f.write(flag)
            print("Done!")
        else:
            print("File not Found")

    def restore(self):
        self.patchvb(b'\x00')

    def disdm(self):
        self.patchvb(b'\x01')

    def disavb(self):
        self.patchvb(b'\x02')


class DUMPCFG:
    blksz = 0x1 << 0xc
    headoff = 0x4000
    magic = b"LOGO!!!!"
    imgnum = 0
    imgblkoffs = []
    imgblkszs = []


class BMPHEAD(object):
    def __init__(self, buf: bytes = None):  # Read bytes buf and use this struct to parse
        assert buf is not None, f"buf Should be bytes not {type(buf)}"
        # print(buf)
        self.structstr = "<H6I"
        (
            self.magic,
            self.fsize,
            self.reserved,
            self.hsize,
            self.dib,
            self.width,
            self.height,
        ) = struct.unpack(self.structstr, buf)


class XIAOMI_BLKSTRUCT(object):
    def __init__(self, buf: bytes):
        self.structstr = "2I"
        (
            self.imgoff,
            self.blksz,
        ) = struct.unpack(self.structstr, buf)


class LOGODUMPER(object):
    def __init__(self, img: str, out: str, dir__: str = "pic"):
        self.out = out
        self.img = img
        self.dir = dir__
        self.structstr = "<8s"
        self.cfg = DUMPCFG()
        self.chkimg(img)

    def chkimg(self, img: str):
        assert os.access(img, os.F_OK), f"{img} does not found!"
        with open(img, 'rb') as f:
            f.seek(self.cfg.headoff, 0)
            self.magic = struct.unpack(
                self.structstr, f.read(struct.calcsize(self.structstr))
            )[0]
            while True:
                m = XIAOMI_BLKSTRUCT(f.read(8))
                if m.imgoff != 0:
                    self.cfg.imgblkszs.append(m.blksz << 0xc)
                    self.cfg.imgblkoffs.append(m.imgoff << 0xc)
                    self.cfg.imgnum += 1
                else:
                    break
        # print(self.magic)
        assert self.magic == b"LOGO!!!!", "File does not match xiaomi logo magic!"
        print("Xiaomi LOGO!!!! format check pass!")

    def unpack(self):
        with open(self.img, 'rb') as f:
            print("Unpack:\n"
                  "BMP\tSize\tWidth\tHeight")
            for i in range(self.cfg.imgnum):
                f.seek(self.cfg.imgblkoffs[i], 0)
                bmph = BMPHEAD(f.read(26))
                f.seek(self.cfg.imgblkoffs[i], 0)
                print("%d\t%d\t%d\t%d" % (i, bmph.fsize, bmph.width, bmph.height))
                with open(os.path.join(self.out, "%d.bmp" % i), 'wb') as o:
                    o.write(f.read(bmph.fsize))
            print("\tDone!")

    def repack(self):
        with open(self.out, 'wb') as o:
            off = 0x5
            for i in range(self.cfg.imgnum):
                print("Write BMP [%d.bmp] at offset 0x%X" % (i, off << 0xc))
                with open(os.path.join(self.dir, "%d.bmp" % i), 'rb') as b:
                    bhead = BMPHEAD(b.read(26))
                    b.seek(0, 0)
                    self.cfg.imgblkszs[i] = (bhead.fsize >> 0xc) + 1
                    self.cfg.imgblkoffs[i] = off

                    o.seek(off << 0xc)
                    o.write(b.read(bhead.fsize))

                    off += self.cfg.imgblkszs[i]
            o.seek(self.cfg.headoff)
            o.write(self.magic)
            for i in range(self.cfg.imgnum):
                o.write(struct.pack("<I", self.cfg.imgblkoffs[i]))
                o.write(struct.pack("<I", self.cfg.imgblkszs[i]))
            print("\tDone!")
