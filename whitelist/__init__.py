from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command
from .view import WhiteListView, WhiteListWidget

class Whitelist(AppConfig):
    name = 'whitelist'
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.whitelist = []
        self.active = False
        self.widget = WhiteListWidget(self)

    async def on_start(self):
        await self.instance.permission_manager.register('admin', 'Administer the whitelist', app=self, min_level=2)
        await self.instance.command_manager.register(
            Command(command='add', namespace='wl', target=self.add_player_from_server, perms='whitelist:admin', admin=True, description='Add a player login to the local whitelist with his login or nickname.').add_param(name='player', required=True),
            Command(command='addlogin', namespace='wl', target=self.add_player_login, perms='whitelist:admin', admin=True, description='Add a player login to the local whitelist.').add_param(name='player_login', required=True),
            Command(command='remove', namespace='wl', target=self.remove_player_login, perms='whitelist:admin', admin=True, description='Remove a player login from the local whitelist.').add_param(name='player', required=True),
            Command(command='current', namespace='wl', target=self.add_current_players, perms='whitelist:admin', admin=True, description='Create a new the local whitelist with all current connected players.'),
            Command(command='clear', namespace='wl', target=self.clear, perms='whitelist:admin', admin=True, description='Clear the local whitelist.'),
            Command(command='show', namespace='wl', target=self.show, perms='whitelist:admin', admin=True, description='Show the players from the local whitelist in the chat.'),
            Command(command='on', namespace='wl', target=self.activate, perms='whitelist:admin', admin=True, description='Activate the local whitelist.'),
            Command(command='off', namespace='wl', target=self.deactivate, perms='whitelist:admin', admin=True, description='Deactivate the local whitelist.'),
            Command(command='help', namespace='wl', target=self.show_commands, perms='whitelist:admin', admin=True, description='Show available whitelist commands in the chat.'),
            Command(command='status', namespace='wl', target=self.get_status, perms='whitelist:admin', admin=True, description='Show the status of the whitelist(on or off) in the chat'),
            Command(command='whitelist', target=self.show_whitelist_window, perms='whitelist:admin', admin=True, description='Show the whitelist window'),
        )
        self.context.signals.listen(mp_signals.player.player_connect, self.player_connect)

        # Display widget for admin roles 
        for player in self.instance.player_manager.online:
            if player.level > 0:
                await self.widget.display([player.login])
       

    async def player_connect(self, player, *args, **kwargs):
        # Check if player(not admin) is in the whitelist and kick him if not
        if self.active:
            if player.level == 0:
                if player.login not in self.whitelist:
                    await self.instance.gbx('Kick', player.login, 'You are not in the whitelist')
                    await self.instance.chat(f'{player.nickname} $ff0is not whitelisted!')
                else:
                    await self.instance.chat(f'{player.nickname} $ff0is whitelisted!')
            else:
                await self.instance.chat(f'{player.nickname} $ff0is whitelisted!')
        # Display widget for admin roles        
        if player.level > 0:
            await self.widget.display([player.login])

    async def activate(self, player, **kwargs):
        if(self.active):
            await self.instance.chat('$f00Whitelist already activated!', player.login)
        else:
            self.active = True
            await self.instance.chat('$ff0Whitelist Activated')
            await self.kick_players_not_in_wl(player)
    
    async def kick_players_not_in_wl(self, player, **kwargs):
        for player_online in self.instance.player_manager.online:
                if player_online.login not in self.whitelist and player_online.level == 0:
                    await self.instance.gbx('Kick', player_online.login, 'You are not in the whitelist')
    
    async def deactivate(self, player, **kwargs):
        if(not self.active):
            await self.instance.chat('$f00Whitelist already deactivated!', player.login)
        else:
            self.active = False
            await self.instance.chat('$ff0Whitelist Deactivated')

    async def get_status(self, player, **kwargs):
        if(self.active):
            await self.instance.chat('Whitelist is $0C0activated', player.login)
        else:
            await self.instance.chat('Whitelist is $f00not activated', player.login)

    async def find_player_by_login_or_nickname(self, player_login_or_nickname):
        player_found = [p for p in self.instance.player_manager.online if p.nickname == player_login_or_nickname or p.login == player_login_or_nickname]
        return player_found

    async def add_player_from_server(self, player, data = None, **kwargs):
        player_found = await self.find_player_by_login_or_nickname(data.player)
        if not len(player_found) == 1:
            await self.instance.chat(f'{data.player} $f00is not found!', player.login)
        else:
            if player_found[0] not in self.whitelist:
                self.whitelist.append(player_found[0])
                await self.instance.chat(f'{player_found[0].nickname} $0C0added to the local whitelist!')
            else:
                await self.instance.chat(f'{player_found[0].nickname} $f00is already whitelisted locally!', player.login)
    
    async def add_player_login(self, player, data, **kwargs):
        if data.player_login not in self.whitelist:
            self.whitelist.append(data.player_login)
            await self.instance.chat(f'{data.player_login} $0C0added to the local whitelist!')
        else:
            await self.instance.chat(f'{data.player_login} $f00is already whitelisted locally!', player.login)

    async def add_players_from_view(self, player, logins, **kwargs):
        # Remove whitespaces and break lines 
        logins = logins.replace(' ', '')
        logins = logins.replace('\n', '')

        logins_list = logins.split(",")
        nbr = 0
        for login in logins_list:
            if login != "" and login not in self.whitelist:
                    self.whitelist.append(login)
                    nbr += 1
        await self.instance.chat(f'{player.nickname} $0C0added {nbr} logins to the local whitelist!')


    async def remove_player_login(self, player, data = None, **kwargs):
        if data.player not in self.whitelist:
            await self.instance.chat(f'{data.player} $f00is not on local Whitelist, cannot be removed!', player.login) 
        else:
            self.whitelist.remove(data.player)
            if self.active:
                target_player = await self.instance.player_manager.get_player(login=data['login'], lock=False)
                if target_player.level == 0:
                    await self.app.instance.gbx('Kick', target_player.login, 'You are not in the whitelist')
            await self.instance.chat(f'{data.player} $0C0removed from the local whitelist!')

    async def add_current_players(self, **kwargs): 
        self.whitelist = []
        for player_online in self.instance.player_manager.online:
                self.whitelist.append(player_online.login)
        await self.instance.chat('$ff0Local Whitelist with current Players and Spectators created!')

    async def show(self, player, **kwargs):
        whitelist_as_string = ""
        if self.whitelist == []:
            await self.instance.chat('$f00There is players in the local whitelist!', player.login)
        else:
            for i, player_in_wl in enumerate(self.whitelist):
                if i == len(self.whitelist) - 1:
                    whitelist_as_string += f'{player_in_wl}'
                else:
                    whitelist_as_string += f'{player_in_wl}, '
            await self.instance.chat(f'$ff0Players in the local whitelist: $fff{whitelist_as_string}', player.login)

    async def clear(self, player, **kwargs):
        self.whitelist = []
        if self.active:
            await self.kick_players_not_in_wl(player)
        await self.instance.chat('$0C0Local whitelist cleared!')

    async def show_commands(self, player, **kwargs):
        commands_string = ""
        commands = ['//wl whitelist | ', '//wl add $iplayernickname$z$s | ', '//wl addlogin $iplayerlogin$z$s | ', '//wl remove $iplayer$z$s | ', '//wl current | ', '//wl clear | ', '//wl show | ', '//wl on | ', '//wl off | ', '//wl status | ', '//wl help']
        await self.instance.chat(commands_string.join(commands), player.login)
    
    async def show_whitelist_window(self, player, *args, **kwargs):
        view = WhiteListView(self, self.whitelist)
        await view.show(player)

    
