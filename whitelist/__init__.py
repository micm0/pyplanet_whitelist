from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command

class Whitelist(AppConfig):
    name = 'whitelist'
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.whitelist = []
        self.active = False

    async def on_start(self):
        await self.instance.permission_manager.register('admin', 'Administer the whitelist', app=self, min_level=2)
        await self.instance.command_manager.register(
            Command(command='add', namespace='wl', target=self.add_player, perms='whitelist:admin', admin=True, description='Add a player to the local whitelist with his login or nickname.').add_param(name='player', required=True),
            Command(command='remove', namespace='wl', target=self.remove_player, perms='whitelist:admin', admin=True, description='Remove a player from the local whitelist with his login or nickname.').add_param(name='player', required=True),
            Command(command='current', namespace='wl', target=self.add_current_players, perms='whitelist:admin', admin=True, description='Create a new the local whitelist with all current connected players.'),
            Command(command='clear', namespace='wl', target=self.clear, perms='whitelist:admin', admin=True, description='Clear the local whitelist.'),
            Command(command='show', namespace='wl', target=self.show, perms='whitelist:admin', admin=True, description='Show the players from the local whitelist in the chat.'),
            Command(command='on', namespace='wl', target=self.activate, perms='whitelist:admin', admin=True, description='Activate the local whitelist.'),
            Command(command='off', namespace='wl', target=self.deactivate, perms='whitelist:admin', admin=True, description='Deactivate the local whitelist.'),
            Command(command='help', namespace='wl', target=self.show_commands, perms='whitelist:admin', admin=True, description='Show available whitelist commands in the chat.'),
        )
        self.context.signals.listen(mp_signals.player.player_connect, self.player_connect)
       

    async def player_connect(self, player, is_spectator, source, signal):
        if self.active:
            if player.level == 0:
                if self.whitelist != []:
                    if player not in self.whitelist:
                        await self.instance.gbx('Kick', player.login)
                        await self.instance.chat(f'{player.nickname} $ff0is not whitelisted!')
                    else:
                        await self.instance.chat(f'{player.nickname} $ff0is whitelisted!')

    async def activate(self, player, data = None, **kwargs):
        if(self.active):
            await self.instance.chat('$f00Whitelist already activated!', player.login)
        else:
            self.active = True
            await self.instance.chat('$ff0Whitelist Activated')
    
    async def deactivate(self, player, data = None, **kwargs):
        if(not self.active):
            await self.instance.chat('$f00Whitelist already deactivated!', player.login)
        else:
            self.active = False
            await self.instance.chat('$ff0Whitelist Deactivated')
    
    async def find_player_by_login_or_nickname(self, player_login_or_nickname, player):
        player_found = [p for p in self.instance.player_manager.online if p.nickname == player_login_or_nickname or p.login == player_login_or_nickname]
        return player_found

    async def add_player(self, player, data = None, **kwargs):
        player_found = await self.find_player_by_login_or_nickname(data.player, player)
        if not len(player_found) == 1:
            await self.instance.chat(f'{data.player} $f00is not found!', player.login)
        else:
            if player_found[0] not in self.whitelist:
                self.whitelist.append(player_found[0])
                await self.instance.chat(f'{player_found[0].nickname} $0C0added to the local whitelist!')
            else:
                await self.instance.chat(f'{player_found[0].nickname} $f00is already whitelisted locally!', player.login)

    async def remove_player(self, player, data = None, **kwargs):
        player_found = await self.find_player_by_login_or_nickname(data.player, player)
        if not len(player_found) == 1:
            await self.instance.chat(f'{data.player} $f00is not found!', player.login)
        else:
            if player_found[0] in self.whitelist:
                self.whitelist.remove(player_found[0])
                await self.instance.chat(f'{player_found[0].nickname} $0C0removed from the local whitelist!')
            else:
                await self.instance.chat(f'{player_found[0].nickname} $f00is not on local Whitelist, cannot be removed!', player.login)

    async def add_current_players(self, player, data = None, **kwargs): 
        self.whitelist = []
        for player in self.instance.player_manager.online:
            if player not in self.whitelist:
                self.whitelist.append(player)
            await self.instance.chat('$ff0Local Whitelist with current Players and Spectators created!')

    async def show(self, player, data = None, **kwargs):
        whitelist_as_string = ""
        if self.whitelist == []:
            await self.instance.chat('$f00There is players in the local whitelist!', player.login)
        else:
            for i, player in enumerate(self.whitelist):
                if i == len(self.whitelist) - 1:
                    whitelist_as_string += f'{player.nickname}'
                else:
                    whitelist_as_string += f'{player.nickname}, '
            await self.instance.chat(f'$ff0Players in the local whitelist: $fff{whitelist_as_string}', player.login)

    async def clear(self, player, data = None, **kwargs):
        self.whitelist = []
        await self.instance.chat('$0C0Local whitelist cleared!', player.login)

    async def show_commands(self, player, data = None, **kwargs):
        commands_string = ""
        commands = ['//wl add $iplayer$z$s | ','//wl remove $iplayer$z$s | ', '//wl current | ', '//wl clear | ', '//wl show | ', '//wl on | ', '//wl off | ', '//wl help']
        await self.instance.chat(commands_string.join(commands), player.login)

    
