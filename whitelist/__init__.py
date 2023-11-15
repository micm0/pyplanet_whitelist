from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting
from .view import WhiteListView, WhiteListWidget

from .models import WhiteListPlayer


class Whitelist(AppConfig):
    name = 'whitelist'
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.whitelist = []
        self.widget = WhiteListWidget(self)
        self.active = False
        self.setting_activate_whitelist = Setting(
            'activate_whitelist', 'Whitelist activated', Setting.CAT_BEHAVIOUR,
            type=bool, description='', default=False
        )

        self.setting_chat_announce = Setting(
            'whitelist_chat_announce', 'Whitelist chat announces', Setting.CAT_BEHAVIOUR,
            type=bool, description='', default=False
        )

        self.setting_admin_widget = Setting(
            'whitelist_widget', 'Whitelist admin widget', Setting.CAT_BEHAVIOUR,
            type=bool, description='', default=False
        )

    async def on_start(self):
        await self.instance.permission_manager.register('admin', 'Administer the whitelist', app=self, min_level=2)
        await self.instance.command_manager.register(
            Command(command='add', namespace='wl', target=self.add_player_from_server_cmd, perms='whitelist:admin',
                    admin=True,
                    description='Add a player login to the whitelist with his login or nickname.').add_param(
                name='player', required=True),
            Command(command='addlogin', namespace='wl', target=self.add_player_login_cmd, perms='whitelist:admin',
                    admin=True, description='Add a player login to the whitelist.').add_param(name='player_login',
                                                                                                    required=True),
            Command(command='remove', namespace='wl', target=self.remove_player_cmd, perms='whitelist:admin',
                    admin=True, description='Remove a player login from the whitelist.').add_param(name='player',
                                                                                                         required=True),
            Command(command='current', namespace='wl', target=self.add_current_players, perms='whitelist:admin',
                    admin=True, description='Create a new the whitelist with all current connected players.'),
            Command(command='clear', namespace='wl', target=self.clear, perms='whitelist:admin', admin=True,
                    description='Clear the whitelist.'),
            Command(command='show', namespace='wl', target=self.show, perms='whitelist:admin', admin=True,
                    description='Show players from the whitelist in the chat.'),
            Command(command='on', namespace='wl', target=self.activate, perms='whitelist:admin', admin=True,
                    description='Activate the whitelist.'),
            Command(command='off', namespace='wl', target=self.deactivate, perms='whitelist:admin', admin=True,
                    description='Deactivate the whitelist.'),
            Command(command='help', namespace='wl', target=self.show_commands, perms='whitelist:admin', admin=True,
                    description='Show available whitelist commands in the chat.'),
            Command(command='status', namespace='wl', target=self.cmd_get_status, perms='whitelist:admin', admin=True,
                    description='Show the status of the whitelist(on or off) in the chat'),
            Command(command='whitelist', target=self.show_whitelist_window, perms='whitelist:admin', admin=True,
                    description='Show the whitelist window'),
        )
        self.context.signals.listen(mp_signals.player.player_connect, self.player_connect)

        await self.context.setting.register(self.setting_activate_whitelist,
                                            self.setting_chat_announce,
                                            self.setting_admin_widget)

        if await self.setting_admin_widget.get_value():
            # Display widget for admin roles
            for player in self.instance.player_manager.online:
                if player.level > 1:
                    await self.widget.display([player.login])

        # Load initial data.
        await self.refresh_whitelist()
        if self.active:
            await self.instance.chat('Whitelist is $0C0active')

    async def send_chat(self, message, player=None):
        announce = await self.setting_chat_announce.get_value()
        if not announce:
            return
        await self.instance.chat(message, player)

    async def player_connect(self, player, *args, **kwargs):
        # Display widget for admin roles
        if await self.setting_admin_widget.get_value() and player.level > 0:
            await self.widget.display([player.login])

        if not self.active:
            return

        # Check if player(not admin) is in the whitelist and kick him if not
        if player.level == 0:
            if not self.login_in_whitelist(player.login):
                await self.instance.gbx('Kick', player.login, 'You are not in the whitelist')
                await self.send_chat(f'{player.nickname} $ff0is not whitelisted!')
                return
        await self.send_chat(f'{player.nickname} $ff0is whitelisted!')

    async def activate(self, player, **kwargs):
        if self.active:
            await self.instance.chat('$f00Whitelist already active!', player.login)
            return

        await self.set_status(True)
        await self.instance.chat('$ff0Whitelist Activated')
        await self.kick_players_not_in_wl(player)

    async def kick_players_not_in_wl(self, player, **kwargs):
        for player_online in self.instance.player_manager.online:
            if player_online.level == 0 and not self.login_in_whitelist(player_online.login):
                await self.instance.gbx('Kick', player_online.login, 'You are not in the whitelist')

    async def deactivate(self, player, **kwargs):
        if not self.active:
            await self.instance.chat('$f00Whitelist already deactivated!', player.login)
            return

        await self.set_status(False)
        await self.instance.chat('$ff0Whitelist Deactivated')

    async def set_status(self, status):
        await self.setting_activate_whitelist.set_value(status)
        await self.refresh_whitelist()

    async def cmd_get_status(self, player, **kwargs):
        if self.active:
            await self.instance.chat('Whitelist is $0C0active', player.login)
        else:
            await self.instance.chat('Whitelist is $f00not activate', player.login)

    async def find_player_by_login_or_nickname(self, player_login_or_nickname):
        player_found = [p for p in self.instance.player_manager.online if
                        p.nickname == player_login_or_nickname or
                        p.login == player_login_or_nickname]
        return player_found

    async def add_player_from_server_cmd(self, player, data=None, **kwargs):
        player_found = await self.find_player_by_login_or_nickname(data.player)
        if len(player_found) < 1:
            await self.instance.chat(f'{data.player} $f00is not found!', player.login)
            return

        if self.login_in_whitelist(player_found[0].login):
            await self.instance.chat(f'{player_found[0].nickname} $f00is already whitelisted!', player.login)
            return

        await self.add_player(player_found[0].login)
        await self.refresh_whitelist()
        await self.instance.chat(f'{player_found[0].nickname} $0C0added to the whitelist!', player.login)

    async def add_player_login_cmd(self, player, data, **kwargs):
        if self.login_in_whitelist(data.player_login):
            await self.instance.chat(f'{data.player_login} $f00is already whitelisted!', player.login)
            return

        await self.add_player(data.player_login)
        await self.refresh_whitelist()
        await self.instance.chat(f'{data.player_login} $0C0added to the whitelist!')

    async def add_players_from_view(self, player, logins, **kwargs):
        # Remove whitespaces and break lines
        logins = logins.replace(' ', '')
        logins = logins.replace('\n', '')

        logins_list = logins.split(",")
        nbr = 0
        plural = ""
        for login in logins_list:
            if login != "" and not self.login_in_whitelist(login):
                await self.add_player(login)
                plural = "s"
                nbr += 1
        await self.refresh_whitelist()

        if nbr == 0:
            await self.instance.chat(f'$0C0{nbr} login added to the whitelist!', player.login)
        else:
            await self.send_chat(f'{player.nickname} $0C0added {nbr} login{plural} to the whitelist!')

    async def remove_player_from_view(self, player, login, **kwargs):
        await self.remove_player(login)
        if self.active and login in self.instance.player_manager.online_logins:
            target_player = await self.instance.player_manager.get_player(login=login, lock=False)
            if target_player.level == 0:
                await self.instance.gbx('Kick', target_player.login, 'You are not in the whitelist')

    async def remove_player_cmd(self, player, data=None, **kwargs):
        if not self.login_in_whitelist(data.player):
            await self.instance.chat(f'{data.player} $f00is not on whitelist, cannot be removed!', player.login)
            return
        await self.remove_player(data.player)
        if self.active and data.player in self.instance.player_manager.online_logins:
            target_player = self.instance.player_manager.get_player(login=data.player, lock=False)
            if target_player.level == 0:
                await self.instance.gbx('Kick', data.player, 'You are not in the whitelist')
        await self.instance.chat(f'{data.player} $0C0removed from the whitelist!', player.login)

    async def add_current_players(self, **kwargs):
        await self.remove_all_players()
        await self.add_players(self.instance.player_manager.online_logins)
        await self.instance.chat('$ff0Whitelist with current Players and Spectators created!')

    async def show(self, player, **kwargs):
        whitelist_as_string = ""
        if not self.whitelist:
            await self.instance.chat('$f00There is no players in the whitelist!', player.login)
            return

        for i, player_in_wl in enumerate(self.whitelist):
            if i == len(self.whitelist) - 1:
                whitelist_as_string += f'{player_in_wl.login}'
            else:
                whitelist_as_string += f'{player_in_wl.login}, '
        await self.instance.chat(f'$ff0Players in the whitelist: $fff{whitelist_as_string}', player.login)

    async def clear(self, player, **kwargs):
        await self.remove_all_players()
        if self.active:
            await self.kick_players_not_in_wl(player)
        await self.instance.chat('$0C0Whitelist cleared!', player.login)

    async def show_commands(self, player, **kwargs):
        commands_string = ""
        commands = ['//wl whitelist | ', '//wl add $iplayernickname$z$s | ', '//wl addlogin $iplayerlogin$z$s | ',
                    '//wl remove $iplayer$z$s | ', '//wl current | ', '//wl clear | ', '//wl show | ', '//wl on | ',
                    '//wl off | ', '//wl status | ', '//wl help']
        await self.instance.chat(commands_string.join(commands), player.login)

    async def show_whitelist_window(self, player, *args, **kwargs):
        window = WhiteListView(self)
        await window.show(player)

    def login_in_whitelist(self, login):
        return any(player_wl.login == login for player_wl in self.whitelist)

    """
    DB functions
    """

    async def refresh_whitelist(self):
        whitelist = await WhiteListPlayer.objects.execute(WhiteListPlayer.select())
        self.whitelist = list(whitelist)
        self.active = await self.setting_activate_whitelist.get_value()

    async def add_player(self, player_login):
        await WhiteListPlayer.execute(WhiteListPlayer.insert(login=player_login))

    async def add_players(self, players_login):
        logins = list()
        for login in players_login:
            logins.append({"login": login})
        await WhiteListPlayer.execute(WhiteListPlayer.insert_many(logins))
        await self.refresh_whitelist()

    async def remove_player(self, player_login):
        await WhiteListPlayer.execute(WhiteListPlayer.delete().where(WhiteListPlayer.login == player_login))
        await self.refresh_whitelist()

    async def remove_all_players(self):
        await WhiteListPlayer.execute(WhiteListPlayer.delete())
        await self.refresh_whitelist()
