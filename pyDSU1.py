import socket
import struct
import zlib
from pprint import pprint

# protocol: https://github.com/v1993/cemuhook-protocol

class UDPDSU:
    MSG_TYP = {
        int(0x100000) : 'Protocol version information',
        int(0x100001) : 'Information about connected controllers',
        int(0x100002) : 'Actual controllers data',
        int(0x110001) : '(Unofficial) Information about controller motors', # unofficial
        int(0x110002) : '(Unofficial) Rumble controller motor'              # unofficial
    }
    def __init__(self, host="127.0.0.1", port=26760):
        self.host = host
        self.port = port

        # Create a UDP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        print(f"DSU server is running on {self.host}:{self.port}")
    
    def decode_packet(self, packet):
        magic_string, protocol_version, message_length, crc, client_id, message_type = struct.unpack('<4sHHLLL', packet[0:20])
        # print('magic_string:', magic_string)
        # print('protocol_version:', protocol_version)
        # print('message_length:', message_length)
        # print('crc:', crc)
        # print('client_id:', client_id)
        # print('message_type:', message_type)
        # print('message_type:', UDPDSU.MSG_TYP[message_type])
        
        return UDPDSU.MSG_TYP[message_type], message_type, packet[20:]


    def handle_dolphin_requests(self):
        while True:
            try:
                message, client_address = self.server_socket.recvfrom(1024)
                self.client_address = client_address

                # decode the message
                decoded_type, encoded_type, msg_data = self.decode_packet(message)

                # I was respnding to the wrong message from Dolphin! Before going any further, make a function for each of these scenarios,
                # use struct.unpack with the correct format based on the message type to decode the message from Dolphin
                # THEN AFTER ALL THAT, try sending the response again.
                if decoded_type == 'Protocol version information':
                    self.version_request(encoded_type, msg_data)
                elif decoded_type == 'Information about connected controllers':
                    pass
                elif decoded_type == 'Actual controllers data':
                    pass
                elif decoded_type == '(Unofficial) Information about controller motors':
                    pass
                elif decoded_type == '(Unofficial) Rumble controller motor':
                    pass

            except Exception as e:
                print(f"Error handling client: {e}")

    def send_packet(self, packet):
        self.server_socket.sendto(packet, self.client_address)

    def add_header_before(self, encoded_msg_type, packet_data):
        response1 = struct.pack("<4sHHLLL", b"DSUS", 1001, len(packet_data), 0, 0, encoded_msg_type)
        print('response1 len:', len(response1))

        response2 = struct.pack("<4sHHLLL", b"DSUS", 1001, len(packet_data), zlib.crc32(response1 + packet_data), 0, encoded_msg_type)
        print('response2 len:', len(response2))
        return response2 + packet_data
    
    def version_request(self, encoded_msg_type, msg_data):
        packet_data = struct.pack(b'H', 1001)
        self.send_packet( self.add_header(encoded_msg_type, packet_data) )

if __name__ == "__main__":
    server = UDPDSU()
    server.handle_dolphin_requests()
