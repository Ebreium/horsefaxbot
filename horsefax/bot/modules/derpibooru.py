import requests

from ..core import HorseFaxBot, ModuleTools, BaseModule
from horsefax.telegram.services.command import Command


class PingModule(BaseModule):
    def __init__(self, bot: HorseFaxBot, util: ModuleTools):
        self.bot = bot
        self.util = util
        self.util.register_command('derpibooru', self.derp)
        self.util.register_command('derpi', self.derp)

    def derp(self, command: Command):
        search = ' '.join(command.args)
        if search == '':
            search = 'safe'
        result = requests.get("https://derpibooru.org/search.json", {
            'filter_id': 141911,
            'q': search,
            'sf': 'random'}).json()
        if 'search' not in result:
            return "Something broke."
        result = result['search']
        if len(result) == 0:
            return "Didn't find anything."
        return f"https:{result[0]['representations']['large']}\nhttps://derpibooru.org/{result[0]['id']}"
