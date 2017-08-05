from typing import cast
from peewee import *

from horsefax.telegram.services.command import Command

from ..core import HorseFaxBot, ModuleTools, BaseModule, ChatService
from ..db import BaseModel, db_random_fn


class Collection(BaseModel):
    id = PrimaryKeyField()
    name = CharField(index=True, unique=True)
    added_by = IntegerField(null=True)


class CollectionItem(BaseModel):
    collection = ForeignKeyField(Collection, related_name="items")
    content = CharField()
    added_by = IntegerField(null=True)


class CollectionModule(BaseModule):
    def __init__(self, bot: HorseFaxBot, tools: ModuleTools):
        self.bot = bot
        self.util = tools
        self.util.register_command("newcollection", self.add_collection)
        self.util.register_command("additem", self.add_item)
        self.util.register_command("removeitem", self.remove_item)
        for collection in Collection.select():
            self.util.register_command(collection.name, self.handle_command)

    def add_collection(self, command: Command):
        if len(command.args) < 1:
            return "You must specify a collection name."
        try:
            collection = Collection(name=command.args[0], added_by=command.message.sender.id)
            collection.save()
            self.util.register_command(cast(str, collection.name), self.handle_command)
        except IntegrityError:
            return "That collection already exists."
        else:
            return f"Created collection `{collection.name}`."

    def handle_command(self, command: Command):
        collection_name = command.command
        collection = Collection.get(name=collection_name)
        try:
            item = collection.items.order_by(db_random_fn).get()
        except DoesNotExist:
            return "That collection is empty."
        else:
            self.bot.message(command.message.chat, cast(str, item.content), parsing=ChatService.ParseMode.NONE)

    def add_item(self, command: Command):
        if len(command.args) < 2:
            return "Syntax: `/additem <collection> <thing to add>`"
        collection_name = command.args[0]
        thing = ' '.join(command.args[1:])
        try:
            collection = Collection.get(name=collection_name)
        except Collection.DoesNotExist:
            return "That collection does not exist."
        else:
            item = CollectionItem(collection=collection, content=thing, added_by=command.message.sender.id)
            item.save()
            return f"Added. {collection.items.count()} items in `{collection.name}`."

    def remove_item(self, command: Command):
        if len(command.args) < 2:
            return "Syntax: `/removeitem <collection> <thing to remove>`"
        collection_name = command.args[0]
        thing = ' '.join(command.args[1:])
        try:
            collection = Collection.get(name=collection_name)
        except Collection.DoesNotExist:
            return "That collection does not exist."
        else:
            try:
                collection.items.filter(content=thing).get().delete_instance()
            except DoesNotExist:
                return "Couldn't find that item."
            else:
                return "Item removed."
