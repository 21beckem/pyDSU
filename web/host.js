class Host {
    static PlayerSlots = {
        0 : null,
        1 : null,
        2 : null,
        3 : null
    };
    static IdSlotLookup = {};
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
            Host.PlayerSlots[slot-1] = new Pointer(slot-1, player.id);
            Host.IdSlotLookup[player.id] = slot-1;

            player.onQuit((state) => {
                console.log(`${state.id} quit!`);
                eel.EVENT_playerQuit(player.id, state);
                for (let thisSlot in Host.PlayerSlots) { // remove player locally as well
                    if (Host.PlayerSlots[thisSlot].id === player.id) {
                        Host.PlayerSlots[thisSlot].destroy();
                        Host.PlayerSlots[thisSlot] = null;
                        break;
                    }
                }
            });
            player.on('packet', data => {
                console.log(`New packet from ${player.id}!`, data);
                eel.EVENT_onPacket(player.id, data);
            });
        });
        Playroom.RPC.register('sendPacket', (data, player) => {
            eel.EVENT_onPacket(player.id, data);
            Host.PlayerSlots[Host.IdSlotLookup[player.id]].move(
                -data['gyro']['z'],
                -data['gyro']['x']
            );
        });
    }
}
class Pointer {
    constructor(slot, playerId) {
        this.id = playerId;
        this.pos = { x: 0, y: 0 };
        this.hoveredElements = [];
        this.DIV = document.createElement('div');
        this.DIV.setAttribute('class', `P${slot+1} pointer`);
        this.DIV.appendChild(document.createElement('div'));
        document.body.appendChild(this.DIV);
        this.center();
    }
    center() {
        this.moveTo(document.documentElement.clientWidth/2, document.documentElement.clientHeight/2);
    }
    moveTo(x, y) {
        this.pos = { x: x, y: y };
        this.DIV.style.left = `${x}px`;
        this.DIV.style.top = `${y}px`;
        this.handleMoveEvents();
    }
    move(x, y) {
        const speedFactor = 0.03; // Adjust this value to change the speed
        const xSpeed = document.documentElement.clientWidth * speedFactor;
        const ySpeed = document.documentElement.clientHeight * speedFactor;

        this.pos = { x: this.pos.x + x * xSpeed, y: this.pos.y + y * ySpeed };
        this.pos = {
            x: Math.min(Math.max(this.pos.x, 0), document.documentElement.clientWidth),
            y: Math.min(Math.max(this.pos.y, 0), document.documentElement.clientHeight)
        };
        this.DIV.style.left = `${this.pos.x}px`;
        this.DIV.style.top = `${this.pos.y}px`;
        this.handleMoveEvents();
    }
    handleMoveEvents() {
        let oldEls = [...this.hoveredElements];
        this.hoveredElements = [];
        document.elementsFromPoint(this.pos.x, this.pos.y).forEach(el => {
            if (el.tagName != 'BUTTON') return;
            if (el.classList.contains('pointer')) return;
            if (oldEls.includes(el)) {
                oldEls.splice(oldEls.indexOf(el), 1);
            }
            this.hoveredElements.push(el);
            el.classList.add('hover');
        });
        oldEls.forEach(e =>  e.classList.remove('hover') );
    }
    destroy() {
        this.DIV.remove();
    }
}
Host.init();