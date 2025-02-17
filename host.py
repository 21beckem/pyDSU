import eel
import json
import tkinter as tk

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
players = {}
MAX_PLAYERS = 4

def get_available_slot():
    """Find the next available player slot."""
    for i in range(MAX_PLAYERS):
        if i not in players:
            return i
    return None

@eel.expose
def join_game(player_id):
    """Handle a player attempting to join the game."""
    if len(players) >= MAX_PLAYERS:
        return {"success": False, "message": "Game is full"}
    
    slot = get_available_slot()
    if slot is not None:
        players[slot] = player_id
        return {"success": True, "slot": slot}
    return {"success": False, "message": "No available slots"}

@eel.expose
def player_left(slot):
    """Handle a player leaving the game."""
    del players[slot]

@eel.expose
def receive_gyro_data(slot, data):
    """Receive gyroscope data from players."""
    if slot in players:
        print(f"Received data from Player {slot}: {json.dumps(data)}")
    else:
        print("Received data from unknown player")

if __name__ == "__main__":
    window_width = 800
    window_height = 600
    geo = center_screen(window_width, window_height)
    eel.start("host.html", mode='edge', size=(window_width, window_height), position=(geo['x'], geo['y']))
