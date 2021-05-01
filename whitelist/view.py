import asyncio

from pyplanet.views.generics.list import ManualListView
from pyplanet.views import TemplateView
from pyplanet.views.generics.alert import show_alert, ask_confirmation
from pyplanet.contrib.player.exceptions import PlayerNotFound

class WhiteListView(ManualListView):
    title = 'Whitelist'
    icon_style = 'Icons128x128_1'
    icon_substyle = 'ChallengeAuthor'

    def __init__(self, app, whitelist):
        """
        Initiate the Whitelist List View
        """
        super().__init__(self)
        self.app = app
        self.fields = self._create_fields()
        self.whitelist = whitelist
        self.manager = app.context.ui
        self.actions = self._create_actions()
        self.child = None

    async def show(self, player):
        await self.display(player=player)

    def _create_fields(self):
        return [
            {
                'name': 'Login',
                'index': 'login',
                'sorting': False,
                'searching': True,
                'width': 90,
                'type': 'label',
            },
            {
                'name': 'Nickname',
                'index': 'nickname',
                'sorting': False,
                'searching': True,
                'width': 90,
                'type': 'label',
            },
        ]
    
    async def get_buttons(self):
        buttons = [
            {
                'title': ' Clear',
                'width': 15,
                'action': self.action_clear
            },
            {
                'title': '  Add New Player(s)',
                'width': 30,
                'action': self.action_new_players
            },
            {
                'title': '  New List With Current Players',
                'width': 50,
                'action': self.action_current
            },
        ]
        if self.app.active:
            buttons.append({
                'title': '$F00 $fffDeactivate',
                'width': 20,
                'action': self.action_deactivate
            })
        else:
            buttons.append({
                'title': '$0C0 $fffActivate',
                'width': 20,
                'action': self.action_activate
            },)
        return buttons
    
    def _create_actions(self):
        return [
            dict(
                name='delete',
                action=self.delete,
                text='&#xF1F8;',
                textsize=1.2,
                safe=True,
                type='label',
                order=0,
                require_confirm=False,
            )
        ]

    async def get_data(self):
        items = []
        for player_login in self.whitelist:
            try:
                target_player = await self.app.instance.player_manager.get_player(login=player_login,lock=False)
                items.append({
                    'login': player_login,
                    'nickname': target_player.nickname,
                })
            except PlayerNotFound:
                items.append({
                    'login': player_login,
                    'nickname': 'Unknown',
                })
        # Sort by nickname
        items.sort(key=lambda x: x['nickname'].lower())
        
        return items
    
    async def action_current(self, player, values, **kwargs):
        await self.app.add_current_players()
        await self.close(player=player)
    
    async def action_clear(self, player, values, **kwargs):
        cancel = bool(
            await ask_confirmation(player, 'Do you really want to clear the whitelist ? If the whitelist is active, it will kick all the players without an admin role')
        )
        if not cancel:
            await self.app.clear(player)
            await self.close(player=player)

    async def action_activate(self, player, values, **kwargs):
        cancel = bool(
            await ask_confirmation(player, 'Do you really want to activate the whitelist ? That will kick all non admin players who are not in the whitelist')
        )
        if not cancel:
            await self.app.activate(player)
            await self.display(player=player)

    async def action_deactivate(self, player, values, **kwargs):
        await self.app.deactivate(player)
        await self.display(player=player)

    async def delete(self, player, values, data, **kwargs):
        cancel = bool(
            await ask_confirmation(player, 'Do you really want to delete this player {} | {}? If the whitelist is active, it will kick the player if he don\'t have an admin role'.format(data['login'], data['nickname']))
        )
        if not cancel:
            self.app.whitelist.remove(data['login'])
            await self.display(player=player)
            if self.app.active:
                target_player = await self.app.instance.player_manager.get_player(login=data['login'], lock=False)
                if target_player.level == 0:
                    await self.app.instance.gbx('Kick', target_player.login, 'You are not in the whitelist')
    
    async def action_new_players(self, player, values, **kwargs):
        if self.child:
            return

        self.child = NewPlayersView(self, player, self.app)
        await self.child.display()
        await self.child.wait_for_response()
        await self.child.destroy()
        await self.display(player)  # refresh.
        self.child = None

class WhiteListWidget(TemplateView):
    template_name = 'whitelist/whitelist.xml'

    def __init__(self, app, *args, **kwargs):
        """
        Initiate the Whitelist Button
        """
        super().__init__(*args, **kwargs)
        self.app = app
        self.manager = self.app.context.ui
        self.subscribe('bar_button_display', self.action_open_wl_view)

    async def action_open_wl_view(self, player, *args, **kwargs):
        return await self.app.instance.command_manager.execute(player, '//whitelist')

class NewPlayersView(TemplateView):
    """
    View to add new logins.
    """
    template_name = 'whitelist/new_players.xml'

    def __init__(self, parent, player, app):
        """
        Initiate child create view.

        :param parent: Parent view.
        :param player: Player instance.
        :param app: app instance.
        :type parent: pyplanet.view.base.View
        :type player: pyplanet.apps.core.maniaplanet.models.player.Player
        :type folder_manager: pyplanet.apps.contrib.jukebox.folders.FolderManager
        """
        super().__init__(parent.manager)

        self.parent = parent
        self.player = player
        self.app = app

        self.response_future = asyncio.Future()

        self.subscribe('button_close', self.close)
        self.subscribe('button_save', self.save)
        self.subscribe('button_cancel', self.close)

    async def display(self, **kwargs):
        await super().display(player_logins=[self.player.login])

    async def close(self, player, *args, **kwargs):
        """
        Close the link for a specific player. Will hide manialink and destroy data for player specific to save memory.

        :param player: Player model instance.
        :type player: pyplanet.apps.core.maniaplanet.models.Player
        """
        if self.player_data and player.login in self.player_data:
            del self.player_data[player.login]
        await self.hide(player_logins=[player.login])

        self.response_future.set_result(None)
        self.response_future.done()

    async def wait_for_response(self):
        return await self.response_future

    async def save(self, player, action, values, *args, **kwargs):
        """
        Save action.

        :param player: Player instance
        :param action: Action label
        :param values: Values from manialink
        :param args: *
        :param kwargs: **
        :type player: pyplanet.apps.core.maniaplanet.models.Player
        """

        # Get logins from input entry
        logins = values['player_login']

        # Add new player
        await self.app.add_players_from_view(player, logins)

        # Return response.
        self.response_future.set_result(None)
        self.response_future.done()