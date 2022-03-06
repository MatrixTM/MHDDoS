from socket import socket, AF_INET, SOCK_STREAM
from struct import pack as data_pack
from contextlib import suppress
from random import randint
from time import sleep
from uuid import UUID

class Minecraft:
    @staticmethod
    def varint(d):
        o = b''
        while True:
            b = d & 0x7F
            d >>= 7
            o += data_pack("B", b | (0x80 if d > 0 else 0))
            if d == 0:
                break
        return o
    
    @staticmethod
    def data(*payload):
        payload = b''.join(payload)
        return Minecraft.varint(len(payload)) + payload
    
    @staticmethod
    def short(integer):
        return data_pack('>H', integer)
    
    @staticmethod
    def handshake(target, version, state):
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.varint(version),
                              Minecraft.data(target[0].encode()),
                              Minecraft.short(target[1]),
                              Minecraft.varint(state))
    
    @staticmethod
    def login(username):
        if isinstance(username, str):
            username = username.encode()
        return Minecraft.data(Minecraft.varint(0x00)),

def varint_unpack(s):
    d, l = 0, 0
    length = len(s)
    if length > 5:
        length = 5
    for i in range(length):
        l += 1
        b = s[i]
        d |= (b & 0x7F) << 7 * i
        if not b & 0x80:
            break
    return (d, s[l:])

def data_unpack(bytes):
    length, bytes = varint_unpack(bytes)
    return bytes[:length], bytes[length:]


data = b'<\x00/6ggmc.ir\x005.127.169.134\x000010d32e8fc03a0b82dbd370c502497fc\xdd\x02'

data = varint_unpack(data) # size
data = varint_unpack(data[1]) #packet id
data = varint_unpack(data[1]) # idk
data = varint_unpack(data[1]) # idk

data = (data[1][:data[0]])
print(data)