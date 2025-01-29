import socket
import struct
import zlib

# protocol: https://github.com/v1993/cemuhook-protocol

class UDPDSU:
    MSG_TYP = {
        'protocol_version': int(0x100000),
        'connected_controllers': 0x100001,
        'controller_data': 0x100002,
        'information_about_motors': 0x110001,  # unofficial
        'rumble_motor' : 0x110002              # unofficial
    }
    def __init__(self, host="127.0.0.1", port=26760):
        self.host = host
        self.port = port

        # Create a UDP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        print(f"DSU server is running on {self.host}:{self.port}")

    def handle_dolphin_requests(self):
        while True:
            try:
                message, client_address = self.server_socket.recvfrom(1024)
                self.client_address = client_address
                print(f"Received {len(message)}-byte message from {client_address}: {message.hex()}")
                print( repr(message) )

                # Check if this is a version request (28 bytes long)
                if len(message) == 28:
                    print(f"Recognized version request from {client_address}")

                    # Create and send the version response
                    response = self.version_request()
                    print( repr(response) )
                    self.send_packet(response)
                    print(f"Sent version response to {client_address}")

            except Exception as e:
                print(f"Error handling client: {e}")

    def send_packet(self, packet):
        self.server_socket.sendto(packet, self.client_address)

    def add_header_before(self, packet_data):
        magic_string = b"DSUC"
        protocol_version = 1001
        message_length = len(packet_data)
        crc_placeholder = 0
        client_id = 0

        response1 = struct.pack(">4sIHLL", magic_string, protocol_version, message_length, crc_placeholder, client_id)
        
        crc = zlib.crc32(response1 + packet_data)

        return struct.pack(">4sIHLL", magic_string, protocol_version, message_length, crc, client_id) + packet_data
    
    def version_request(self):
        chars = b'H'
        protocol_version = 1001
        packet_data = struct.pack(chars, protocol_version)
        return self.add_header_before(packet_data)

if __name__ == "__main__":
    server = UDPDSU()
    server.handle_dolphin_requests()
