#https://wiki.python.org/moin/UdpCommunication
#https://v1993.github.io/cemuhook-protocol/

import socket
from tkinter import EventType
import binascii
import threading
import numpy as np
import time
import struct

def bytes_to_int(n):
    o = 0
    for i in n:
        o = (o << 8) + int(i)
    return o

def bytes_to_int_rev(n):
    o = 0
    for i in reversed(n):
        o = (o << 8) + int(i)
    return o

def int_to_byte_array(n, num):
    return [int(digit) for digit in np.binary_repr(n,width=num)]

def split_int_32(n):
    return [n >> 24 & 0xff, n >> 16 & 0xff, n >> 8 & 0xff, n & 0xff]

def split_int_16(n):
    return [n >> 8 & 0xff, n & 0xff]

def split_int_48_rev(n):
    return [n & 0xff, n >> 8 & 0xff, n >> 16 & 0xff, n >> 24 & 0xff, n >> 32 & 0xff, n >> 40 & 0xff]

def split_int_32_rev(n):
    return [n & 0xff, n >> 8 & 0xff, n >> 16 & 0xff, n >> 24 & 0xff]

def split_int_16_rev(n):
    return [n & 0xff, n >> 8 & 0xff]

def get_timestamp_split():
    timestamp_us = int(time.time() * 1_000_000)
    
    # Pack the timestamp into a 64-bit unsigned integer
    packed_timestamp = struct.pack(">Q", timestamp_us)

    # Unpack into two 32-bit unsigned integers
    high_bits, low_bits = struct.unpack(">II", packed_timestamp)
    
    return high_bits, low_bits


class CEMUMessage:
    def __init__(self, data):
        CRCTestPacket = [data[i:i + 1] for i in range(0, len(data), 1)]
        #print(CRCTestPacket)
        CRCTestPacket[8] = b'\x00'
        CRCTestPacket[9] = b'\x00'
        CRCTestPacket[10] = b'\x00'
        CRCTestPacket[11] = b'\x00'
        #print(CRCTestPacket)
        CRCTestPacketCombined = b''
        for i in CRCTestPacket:
            CRCTestPacketCombined += i
        self.intendedCRC32 = binascii.crc32(CRCTestPacketCombined)

        self.bytes = data#[data[i:i + 1] for i in range(0, len(data), 1)]
        self.owner =self.bytes[0:4].decode('UTF-8')
        self.protocol = bytes_to_int_rev(self.bytes[4:6]) & 0xffff
        self.length = bytes_to_int_rev(self.bytes[6:8]) & 0xffff
        self.CRC32 = bytes_to_int_rev(self.bytes[8:12]) & 0xffffffff
        self.senderID = bytes_to_int_rev(self.bytes[12:16]) & 0xffffffff
        self.eventType = bytes_to_int_rev(self.bytes[16:20]) & 0xffffffff
        self.type = 0 # 0 is Blank, 1 is protocol info, 2 is info about connected controllers, 3 is actual controller data
        if(self.eventType == 1048576):
            self.type = 1
        elif(self.eventType == 1048577):
            self.type = 2
        elif(self.eventType == 1048578):
            self.type = 3
        self.data = self.bytes[20:32]

        # self.controllerID, self.controllerType,
        # if(self.eventType == 2 || self.eventType = 3):
            



    def print(self):
        print("---------")
        print("Owner: %s" % self.owner)
        print("Protocol: %s" % self.protocol)
        print("Length: %s" % self.length)
        print("Entire Length: %s" % len(self.bytes))
        print("Intended CRC32: %s" % self.intendedCRC32)
        print("Recieved CRC32: %s" % self.CRC32)
        print("Sender ID: %s" % self.senderID)
        print("Event Type: 0x%x" % self.eventType)
        print("Data: ",end="")
        if(self.type == 2):
            if(self.owner == "DSUS"):
                print()
                print("- ID: #%i" % (int.from_bytes(self.data[0:1], "big") + 1), )
                print("- Connected?: %i" % int.from_bytes(self.data[1:2], "big"))
                print("- Model: %i" % int.from_bytes(self.data[2:3], "big"))
                print("- Connection: %i" % int.from_bytes(self.data[3:4], "big"))
                print("- MAC: 0x%x" % int.from_bytes(self.data[4:10], "big"))
                print("- Battery: 0x%x" % int.from_bytes(self.data[10:11], "big"))
            elif(self.owner == "DSUC"):
                print()
                num = int.from_bytes(self.data[0:4], "big")
                print("- # of Controller: %i" % num)
                print("- Controllers: ", end="")
                for i in self.data[4:4+num]:
                    print(i, end="")
                    print(", ", end="")
                print()

        else:
            print(self.data)
        print("---------")

    @staticmethod
    def construct(id, eventType, data):
        message = bytearray()
        message += b'DSUS'
        message += b'\xe9' + b'\x03'
        message += bytearray(split_int_16_rev(len(data) + 4))
        message += b'\x00\x00\x00\x00' #CRC32 PLACEHOLDER
        message += bytearray(split_int_32_rev(id))
        message += bytearray(split_int_32_rev(eventType))
        message += data
        crc = split_int_32_rev(binascii.crc32(message))
        for i in range(4):
            message[8 + i] = crc[0 + i]
        #print(returnMsg)
        return CEMUMessage(message)

    def constructResponse(id, eventType, controllerID, connectStatus, controllerType, connectType, MACaddr, battery, data = b'\0'):
        packet = bytearray([controllerID, connectStatus, controllerType, connectType])
        packet += bytearray(split_int_48_rev(MACaddr))
        packet += bytearray([battery])
        packet += data
        return CEMUMessage.construct(id, eventType, packet)
    
    def constructRemoteData(id, eventType, controllerID, connectStatus, controllerType, connectType, MACaddr, battery, isConnected, packetNumber, dpadL, dpadD, dpadR, dpadU, start, r3, l3, select, y, b, a, x, r1, l1, r2, l2, homeB, touchB, lX, lY, rX, rY, accelX, accelY, accelZ, gyroPitch, gyroYaw, gyroRoll):
        packet = bytearray([controllerID, connectStatus, controllerType, connectType])
        packet += bytearray(split_int_48_rev(MACaddr))
        packet += bytearray([battery, isConnected])
        packet += bytearray(split_int_32_rev(packetNumber))

        packet += bytearray([bytes_to_int([dpadL, dpadD, dpadR, dpadU, start, r3, l3, select])])
        packet += bytearray([bytes_to_int([y, b, a, x, r1, l1, r2, l2])])
        packet += bytearray([homeB, touchB, lX, lY, rX, rY])

        packet += bytearray([dpadL, dpadD, dpadR, dpadU, y, b, a, x, r1, l1, r2, l2])
        packet += bytearray(split_int_48_rev(0))
        packet += bytearray(split_int_48_rev(0))
        hiTime, loTime = get_timestamp_split()
        packet += bytearray(split_int_32_rev(hiTime))
        packet += bytearray(split_int_32_rev(loTime))

        packet += bytearray(split_int_32_rev(accelX))
        packet += bytearray(split_int_32_rev(accelY))
        packet += bytearray(split_int_32_rev(accelZ))
        packet += bytearray(split_int_32_rev(gyroPitch))
        packet += bytearray(split_int_32_rev(gyroYaw))
        packet += bytearray(split_int_32_rev(gyroRoll))
        return CEMUMessage.construct(id, eventType, packet)

connectedToDolphin = False
DolphinAddr = None
testVar = 0
packetNum = 0
def sendControllerData():
    global testVar, connectedToDolphin, packetNum
    if not connectedToDolphin:
        return
    atxMsg = CEMUMessage.constructRemoteData(
        28592813, # id
        0x100001, # type
        0,        # slotID
        2,        # connection status
        2,        # controller type
        0,        # connection type
        0,        # MAC
        0x03,     # battery
        1,        # is connected
        packetNum,# packet number
        0,        # dpad left
        0,        # dpad down
        0,        # dpad right
        0,        # dpad up
        0,        # start
        0,        # r3
        0,        # l3
        0,        # start
        0,        # y
        0,        # b
        0,        # a
        0,        # x
        0,        # r1
        0,        # l1
        0,        # r2
        0,        # l2
        testVar,  # home button
        testVar,  # touch button
        0,        # lX
        255,        # lY
        0,        # rX
        0,        # rY
        0,        # accelX
        0,        # accelY
        0,        # accelZ
        0,        # gyroPitch
        0,        # gyroYaw
        0         # gyroRoll
    )
    atxMsg.print()
    sock.sendto(atxMsg.bytes, DolphinAddr)
    packetNum += 1
    if(testVar == 0):
        testVar = 1
    else:
        testVar = 0

def sendControllerDataThreadFunc():
    while True:
        sendControllerData()
        time.sleep(1/10)

sendControllerDataThread = threading.Thread(target=sendControllerDataThreadFunc, daemon=True)
# sendControllerDataThread.start()

UDP_IP = "127.0.0.1"
UDP_PORT = 26760

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
print("UDP server up and listening")
while True:
    data, DolphinAddr = sock.recvfrom(128) # buffer size is 1024 bytes
    #bytes = [data[i:i + 1] for i in range(0, len(data), 1)]
    rxMsg = CEMUMessage(data)
    # rxMsg.print()
    print(DolphinAddr)
    if(rxMsg.type == 2):
        print("RESPONSE")
        atxMsg = CEMUMessage.constructResponse(28592813,0x100001,0,2,2,2,0,3)
        sock.sendto(atxMsg.bytes, DolphinAddr)
        connectedToDolphin = True
    elif(rxMsg.type == 3):
        print("REMOTE DATA")
        sendControllerData()


    # txMsg = CEMUMessage.construct(28592813,0x100001,b'\x00\x01\x02\x02\x00\x00\x00\x00\x00\x00\x04\x00')
    # txMsg.print()
    
    try:
        pass
    except KeyboardInterrupt:
        print('\nExiting...')
        exit(0)
