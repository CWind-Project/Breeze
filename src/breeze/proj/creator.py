from pathlib import Path
import shutil

from brich import Rich
from dulwich.repo import Repo


class BreezeSource:
    Project_Folder = Path(__file__).parent.parent / "assets" / "template"


class BreezeProjectCreator:
    @classmethod
    def create_proj(cls, target: str) -> None:
        root = Path(target).absolute()
        if root.exists():
            Rich.print("""\
<Bold><Underline>Breeze<Reset>:
 [E] new : This Command Failed
     Msg : The Target folder already exists
 [N] Hint: Try a different path, or delete the corresponding folder
""")
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
