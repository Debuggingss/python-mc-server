# python-mc-server
A simple socket server that responds to Minecraft ping and login attempt packets.

This is NOT meant to be a playable server. It lacks every feature.

Features:
- Respond to ping packet

![motd](https://i.debuggings.dev/Mb4UzVVP.gif)

![player list](https://i.debuggings.dev/y1AVD9rb.png)

- Kick player on login attempt

![kicked](https://i.debuggings.dev/Dk35m38l.png)

And that's about it. Again, it's more of a proof of concept. For an actual server implementation I highly recommend checking out [Minestom](https://minestom.net/) or [node-minecraft-protocol](https://github.com/PrismarineJS/node-minecraft-protocol).

I hope this can help at least one person someday, somehow.

Credits:
- [wiki.vg - Server List Ping](https://wiki.vg/Server_List_Ping)
- [wiki.vg - Disconnect (login)](https://wiki.vg/Protocol#Disconnect_(login))
- [Lonami/mc-ping.py](https://gist.github.com/Lonami/b09fc1abb471fd0b8b5483d54f737ea0)
- [ewized/statusping.py](https://gist.github.com/ewized/97814f57ac85af7128bf)
