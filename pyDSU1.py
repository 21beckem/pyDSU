import socket
import struct
import zlib

def create_version_response():
    """
    Create the DSU version response with the correct structure and CRC.
    :return: Version response packet (bytes).
    """
    # Response fields
    header = b"DSUC"  # Identifier
    protocol_version = 1001  # DSU protocol version (0x000003E9)
    message_length = 12  # Length of the message following the header
    crc_placeholder = 0  # Placeholder for CRC

    num_controllers = 4  # Number of supported controllers (adjustable)
    controllers_connected = 1  # How many controllers are connected

    # Step 1: Construct the header (without CRC)
    response = struct.pack(
        ">4sIHHI",  # Format: Identifier | Protocol Version | Length | Padding | CRC Placeholder
        header,
        protocol_version,
        message_length,
        0,  # Padding
        crc_placeholder,
    )

    # Step 2: Append controller-specific data
    response += struct.pack(">I", num_controllers)  # Number of controllers
    response += struct.pack(">I", controllers_connected)  # Controllers connected
    response += struct.pack(">I", 0)  # Reserved / Padding

    # Step 3: Calculate CRC for the response
    crc = zlib.crc32(response)
    response = response[:12] + struct.pack(">I", crc) + response[16:]  # Insert CRC at the correct offset

    return response

def handle_client(server_socket):
    """
    Handle incoming requests from Dolphin.
    :param server_socket: The UDP server socket.
    """
    while True:
        try:
            # Receive a message from Dolphin
            message, client_address = server_socket.recvfrom(1024)

            # Log the incoming message details
            print(f"Received {len(message)}-byte message from {client_address}: {message.hex()}")

            # Check if this is a version request (28 bytes long)
            if len(message) == 28:
                print(f"Recognized version request from {client_address}")

                # Create and send the version response
                response = create_version_response()
                server_socket.sendto(response, client_address)
                print(f"Sent version response to {client_address}")

        except Exception as e:
            print(f"Error handling client: {e}")

def start_dsu_server():
    """
    Start the DSU server.
    """
    # DSU server address and port
    host = "127.0.0.1"
    port = 26760

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"DSU server is running on {host}:{port}")

    # Handle incoming requests
    handle_client(server_socket)

if __name__ == "__main__":
    start_dsu_server()
