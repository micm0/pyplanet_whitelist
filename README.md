# pyplanet_whitelist

### PyPlanet app that offers a Whitelist, which only lets certain people join

<p float="left">
    <img src="https://i.imgur.com/9DNapFd.jpg" alt="screenshot1" width="470"/>
    <img src="https://i.imgur.com/5MoeeqC.jpg" alt="screenshot2" width="470"/>
</p>

Working on Trackmania2020 and Trackmania²

### Behavior:

- When a player join the server, if the whitelist is activated and the player is not in the whitelist, he will be kicked from the server
- When an admin activate the whitelist, all players not in the whitelist will be kicked
- If the whitelist is already activated, if you remove a player from the whitelist he will be kicked, if you clear everyone will be kicked.  
  ! Players with admin roles are considered whitelisted even if they are not in the whitelist !

### Commands(if you prefer to use commands) :

`//whitelist` Show the whitelist window.  
`//wl help` Show available whitelist commands in the chat.  
`//wl add` _Parameter: player login or nickname._  
 Add a player(connected to the server) to the local whitelist with his login or nickname.  
`//wl addlogin` _Parameter: player login._  
 Add a player login to the local whitelist.  
`//wl remove` _Parameter: player login or nickname._  
 Remove a player login from the local whitelist.  
`//wl current` Create a new the local whitelist with all current connected players.  
`//wl clear` Clear the local whitelist.  
`//wl show` Show the player logins from the local whitelist in the chat.  
`//wl on` Activate the local whitelist.  
`//wl off` Deactivate the local whitelist.  
`//wl status` Show the status of the whitelist(on or off) in the chat.

The whitelist is saved only locally at the moment so it will be removed at the restart of pyplanet.  
Save in database coming soon

### Known bugs:

- The input of a manialink accept a maximum of 1024 characters(Nadeo limitation I guess) and there's no attribute to limit the number of characters.
  The manialink crash when we exceed the limit
