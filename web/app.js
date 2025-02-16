async function init() {
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

    Playroom.onPlayerJoin(async (player) => {
        let response = await eel.join_game(player.id)();
        if (response.success) {
            player.number = response.player_number;
            document.getElementById("playerCount").innerText = Object.keys(game.players).length;
            player.onQuit((state) => {
                console.log(`${state.id} quit!`);
                eel.player_left(player.number);
            });
            player.on("gyro", data => {
                eel.receive_gyro_data(player.number, data);
            });
        } else {
            await player.kick(response.message);
        }
    });
}
init();