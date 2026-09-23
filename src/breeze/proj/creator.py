from pathlib import Path
import shutil

from dulwich.repo import Repo

from ..help_renderer import render_target_error


class BreezeSource:
    Project_Folder = Path(__file__).parent.parent / "assets" / "template"


class BreezeProjectCreator:
    @classmethod
    def create_proj(cls, target: str) -> None:
        root = Path(target).absolute()
        if root.exists():
            render_target_error()
            return

        root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            BreezeSource.Project_Folder,
            root,
            dirs_exist_ok=True,
        )
        manifest = root / "Breeze.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace("$name", root.name),
            encoding="utf-8",
        )
        with Repo.init(root):
            pass


__all__ = [
    "BreezeProjectCreator"
]
