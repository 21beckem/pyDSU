import eel
import json

# Initialize the eel app
eel.init("web")

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
        return {"success": True, "player_number": slot}
    return {"success": False, "message": "No available slots"}

@eel.expose
def receive_gyro_data(player_number, data):
    """Receive gyroscope data from players."""
    if player_number in players:
        print(f"Received data from Player {player_number}: {json.dumps(data)}")
    else:
        print("Received data from unknown player")

if __name__ == "__main__":
    eel.start("app.html", size=(600, 400), mode='edge')
