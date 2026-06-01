"""Command Palette — discoverable command registry"""
from typing import Callable
from dataclasses import dataclass, field


@dataclass
class Command:
    name: str
    description: str
    category: str
    handler: Callable = None
    aliases: list[str] = field(default_factory=list)


class CommandPalette:
    def __init__(self):
        self.commands: dict[str, Command] = {}

    def register(self, cmd: Command):
        self.commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self.commands[alias] = cmd

    def get(self, name: str) -> Command | None:
        return self.commands.get(name)

    def list_commands(self, category: str | None = None) -> list[Command]:
        seen = set()
        result = []
        for cmd in self.commands.values():
            if cmd.name not in seen:
                if category is None or cmd.category == category:
                    result.append(cmd)
                    seen.add(cmd.name)
        return result

    def search(self, query: str) -> list[Command]:
        q = query.lower()
        return [
            cmd
            for cmd in dict.fromkeys(self.commands.values())
            if q in cmd.name.lower() or q in cmd.description.lower()
        ]


palette = CommandPalette()
