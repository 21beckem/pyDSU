import eel
import json
import tkinter as tk
import threading

# Initialize the eel app
eel.init("web")

def center_screen(width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    return { 'x': int(x), 'y': int(y) }
root = tk.Tk()
root.withdraw()  # Hide the tkinter window

# Store player connections
players = {
    0 : None,
    1 : None,
    2 : None,
    3 : None
}
def getNextAvailableSlot():
    global players
    for i in range(4):
        if players[i] == None:
            return i
    return None
def clearReservedPlayer(id):
    global players
    for i in range(4):
        if players[i] == id + '_RESERVED':
            players[i] = None
def getPlayerIndexById(id):
    global players
    for i in range(4):
        if players[i] != None and players[i] == id:
            return i
    return None


@eel.expose
def EVENT_onPlayerJoin(id):
    global players
    i = getNextAvailableSlot()
    if i == None:
        return False
    print(f"Player {id} attempting to join slot {i}")
    players[i] = id + '_RESERVED'
    threading.Timer(5.0, clearReservedPlayer, args=[id]).start()
    return i + 1

@eel.expose
def EVENT_handshook(id):
    global players
    i = getPlayerIndexById(id + '_RESERVED')
    players[i] = id
    print(f"Player {id} successfully joined slot {i}")

@eel.expose
def EVENT_playerQuit(id, state):
    global players
    i = getPlayerIndexById(id)
    print(f"Player {id} left slot {i}")
    players[i] = None

@eel.expose
def EVENT_onPacket(id, data):
    global players
    i = getPlayerIndexById(id)
    print(f"Received packet from player {i}: {data}")



if __name__ == "__main__":
    window_width = 800
    window_height = 600
    geo = center_screen(window_width, window_height)
    eel.start("host.html", mode='edge', size=(window_width, window_height), position=(geo['x'], geo['y']))
