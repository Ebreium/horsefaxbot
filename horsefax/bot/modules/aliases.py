import copy
from typing import Optional
from peewee import *

from horsefax.telegram.services.command import Command

from ..core import HorseFaxBot, ModuleTools, BaseModule
from ..db import BaseModel


class Alias(BaseModel):
    id = PrimaryKeyField()
    alias = CharField(index=True, unique=True)
    command = CharField()
    added_by = IntegerField(null=True)


class PingModule(BaseModule):
    def __init__(self, bot: HorseFaxBot, util: ModuleTools) -> None:
        self.bot = bot
        self.util = util
        self.util.register_command('addalias', self.add_alias)
        self.util.register_command('removealias', self.remove_alias)
        for alias in Alias.select():
            self.util.register_command(alias.alias, self.handle_alias)

    def add_alias(self, command: Command) -> Optional[str]:
        if len(command.args) < 2:
            return "Syntax: `/addalias <alias> <command>`"
        alias = command.args[0]
        alias_to = ' '.join(command.args[1:])
        try:
            Alias(alias=alias, command=alias_to, added_by=command.message.sender.id).save()
        except IntegrityError:
            return "That alias already exists."
        self.util.register_command(alias, self.handle_alias)
        return f"Added alias /{alias}."

    def handle_alias(self, command: Command) -> Optional[str]:
        alias = Alias.get(alias=command.command)
        if not hasattr(command.message, 'alias_origin'):
            command.message.alias_origin = []
        if command.command in command.message.alias_origin:
            return f"Detected command loop: `{' -> '.join(command.message.alias_origin)} -> {command.command}`"
        command.message.alias_origin.append(command.command)

        new_message = copy.copy(command.message)
        new_message.text = "/" + alias.command
        if len(command.args) > 0:
            new_message.text += ' ' + ' '.join(command.args)
        self.bot.commands.handle_message(new_message)
        return None

    def remove_alias(self, command: Command) -> str:
        if len(command.args) < 1:
            return "Syntax: `/removealias alias`"
        alias_name = command.args[0]
        try:
            alias = Alias.get(alias=alias_name)
        except DoesNotExist:
            return f"Alias `{alias_name}` does not exist."
        alias.delete()
        return f"Deleted `/{alias_name}` (which was an alias for `/{alias.command}`)."
