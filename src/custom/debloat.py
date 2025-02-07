import json
import pathlib
from dataclasses import dataclass

import rich


def error(msg: str):
    rich.print(f"[bold red]Error: {msg}[/bold red]")


def warn(msg: str):
    rich.print(f"[red]Warning: {msg}[/red]")


def success(msg: str):
    rich.print(f"[green]Success: {msg}[/green]")


def info(msg: str):
    rich.print(f"[yellow]{msg}[/yellow]")


# maybe /home/rom/CHN (contains partitions to be handled)
STORE_PATH = "../.."

PARTITIONS = ["system", "system_ext", "product"]


@dataclass
class DebloatStuff:
    """
    Class to store one specific debloat stuff
    """

    store_path: str
    partition_name: str
    detail_path: str
    specific_info: str = ""

    def get_abs_path(self) -> str:
        """
        Get the absolute path of the debloat stuff
        """

        return f"{self.store_path}/{self.partition_name}/{self.detail_path}"

    def show_info(self) -> None:
        """
        Get the info of the debloat stuff
        """

        path = self.get_abs_path()
        self.specific_info = self.specific_info if self.specific_info else "None"
        print("----------------")
        info(f"Task: Remove {path}\n" f"Info: {self.specific_info}")
        print("----------------")

    def delete(self) -> int:
        """
        Delete the one specific folder
        """
        abs_path = pathlib.Path(self.get_abs_path())
        if not abs_path.exists():
            return 1

        abs_path.unlink()
        return 0

