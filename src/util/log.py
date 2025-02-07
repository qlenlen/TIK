from time import strftime


def log_error(info):
    print(f"\033[91m[{strftime('%H:%M:%S')}] [ERROR]{info}\033[0m")


def log_warning(info):
    print(f"\033[93m[{strftime('%H:%M:%S')}] [WARNING]{info}\033[0m")


def log_success(info):
    print(f"\033[92m[{strftime('%H:%M:%S')}] [SUCCESS]{info}\033[0m")


def wrap_red(info, needTime=True) -> str:
    if needTime:
        return f"\033[31m[{strftime('%H:%M:%S')}]{info}\033[0m"
    else:
        return f"\033[31m{info}\033[0m"


def warp_yellow(info, needTime=True) -> str:
    if needTime:
        return f"\033[33m[{strftime('%H:%M:%S')}]{info}\033[0m"
    else:
        return f"\033[33m{info}\033[0m"


def wrap_green(info, needTime=True) -> str:
    if needTime:
        return f"\033[32m[{strftime('%H:%M:%S')}]{info}\033[0m"
    else:
        return f"\033[32m{info}\033[0m"


def print_red(info, needTime=True):
    print(wrap_red(info, needTime))


def print_yellow(info, needTime=True):
    print(warp_yellow(info, needTime))


def print_green(info, needTime=True):
    print(wrap_green(info, needTime))


print_green("Hello, World!")
