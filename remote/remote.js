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
        GUI.attemptFullscreen();
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

        // start sending packets to the host
        Remote.sendPackets();
    }
    static Acel = null;
    static Gyro = null;
    static sendPackets() {
        if (DeviceMotionEvent && typeof DeviceMotionEvent.requestPermission === "function") { // request permission for IOS 13+ devices
            DeviceMotionEvent.requestPermission();
        }
        if ('Accelerometer' in window && 'Gyroscope' in window) { // if remote device supports motion
            Remote.Acel = new Accelerometer({ frequency: 60 });
            Remote.Gyro = new Gyroscope({ frequency: 60 });
            Remote.Gyro.addEventListener('reading', e => {
                Playroom.RPC.call('sendPacket', {
                    buttons : GUI.buttons,
                    acc : {
                        x: Remote.Acel.x,
                        y: Remote.Acel.y,
                        z: Remote.Acel.z
                    },
                    gyro : {
                        x: e.target.x,
                        y: e.target.y,
                        z: e.target.z
                    }
                }, Playroom.RPC.Mode.HOST);
                console.log('sent packet');
            }, true);
            Remote.Acel.addEventListener('error', (event) => {
                console.error('Accelerometer error:', event);
            });
            Remote.Gyro.addEventListener('error', (event) => {
                console.error('Gyroscope error:', event);
            });
            Remote.Acel.start();
            Remote.Gyro.start();
        } else { // if remote device doesn't support motion
            alert('This device does not support motion. If you beleive this is a mistake, please click here for assistance.');
            setInterval(() => {
                console.log('Packet sending...');
                Playroom.RPC.call('sendPacket', {
                    buttons : GUI.buttons,
                    acc : {
                        x: 0, y: 0, z: 0
                    },
                    gyro : {
                        a: 0, b: 0, g: 0
                    }
                }, Playroom.RPC.Mode.HOST);
                console.log('Packet sent!');
            }, 1000/60);
        }
    }
}
Remote.init();