class Host {
    static async init() {
        await Playroom.insertCoin({
            skipLobby: true,
            maxPlayersPerRoom: 4
        });
        if (!Playroom.isHost()) {
            console.error("You are not the host! Try Again!");
            // refresh the page without any parameters
            window.location.href = window.location.href.split("#")[0];
            return;
        } else {
            console.log("New Game Started!");
        }
        document.getElementById("gameCode").innerText = Playroom.getRoomCode();
    
        // expose all events
        Playroom.onPlayerJoin(async (player) => {
            if (player.id == Playroom.me().id) return; // ignore the host
            console.log(`${player.id} joined!`);
            let slot = await eel.EVENT_onPlayerJoin(player.id)();
            if (!slot) {
                player.kick("Connection refused by host. Too many players.");
                return;
            }
            // send handshake
            player.setState('handshake', slot, true);
            console.log(`Handshake sent to ${player.id}`);
            await Playroom.waitForPlayerState(player, 'handshook');
            await eel.EVENT_handshook(player.id);
            console.log(`Connected! Slot: ${slot-1}`);
            await new Promise(r => setTimeout(r, 500)); // wait a bit to be sure the host registers the player

            player.onQuit((state) => {
                console.log(`${state.id} quit!`);
                eel.EVENT_playerQuit(player.id, state);
            });
            player.on("packet", data => {
                console.log(`New packet from ${player.id}!`, data);
                eel.EVENT_onPacket(player.id, data);
            });
        });
    }
}
Host.init();