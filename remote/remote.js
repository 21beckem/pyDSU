class Remote {
    static init() {
        // attempt to connect to the host if room code is in hash
        if (window.location.hash) {
            Remote.connectWithCode();
        }
    }
    static async connectWithCode(code='') {
        if (code == '' && !window.location.hash.includes('#r=')) {
            console.error("No game code provided!");
            return;
        }
        // if trying to use differnent code than in the hash, be sure that the hash won't mess with that
        if (code != '') {
            window.location.hash = '';
        }
        await Playroom.insertCoin({
            skipLobby: true,
            roomCode: code
        });
        if (Playroom.isHost()) {
            console.error("You are the host, not good! Try Again!");
            // refresh the page without any parameters
            window.location.hash = '';
            window.location = window.location.pathname;
        }
        console.log('waiting for handshake...');
        
        let slot = await Playroom.waitForPlayerState(Playroom.me(), 'handshake');
        Playroom.me().setState('handshook', slot, true);
        slot -= 1;

        Remote.showRemotePage();
        GUI.setSlot(slot);
    }
    static showRemotePage() {
        _('connectPage').style.display = 'none';
        _('RemotePage').style.display = '';
        GUI.setBposition();
    }
}
Remote.init();