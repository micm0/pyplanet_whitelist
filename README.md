# pyplanet_whitelist

PyPlanet app that offers a Whitelist, which only lets certain people join

### Behavior:

When a player join the server, if the whitelist is activated and the player is not in the whitelist, he will be kicked from the server  
Players with admin roles are automatically whitelisted

### Commands :

`//wl help` Show available whitelist commands in the chat.  
`//wl add` _Parameter: player login or nickname._ Add a player to the local whitelist with his login or nickname.  
`//wl remove` _Parameter: player login or nickname._ Remove a player from the local whitelist with his login or nickname.  
`//wl current` Create a new the local whitelist with all current connected players.  
`//wl clear` Clear the local whitelist.  
`//wl show` Show the players from the local whitelist in the chat.  
`//wl on` Activate the local whitelist.  
`//wl off` Deactivate the local whitelist.

The whitelist is saved only locally at the moment so it will be removed at the restart of pyplanet.  
Save in database coming soon
