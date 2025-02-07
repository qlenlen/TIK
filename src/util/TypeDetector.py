from dataclasses import dataclass


@dataclass
class TypeFlag:
    flag: bytes
    typeStr: str
    offset: int = 0


class TypeDetector:
    """
    文件类型获取
    """

    path: str = ""

    formats: tuple[TypeFlag] = (
        TypeFlag(b"PK", "zip"),
        TypeFlag(b"OPPOENCRYPT!", "ozip"),
        TypeFlag(b"7z", "7z"),
        TypeFlag(b"\x53\xef", "ext", 1080),
        TypeFlag(b"\x10\x20\xF5\xF2", "f2fs", 1024),
        TypeFlag(b"\x3a\xff\x26\xed", "sparse"),
        TypeFlag(b"\xe2\xe1\xf5\xe0", "erofs", 1024),
        TypeFlag(b"CrAU", "payload"),
        TypeFlag(b"AVB0", "vbmeta"),
        TypeFlag(b"\xd7\xb7\xab\x1e", "dtbo"),
        TypeFlag(b"\xd0\x0d\xfe\xed", "dtb"),
        TypeFlag(b"MZ", "exe"),
        TypeFlag(b".ELF", "elf"),
        TypeFlag(b"ANDROID!", "boot"),
        TypeFlag(b"VNDRBOOT", "vendor_boot"),
        TypeFlag(b"AVBf", "avb_foot"),
        TypeFlag(b"BZh", "bzip2"),
        TypeFlag(b"CHROMEOS", "chrome"),
        TypeFlag(b"\x1f\x8b", "gzip"),
        TypeFlag(b"\x1f\x9e", "gzip"),
        TypeFlag(b"\x02\x21\x4c\x18", "lz4_legacy"),
        TypeFlag(b"\x03\x21\x4c\x18", "lz4"),
        TypeFlag(b"\x04\x22\x4d\x18", "lz4"),
        TypeFlag(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03", "zopfli"),
        TypeFlag(b"\xfd7zXZ", "xz"),
        TypeFlag(b"]\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff", "lzma"),
        TypeFlag(b"\x02!L\x18", "lz4_lg"),
        TypeFlag(b"\x89PNG", "png"),
        TypeFlag(b"LOGO!!!!", "logo"),
        TypeFlag(b"\x28\xb5\x2f\xfd", "zstd"),
    )

    def __init__(self, path: str):
        self.path = path

    def compare(self, type_flag: TypeFlag) -> bool:
        with open(self.path, "rb") as f:
            f.seek(type_flag.offset)
            return f.read(len(type_flag.flag)) == type_flag.flag

    @staticmethod
    def inner_compare(fileObj, type_flag: TypeFlag) -> bool:
        """
        优化速度，不重复开启文件
        """
        fileObj.seek(type_flag.offset)
        return fileObj.read(len(type_flag.flag)) == type_flag.flag

    def get_type(self) -> str:
        with open(self.path, "rb") as file:
            for f in self.formats:
                if self.inner_compare(file, f):
                    return f.typeStr
            return "Unknown"
