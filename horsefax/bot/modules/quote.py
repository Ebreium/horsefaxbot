from typing import cast
from pony.orm import *

from random import randint
from pprint import pprint
from horsefax.telegram.services.command import Command

from horsefax.telegram.types import TextEntity
from ..core import HorseFaxBot, ModuleTools, BaseModule, ChatService
from ..db import db
from .tracking import TelegramUser


class Quote(db.Entity):
	id = PrimaryKey(int, auto=True)
	user = Required(int)
	content = Required(str)
	added_by = Required(int)
	
	
class QuoteModule(BaseModule):
	@db_session
	def __init__(self, bot: HorseFaxBot, tools: ModuleTools) -> None:
		self.bot = bot
		self.util = tools
		self.util.register_command("addquote", self.add_quote)
		self.util.register_command("delquote", self.del_quote)
		self.util.register_command("listquote", self.list_quote)
		self.util.register_command("quote", self.quote)
		
	@db_session
	def add_quote(self, command: Command):
		if len(command.args) < 2 or len(command.message.entities) < 2:
			return "You must specify both a user and a quote."
		
		quote = None
		user = None
		if command.message.entities[1].type is TextEntity.Type.MENTION:
			user = TelegramUser.get(username=command.args[0][1:])
			quote = command.args[1:]
		elif command.message.entities[1].type is TextEntity.Type.TEXT_MENTION:
			user = TelegramUser.get(id=command.message.entities[1].user.id)
			quote = command.message.text[command.message.entities[1].offset + command.message.entities[1].length + 1:]
		
		added = Quote(user = user.id, content=quote, added_by=command.message.sender.id)

		return f"Added \"{quote}\". {count(q for q in Quote if q.user == user.id)} quotes for {user.first_name}."

		
	@db_session
	def quote(self, command: Command):
		if len(command.message.entities) < 2:
			q = Quote.select_random(1)[0]
			return f"{TelegramUser.get(id=q.user).first_name}: {q.content}"

		prefix = command.message.entities[1].offset + command.message.entities[1].length
		quote = None
		if command.message.entities[1].type is TextEntity.Type.MENTION:
			user = TelegramUser.get(username=command.args[0][1:])
			if len(command.args) > 1:
				quote = int(command.args[1])
		elif command.message.entities[1].type is TextEntity.Type.TEXT_MENTION:
			user = TelegramUser.get(id=command.message.entities[1].user.id)
			if len(command.message.text) > prefix:
				quote = int(command.message.text[prefix + 1:])
		else:
			return "Invalid input."
		quotes = select(q for q in Quote if q.user == user.id).order_by(Quote.id)[:]
		if quote is None:
			return user.first_name + ": \"__" + quotes[randint(0, len(quotes) - 1)].content + "__\""
		else:
			return user.first_name + ": \"__" + quotes[quote - 1].content + "__\""

	@db_session
	def del_quote(self, command: Command):
		if len(command.args) < 2:
			return "Syntax: `/delquote <user> <quote number>`"
		if len(command.message.entities) < 2:
			return "Syntax: `/delquote <user> <quote number>`"
		prefix = command.message.entities[1].offset + command.message.entities[1].length
		if command.message.entities[1].type is TextEntity.Type.MENTION:
			user = TelegramUser.get(username=command.args[0][1:])
			quote = int(command.args[1])
#TODO: Restructure
		elif command.message.entities[1].type is TextEntity.Type.TEXT_MENTION and len(command.message.text) > prefix:
			user = TelegramUser.get(id=command.message.entities[1].user.id)
			quote = int(command.message.text[prefix + 1:])
		else:
			return "Use a direct mention to a user."
		quotes = select(q for q in Quote if q.user == user.id).order_by(Quote.id)[:]
		if len(quotes) < quote:
			return "Invalid quote number."
		delete(q for q in Quote if q.id == quotes[quote - 1].id)
		return "Deleted quote."
		#return quotes[quote - 1].id
		
	@db_session
	def list_quote(self, command: Command):
		if len(command.args) < 2 or len(command.message.entities) < 2:
			return "Syntax: `/listquote <user> <page number>`"
		
		prefix = command.message.entities[1].offset + command.message.entities[1].length
		if command.message.entities[1].type is TextEntity.Type.MENTION:
			user = TelegramUser.get(username=command.args[0][1:])
			page = int(command.args[1])
		elif command.message.entities[1].type is TextEntity.Type.TEXT_MENTION and len(command.message.text) > prefix:
			user = TelegramUser.get(id=command.message.entities[1].user.id)
			page = int(command.message.text[prefix + 1:])
		else:
			return "Use a direct mention to a user."

		quotes = select(q for q in Quote if q.user == user.id).order_by(Quote.id).page(pagenum=page, pagesize=5)
		msg = f"Quotes for {user.first_name}, page {page}\n"
		if page == 1:
			n = 1
		else:
			n = page * 5 - 4
		for q in quotes:
			msg += f"{n}: \"{q.content}\"\n"
			n += 1
		return msg
