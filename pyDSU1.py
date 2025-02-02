import socket
import struct
import binascii
import threading
import time
from pprint import pprint

# protocol: https://github.com/v1993/cemuhook-protocol

class FONEMOTE:
    MSG_TYP = {
        int(0x100000) : 'Protocol version information',
        int(0x100001) : 'Information about connected controllers',
        int(0x100002) : 'Actual controllers data',
        int(0x110001) : '(Unofficial) Information about controller motors', # unofficial
        int(0x110002) : '(Unofficial) Rumble controller motor'              # unofficial
    }
    def __init__(self, host='127.0.0.1', port=26760, startServer=False):
        self.host = host
        self.port = port
        self.controller_states = [
            {
                'dolphin_requested': False,
                'slot_state': 0,
                'connected_state': 0,
                'packet_number': 40,
                'data': {
                    'Home Btn': 0,
                    'Plus Btn': 0,
                    'Minus Btn': 0,
                    'A Btn': 0,
                    'B Btn': 0,
                    '1 Btn': 0,
                    '2 Btn': 0,
                    'D-Pad Left': 0,
                    'D-Pad Down': 0,
                    'D-Pad Right': 0,
                    'D-Pad Up': 0,
                    'timestamp': 0,
                    'AccelerometerX': 0.0,
                    'AccelerometerY': 0.0,
                    'AccelerometerZ': 0.0,
                    'Gyroscope_Pitch': 0.0,
                    'Gyroscope_Yaw': 0.0,
                    'Gyroscope_Roll': 0.0
                }
            }
            for _ in range(4)
        ]

        if startServer:
            self.start_server()
    
    def compute_crc(self, packet: bytearray, crc_field_range=(8, 12)) -> int:
        # Create a copy so we don't modify the original packet
        p = bytearray(packet)
        # Zero out the bytes corresponding to the CRC field
        start, end = crc_field_range  # end is non-inclusive, so [4,8) zeroes bytes 4,5,6,7.
        for i in range(start, end):
            p[i] = 0
        # Compute and return the CRC32 value
        return binascii.crc32(p) & 0xffffffff
    
    def decode_packet(self, packet):
        # print('received packet:', packet)
        magic_string, protocol_version, message_length, crc, client_id, message_type = struct.unpack('<4sHHLLL', packet[0:20])
        # print('magic_string:', magic_string)
        # print('protocol_version:', protocol_version)
        # print('message_length:', message_length)
        # print('crc:', crc)
        # print('client_id:', client_id)
        # print('message_type:', message_type)
        print('message_type:', FONEMOTE.MSG_TYP[message_type])
        
        return FONEMOTE.MSG_TYP[message_type], message_type, packet[20:]


    def start_server(self):
        # Create a UDP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        print(f'DSU server is running on {self.host}:{self.port}')

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
                    self.controller_info_request(encoded_type, msg_data)
                elif decoded_type == 'Actual controllers data':
                    self.actual_controller_data_request(encoded_type, msg_data)
                elif decoded_type == '(Unofficial) Information about controller motors':
                    pass
                elif decoded_type == '(Unofficial) Rumble controller motor':
                    pass

            except Exception as e:
                print(f'Error handling client: {e}')

    def send_packet(self, packet):
        self.server_socket.sendto(packet, self.client_address)

    def add_header(self, encoded_msg_type, packet_data, override_crc=0):
        packet_data = struct.pack(b'<L', encoded_msg_type) + packet_data

        response1 = struct.pack('<4sHHLL', b'DSUS', 1001, len(packet_data), 0, 0)
        # print('response1 len:', len(response1))

        # crc = 0x15542c26
        if override_crc == 0:
            crc = self.compute_crc(response1 + packet_data)
        else:
            crc = override_crc
        # print('crc:', hex(crc))

        response2 = struct.pack('<4sHHLL', b'DSUS', 1001, len(packet_data), crc, 0)
        # print('response2 len:', len(response2))
        full_packet = response2 + packet_data
        # print('full_packet:', full_packet)
        # print('packet len:', len(full_packet))
        # print('second crc:', hex( binascii.crc32(full_packet) ))
        return full_packet
    
    def create_controller_info_intro(self, slot):
        return struct.pack(b'<BBBB', int(slot), int(self.controller_states[slot]['slot_state']), 0, 0) + struct.pack('<Q', 0)[:6] + struct.pack(b'<B', 0x04)
    
    def version_request(self, encoded_msg_type, msg_data):
        packet_data = struct.pack(b'<H', 1001)
        self.send_packet( self.add_header(encoded_msg_type, packet_data) )
    
    def controller_info_request(self, encoded_msg_type, msg_data):
        # read rest of msg_data
        # print('msg_data:', msg_data)
        nOfPorts = struct.unpack('<l', msg_data[0:4])[0]
        ports_bytes = msg_data[4:]
        # print('nOfPorts:', nOfPorts)
        ports = []
        for i in range(nOfPorts):
            ports.append( int(struct.unpack('<B', ports_bytes[0:1])[0]) )
            ports_bytes = ports_bytes[1:]
        
        for port in ports:
            # create packet reporting on the port
            packet_data = self.create_controller_info_intro(port) + struct.pack(b'<B', 0)

            self.send_packet( self.add_header(encoded_msg_type, packet_data) )

    def actual_controller_data_request(self, encoded_msg_type, msg_data):
        #read rest of msg_data
        bitMask, slot, macLow, macHigh = struct.unpack('<BBIH', msg_data)
        macAddr = (macHigh << 24) | macLow
        print(f'bitMask: {bitMask}, slot: {slot}, macAddr: {macAddr}')

        if not (bitMask == 0 or bitMask == 1):
            print('Fatal error: bitMask is not 0 or 1. FONEMOTE does not support MACaddress based subscriptions.')
        
        self.controller_states[slot]['dolphin_requested'] = True
    
### start CONTROLLER Specific Functions

    def setControllerState(self, slot, state):
        if state == 0:
            self.controller_states[slot]['slot_state'] = state
            self.controller_states[slot]['connected_state'] = state
        else:
            self.controller_states[slot]['slot_state'] = 2
            self.controller_states[slot]['connected_state'] = 1

    def sendControllerData(self, slot, data):
        self.controller_states[slot]['data'] = data

        ### construct the packet
        packet = self.create_controller_info_intro(slot)
        packet += struct.pack(b'<BIBBBBBBBBBBBBBBBBBBBBBBHHBBHHQffffff',
            self.controller_states[slot]['connected_state'],
            self.controller_states[slot]['packet_number'],
            0,0,
            data['Home Btn'],
            0,0,0,0,0,
            data['D-Pad Left'] * 255,
            data['D-Pad Down'] * 255,
            data['D-Pad Right'] * 255,
            data['D-Pad Up'] * 255,
            data['A Btn'] * 255,
            data['B Btn'] * 255,    
            data['1 Btn'] * 255,
            data['2 Btn'] * 255,
            data['Plus Btn'] * 255,
            data['Minus Btn'] * 255,
            0,0,
            0,0,0,0,
            0,0,0,0,
            data['timestamp'],
            data['AccelerometerX'],
            data['AccelerometerY'],
            data['AccelerometerZ'],
            data['Gyroscope_Pitch'],
            data['Gyroscope_Yaw'],
            data['Gyroscope_Roll']
        )
        packet = self.add_header(int(0x100002), packet)

        print('packet len', len(packet))
        print('packet number', self.controller_states[slot]['packet_number'])
        self.send_packet( packet )

        self.controller_states[slot]['packet_number'] += 1


        


if __name__ == '__main__':
    foneMotes = FONEMOTE()
    server_thread = threading.Thread(target=foneMotes.start_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    foneMotes.setControllerState(0, 1)
    while True:
        v = 0
        foneMotes.sendControllerData(0, {
            'Home Btn': v,
            'Plus Btn': 0,
            'Minus Btn': 0,
            'A Btn': 0,
            'B Btn': 0,
            '1 Btn': 0,
            '2 Btn': 0,
            'D-Pad Left': 0,
            'D-Pad Down': 0,
            'D-Pad Right': 0,
            'D-Pad Up': 0,
            'timestamp': 0,
            'AccelerometerX': 0.0,
            'AccelerometerY': 0.0,
            'AccelerometerZ': 0.0,
            'Gyroscope_Pitch': 0.0,
            'Gyroscope_Yaw': 0.0,
            'Gyroscope_Roll': 0.0
        })
        v += 1
        if v > 1:
            v = 0
        time.sleep(1.5)
