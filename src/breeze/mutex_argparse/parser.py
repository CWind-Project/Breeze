from typing import Optional
import os
from enum import Enum

from rich import print as rprint

from ..help_renderer import helper_summary
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
        values = {
            name: helper_summary(name)
            for name, _display in self.command_entries()
        }
        values.update({name: msg for name, msg in self.helper.items() if msg})
        return Enum("Helper", values)

    def command_entries(self) -> list[tuple[str, str]]:
        rules = self._rule[BreezeSymbols.me]
        names = [name for name in self.helper if name in rules]
        names.extend(sorted(set(rules[BreezeSymbols.ls_cmd]) - set(names)))
        return [
            (
                name,
                f"--{name}" if rules[name][BreezeSymbols.sep] else name,
            )
            for name in names
        ]

    def option_entries(self, command: str) -> list[tuple[str, str]]:
        rules = self._rule[BreezeSymbols.me]
        command_rule = rules.get(command)
        if command_rule is None:
            return []
        subrules = command_rule.get(BreezeSymbols.subcmd)
        if not isinstance(subrules, dict):
            return []
        return [
            (
                name,
                f"--{name}" if subrules[name][BreezeSymbols.sep] else name,
            )
            for name in subrules[BreezeSymbols.ls_cmd]
        ]

    def add_mutually_exclusive(
            self,
            name: str,
            recv_type: type,
            helper: str = "",
            double_dash: Optional[bool] = False,
            need_subcmd: bool = False,
            optional_value: bool = False,
    ) -> BreezeSubCMDHandle | None:
        self.add_helper(name, helper)
        self._rule[
            BreezeSymbols.me
        ][name] = {
            BreezeSymbols.recv: recv_type,
            BreezeSymbols.vector: BreezeFuzzinessCalculator.word_to_vector(
                name),
            BreezeSymbols.helper: helper,
            BreezeSymbols.optional_value: optional_value,
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
                ][name]
            )
        return None

    def parse(self, argv: list[str]) -> BreezeArgBox:
        debug = os.environ.get(BreezeSymbols.debug_env)
        if debug:
            rprint(self._rule)
            rprint(f"DEBUG: {debug}, {type(debug)}")
        result = self._parse(argv)
        suggestion = {
            arg: result.suggest(arg, top=1)
            for arg in result.unknown_args
        }
        result.did_you_mean = suggestion
        return result


