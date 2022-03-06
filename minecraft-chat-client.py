from socket import socket, AF_INET, SOCK_STREAM
from struct import pack as data_pack
from contextlib import suppress
from random import randint
from time import sleep
from uuid import UUID, uuid4

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
    def handshake_forwarded(target, version, state, ip, uuid):
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.varint(version),
                              Minecraft.data(
                                  target[0].encode(),
                                  b"\x00",
                                  ip.encode(),
                                  b"\x00",
                                  uuid.hex.encode()
                              ),
                              Minecraft.short(target[1]),
                              
                              Minecraft.varint(state))
    
    @staticmethod
    def login(username):
        if isinstance(username, str):
            username = username.encode()
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.data(username))

target = ("185.105.237.4", 10170)
with suppress(KeyboardInterrupt):  
    with socket(AF_INET, SOCK_STREAM) as s:
        s.connect(target)
        data = Minecraft.handshake_forwarded(target, 47, 2, "0.0.0.0", uuid4())
        s.sendall(data)
        s.sendall(Minecraft.login("MH_ProDev"))
