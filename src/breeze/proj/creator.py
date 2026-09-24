from pathlib import Path
import shutil

from brich import Rich
from dulwich.repo import Repo

from ..help_renderer import render_target_error


class BreezeSource:
    Project_Folder = Path(__file__).parent.parent / "assets" / "template"


class BreezeProjectCreator:
    @classmethod
    def create_proj(cls, target: str, is_lib: bool = False) -> int:
        root = Path(target).absolute()
        if root.exists():
            render_target_error()
            return 0

        root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            BreezeSource.Project_Folder,
            root,
            dirs_exist_ok=True,
        )
        manifest = root / "Breeze.toml"
        manifest_text = manifest.read_text(encoding="utf-8").replace(
            "$name", root.name
        )
        if is_lib:
            manifest_text = manifest_text.replace("is_lib = false", "is_lib = true")
        manifest.write_text(manifest_text, encoding="utf-8")
        with Repo.init(root):
            pass
        Rich.print("[<Bold><Underline>Breeze<Reset>] Done")
        return 0


__all__ = [
    "BreezeProjectCreator"
]
