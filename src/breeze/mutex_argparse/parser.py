from typing import Optional
import os
from enum import Enum

from rich import print as rprint

from .fc import BreezeFuzzinessCalculator
from .parse_engine import BreezeParserEngine, BreezeSubCMDHandle, BreezeArgBox, BreezeSymbols


class BreezeMutexArgParser(BreezeParserEngine):
    def __init__(
            self,
            *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.helper: dict[str, str] = {}

    def add_helper(self, name: str, msg: str)->None:
        self.helper.update( { name: msg } )

    def get_helper(self) -> Enum:
        return Enum("Helper", { k: v for k, v in self.helper.items() } )

    def add_mutually_exclusive(
            self,
            name: str,
            recv_type: type,
            helper: str = "",
            double_dash: Optional[bool] = False,
            need_subcmd: bool = False
    ) -> BreezeSubCMDHandle | None:
        self.add_helper(name, helper)
        self._rule[
            BreezeSymbols.me
        ][name] = {
            BreezeSymbols.recv: recv_type,
            BreezeSymbols.vector: BreezeFuzzinessCalculator.word_to_vector(
                name),
            BreezeSymbols.helper: helper,
            BreezeSymbols.sep: double_dash
        }
        self._rule[
            BreezeSymbols.me
        ][BreezeSymbols.ls_cmd].add(name)
        if need_subcmd:
            self._rule[
                BreezeSymbols.me
            ][name][BreezeSymbols.subcmd] = dict()
            self._rule[
                BreezeSymbols.me
            ][name][BreezeSymbols.subcmd][BreezeSymbols.ls_cmd] = []
            return BreezeSubCMDHandle(
                self._rule[
                    BreezeSymbols.me
                ][name], self
            )
        return None

    def parse(self, argv: list[str]) -> BreezeArgBox:
        debug = os.environ.get(BreezeSymbols.debug_env)
        if debug:
            rprint(self._rule)
            rprint(f"DEBUG: {debug}, {type(debug)}")
        result = self._parse(argv)
        suggestion = {
            arg: result.suggest(arg, top=3)
            for arg in result.unknown_args
        }
        result.did_you_mean = suggestion
        return result


