from enum import Enum
from pathlib import Path
from typing import cast, Any
import shutil

from brich import Rich


class BreezeIdentifier(Enum):
    File   = 1
    Folder = 2
    Name   = 3
    Content= 4


class BreezeSource:
    Bin_Breeze_Toml = """\
[package]
name = "me"
version = "0.0.1"
identifier = "Dev"
id_version = "0.0.1"
# {name}-{version}-{identifier}-{id_version}
# version -> identifier -> id_version
# Dev < Alpha < Beta < RC < Standard

description = ""
authors = []
homepage = ""

[entry]
source = "./src"
is_lib = false
module = "lib.wd"

[dependencies]
#NonExistsLib = "0.0.1,Standard"
"""
    Bin_Main_wd     = """\
fn main() {
	print(great("Wind"));
}
"""
    Bin_Lib_wd      = """\
pub use modules::great::great;    
"""
    Bin_Git_Ignore  = """\
# Folders
/target
/build
[T/t]emp
[E/e]xclude
[I/i]gnore
/.gitignore

# Files
*.tmp    
"""
    Bin_Great_wd    = """\
pub fn great(name: String) -> String {
	return "Hello,  {}!".format(name);
}
"""
    Git_Folder      = Path(__file__).parent.parent.joinpath("assets/template/git-template")


class BreezeTemplateProj:
    BinaryTStruct: dict[ int, Any ] = {
        BreezeIdentifier.File.value: [
            {
                BreezeIdentifier.Name: Path("Breeze.toml"),
                BreezeIdentifier.Content: BreezeSource.Bin_Breeze_Toml,
            },
            {
                BreezeIdentifier.Name: Path(".gitignore"),
                BreezeIdentifier.Content: BreezeSource.Bin_Git_Ignore
            }
        ],
        BreezeIdentifier.Folder.value: {
            BreezeIdentifier.Name: Path("src"),
            BreezeIdentifier.File.value: [
                {
                    BreezeIdentifier.Name: Path("main.wd"),
                    BreezeIdentifier.Content: BreezeSource.Bin_Main_wd
                },
                {
                    BreezeIdentifier.Name: Path("lib.wd"),
                    BreezeIdentifier.Content: BreezeSource.Bin_Lib_wd
                }
            ],
            BreezeIdentifier.Folder.value: {
                BreezeIdentifier.Name: Path("modules"),
                BreezeIdentifier.File.value: [
                    {
                        BreezeIdentifier.Name: Path("great.wd"),
                        BreezeIdentifier.Content: BreezeSource.Bin_Great_wd
                    }
                ]
            }
        }
    }


class BreezeProjectCreator:
    @classmethod
    def create_proj(cls, target: str) :
        root: Path = Path.absolute(Path(target))
        if root.exists():
            Rich.print("""\
<Bold><Underline>Breeze<Reset>:
 [E] new : This Command Failed
     Msg : The Target folder already exists
 [N] Hint: Try a different path, or delete the corresponding folder
""")
            return
        Path.mkdir(root, parents=True, exist_ok=True)
        shutil.copytree(
            BreezeSource.Git_Folder,
            root.joinpath(".git"),
            dirs_exist_ok=True
        )
        for k, v in BreezeTemplateProj.BinaryTStruct.items():
            match k:
                case BreezeIdentifier.File.value:
                    cls.__process_files(root, v)
                case BreezeIdentifier.Folder.value:
                    cls.__process_folders(root, v)

    @classmethod
    def __process_folders(cls, root: Path, v: dict) -> Path | None:
        root = root.joinpath(v[BreezeIdentifier.Name])
        Path.mkdir(root, parents=True, exist_ok=True)
        cls.__process_files(root, v[BreezeIdentifier.File.value])
        if BreezeIdentifier.Folder.value in v:
            return cls.__process_folders(root, v[BreezeIdentifier.Folder.value])
        return None

    @staticmethod
    def __process_files(root: Path, v: list):
        for file in v:
            f = cast(dict[BreezeIdentifier, str | Path], file)
            content = cast(str, f[BreezeIdentifier.Content])
            root.joinpath( f[BreezeIdentifier.Name] ).write_text(content, encoding="utf-8", )


__all__ = [
    "BreezeProjectCreator"
]
