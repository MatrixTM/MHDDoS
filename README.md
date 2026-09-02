<div align="center">

# MHDDoS

### DDoS Testing Toolkit · 57 Methods · Python 3

<p>
  <a href="https://github.com/MatrixTM/MHDDoS/network/members"><img src="https://img.shields.io/github/forks/MatrixTM/MHDDoS?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/MatrixTM/MHDDoS/commits/main"><img src="https://img.shields.io/github/last-commit/MatrixTM/MHDDoS/main?color=green&style=for-the-badge" alt="Last commit"></a>
  <a href="https://github.com/MatrixTM/MHDDoS/stargazers"><img src="https://img.shields.io/github/stars/MatrixTM/MHDDoS?style=for-the-badge&color=yellow" alt="Stars"></a>
  <a href="https://github.com/MatrixTM/MHDDoS/blob/main/LICENSE"><img src="https://img.shields.io/github/license/MatrixTM/MHDDoS?color=orange&style=for-the-badge" alt="License"></a>
  <a href="https://github.com/MatrixTM/MHDDoS/issues"><img src="https://img.shields.io/github/issues/MatrixTM/MHDDoS?color=purple&style=for-the-badge" alt="Issues"></a>
</p>

**For authorized testing and educational use only.**  
Do not attack systems, websites, or networks without the owner's explicit permission.

[**Download**](#-downloads) · [**Features**](#-features--methods) · [**Installation**](#-getting-started) · [**Docker**](#-docker) · [**Documentation**](#-documentation) · [**Community**](#-community) · [**Hosting**](#%EF%B8%8F-hosting)

</div>

---

<p align="center">
  <img src="https://i.imgur.com/aNrHJcA.png" width="100%" alt="MHDDoS preview">
</p>

<p align="center">
  <img src="https://i.imgur.com/4Q7v2wn.png" width="100%" alt="MHDDoS script preview">
</p>

---

## ⚠️ Important Notice

> [!CAUTION]
> **MHDDoS is 100% free.** Do **not** send money to anyone claiming to sell this project. If someone asks you to pay for MHDDoS, treat it as a scam.

> [!WARNING]
> Use this project only on infrastructure you own or have explicit authorization to test.

---

## ✨ Features & Methods

MHDDoS includes methods for multiple network layers, utility commands, and console helpers.

### 💣 Layer 7

| Icon | Method | Description |
|:---:|:---:|---|
| <img src="https://img.icons8.com/cotton/344/domain.png" width="20" height="20" alt="GET"> | `GET` | GET Flood |
| <img src="https://cdn0.iconfinder.com/data/icons/database-storage-5/60/server__database__fire__burn__safety-512.png" width="20" height="20" alt="POST"> | `POST` | POST Flood |
| <img src="https://ovh.github.io/manager/ovhcloud-logo.webp" width="20" height="20" alt="OVH"> | `OVH` | Bypass OVH |
| <img src="https://cdn-icons-png.flaticon.com/512/1691/1691948.png" width="20" height="20" alt="RHEX"> | `RHEX` | Random HEX |
| <img src="https://cdn-icons-png.flaticon.com/512/4337/4337972.png" width="20" height="20" alt="STOMP"> | `STOMP` | Bypass `chk_captcha` |
| <img src="https://cdn.iconscout.com/icon/premium/png-256-thumb/cyber-bullying-2557797-2152371.png" width="20" height="20" alt="STRESS"> | `STRESS` | Send HTTP packets with high byte payloads |
| <img src="https://cdn.worldvectorlogo.com/logos/dyndns.svg" width="20" height="20" alt="DYN"> | `DYN` | Random subdomain method |
| <img src="https://cdn-icons-png.flaticon.com/512/6991/6991643.png" width="20" height="20" alt="DOWNLOADER"> | `DOWNLOADER` | Slow data-reading method |
| <img src="https://cdn2.iconfinder.com/data/icons/poison-and-venom-fill/160/loris2-512.png" width="20" height="20" alt="SLOW"> | `SLOW` | Slowloris method |
| <img src="https://lyrahosting.com/wp-content/uploads/2020/06/ddos-how-work-icon.png" width="20" height="20" alt="HEAD"> | `HEAD` | HTTP HEAD method |
| <img src="https://img.icons8.com/plasticine/2x/null-symbol.png" width="20" height="20" alt="NULL"> | `NULL` | Null User-Agent and related headers |
| <img src="https://i.pinimg.com/originals/03/2e/7d/032e7d0755cd511c753bcb6035d44f68.png" width="20" height="20" alt="COOKIE"> | `COOKIE` | Random Cookie method |
| <img src="https://cdn0.iconfinder.com/data/icons/dicticons-files-folders/32/office_pps-512.png" width="20" height="20" alt="PPS"> | `PPS` | Minimal `GET / HTTP/1.1` request |
| <img src="https://cdn3.iconfinder.com/data/icons/internet-security-14/48/DDoS_website_webpage_bomb_virus_protection-512.png" width="20" height="20" alt="EVEN"> | `EVEN` | GET method with additional headers |
| <img src="https://iili.io/HU9BC74.png" width="20" height="20" alt="GSB"> | `GSB` | Google Project Shield bypass |
| <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/DDoS-Guard_logo.svg/1280px-DDoS-Guard_logo.svg.png" width="20" height="20" alt="DGB"> | `DGB` | DDoS-Guard bypass |
| <img src="https://i.imgur.com/bGL8qfw.png" width="20" height="20" alt="AVB"> | `AVB` | ArvanCloud bypass |
| <img src="https://iili.io/HU9BC74.png" width="20" height="20" alt="BOT"> | `BOT` | Googlebot-style requests |
| <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Apache_Feather_Logo.svg/500px-Apache_Feather_Logo.svg.png" width="20" height="20" alt="APACHE"> | `APACHE` | Apache exploit method |
| <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/WordPress_blue_logo.svg/960px-WordPress_blue_logo.svg.png" width="20" height="20" alt="XMLRPC"> | `XMLRPC` | WordPress XML-RPC method (`/xmlrpc.php`) |
| <img src="https://upload.wikimedia.org/wikipedia/commons/9/94/Cloudflare_Logo.png" width="20" height="20" alt="CFB"> | `CFB` | Cloudflare bypass |
| <img src="https://upload.wikimedia.org/wikipedia/commons/9/94/Cloudflare_Logo.png" width="20" height="20" alt="CFBUAM"> | `CFBUAM` | Cloudflare Under Attack Mode bypass |
| <img src="https://cdn-icons-png.flaticon.com/512/905/905568.png" width="20" height="20" alt="BYPASS"> | `BYPASS` | Generic anti-DDoS bypass |
| <img src="https://cdn-icons-png.flaticon.com/512/905/905568.png" width="20" height="20" alt="BOMB"> | `BOMB` | Bombardier-based method |
| 🔪 | `KILLER` | Multi-threaded target method |
| 🧅 | `TOR` | Onion/Tor target method |

### 🧨 Layer 4 / Layer 3

| Icon | Method | Description |
|:---:|:---:|---|
| <img src="https://raw.githubusercontent.com/kgretzky/pwndrop/master/media/pwndrop-logo-512.png" width="20" height="20" alt="TCP"> | `TCP` | TCP Flood |
| <img src="https://styles.redditmedia.com/t5_2rxmiq/styles/profileIcon_snoob94cdb09-c26c-4c24-bd0c-66238623cc22-headshot.png" width="20" height="20" alt="UDP"> | `UDP` | UDP Flood |
| <img src="https://cdn-icons-png.flaticon.com/512/1918/1918576.png" width="20" height="20" alt="SYN"> | `SYN` | SYN Flood |
| <img src="https://images.icon-icons.com/2407/PNG/512/ovh_icon_146131.png" width="20" height="20" alt="OVH-UDP"> | `OVH-UDP` | UDP method with randomized headers and binary payload |
| <img src="https://cdn-icons-png.flaticon.com/512/1017/1017466.png" width="20" height="20" alt="CPS"> | `CPS` | Repeated proxy connection open/close |
| <img src="https://cdn-icons-png.flaticon.com/512/5045/5045810.png" width="20" height="20" alt="ICMP"> | `ICMP` | ICMP Echo Request flood |
| <img src="https://s6.uupload.ir/files/1059643_g8hp.png" width="20" height="20" alt="CONNECTION"> | `CONNECTION` | Keep proxy connections alive |
| <img src="https://ia803109.us.archive.org/27/items/source-engine-video-projects/source-engine-video-projects_itemimage.png" width="20" height="20" alt="VSE"> | `VSE` | Valve Source Engine protocol |
| <img src="https://mycrackfree.com/wp-content/uploads/2018/08/TeamSpeak-Server-9.png" width="20" height="20" alt="TS3"> | `TS3` | TeamSpeak 3 status ping protocol |
| <img src="https://cdn2.downdetector.com/static/uploads/logo/75ef9fcabc1abea8fce0ebd0236a4132710fcb2e.png" width="20" height="20" alt="FIVEM"> | `FIVEM` | FiveM status ping protocol |
| <img src="https://github.com/user-attachments/assets/f40748bf-dd28-4294-b862-cb0acbc74eea" width="20" height="20" alt="FIVEM-TOKEN"> | `FIVEM-TOKEN` | FiveM confirmation token method |
| <img src="https://cdn.iconscout.com/icon/free/png-512/redis-4-1175103.png" width="20" height="20" alt="MEM"> | `MEM` | Memcached amplification |
| <img src="https://lyrahosting.com/wp-content/uploads/2020/06/ddos-attack-icon.png" width="20" height="20" alt="NTP"> | `NTP` | NTP amplification |
| <img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="20" height="20" alt="MCBOT"> | `MCBOT` | Minecraft bot method |
| <img src="https://cdn.worldvectorlogo.com/logos/minecraft-1.svg" width="20" height="20" alt="MINECRAFT"> | `MINECRAFT` | Minecraft status ping protocol |
| <img src="https://cdn.worldvectorlogo.com/logos/minecraft-1.svg" width="20" height="20" alt="MCPE"> | `MCPE` | Minecraft PE status ping protocol |
| <img src="https://cdn-icons-png.flaticon.com/512/2653/2653461.png" width="20" height="20" alt="DNS"> | `DNS` | DNS amplification |
| <img src="https://lyrahosting.com/wp-content/uploads/2020/06/ddos-attack-icon.png" width="20" height="20" alt="CHAR"> | `CHAR` | Chargen amplification |
| <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRct5OvjSCpUftyRMm3evgdPOa-f8LbwJFO-A&usqp=CAU" width="20" height="20" alt="CLDAP"> | `CLDAP` | CLDAP amplification |
| <img src="https://help.apple.com/assets/6171BD2C588E52621824409D/6171BD2D588E5262182440A4/en_US/8b631353e070420f47530bf95f1a7fae.png" width="20" height="20" alt="ARD"> | `ARD` | Apple Remote Desktop amplification |
| <img src="https://www.tenforums.com/geek/gars/images/2/types/thumb__emote__esktop__onnection.png" width="20" height="20" alt="RDP"> | `RDP` | Remote Desktop Protocol amplification |

### ⚙️ Tools

Run the tools console with:

```bash
python3 start.py tools
```

| Icon | Tool | Description |
|:---:|:---:|---|
| 🌟 | `CFIP` | Find the real IP address of Cloudflare-powered websites |
| 🔪 | `DNS` | Show DNS records |
| 📍 | `TSSRV` | TeamSpeak SRV resolver |
| ⚠️ | `PING` | Ping servers |
| 📌 | `CHECK` | Check website status |
| 📊 | `DSTAT` | Display sent/received byte statistics |

### 🎩 Console Commands

| Icon | Command | Description |
|:---:|:---:|---|
| ❌ | `STOP` | Stop all running methods |
| 🌠 | `TOOLS` | Open console tools |
| 👑 | `HELP` | Show script usage |

---

## 📥 Downloads

Prebuilt releases are available from **[GitHub Releases](https://github.com/MatrixTM/MHDDoS/releases)**.

---

## 🚀 Getting Started

### 📦 Requirements

- [Python 3](https://python.org)
- [dnspython](https://github.com/rthalley/dnspython)
- [cfscrape](https://github.com/Anorov/cloudflare-scrape)
- [impacket](https://github.com/SecureAuthCorp/impacket)
- [requests](https://github.com/psf/requests)
- [PyRoxy](https://github.com/MatrixTM/PyRoxy)
- [icmplib](https://github.com/ValentinBELYN/icmplib)
- [certifi](https://github.com/certifi/python-certifi)
- [psutil](https://github.com/giampaolo/psutil)
- [yarl](https://github.com/aio-libs/yarl)

### 🔧 Clone & Install

```bash
git clone https://github.com/MatrixTM/MHDDoS.git
cd MHDDoS
pip install -r requirements.txt
```

### ⚡ One-Line Installation on a Fresh VPS

```bash
apt -y update && apt -y install curl wget libcurl4 libssl-dev python3 python3-pip make cmake automake autoconf m4 build-essential git && git clone https://github.com/MatrixTM/MHDDoS.git && cd MH* && pip3 install -r requirements.txt
```

---

## 🐳 Docker

```bash
git clone https://github.com/MatrixTM/MHDDoS.git
cd MHDDoS
docker compose build
```

Then start the container:

```bash
docker compose run -it --entrypoint /bin/bash mhddos
```

> [!TIP]
> You can also use the built image directly by enabling the relevant line in the Docker Compose configuration.

---

## 📚 Documentation

Full project documentation is available in the **[GitHub Wiki](https://github.com/MatrixTM/MHDDoS/wiki)**.

For bug reports and repository-related issues, use **[GitHub Issues](https://github.com/MatrixTM/MHDDoS/issues)**.

> [!NOTE]
> Please do not use the Issues section for general support questions.

---

## 🌐 Community

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-MatrixTM-181717?style=for-the-badge&logo=github)](https://github.com/MatrixTM)
[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/Matrix_Development)
[![Telegram Group](https://img.shields.io/badge/Telegram-Group-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/MatrixTMChat)

### ⭐ Like the project?

**Consider leaving a star on the repository — it helps the project grow.**

</div>

---

## ☁️ Hosting

<div align="center">

### 🚀 PFcloud

<a href="https://pfcloud.io/aff.php?aff=80">
  <img src="https://github.com/user-attachments/assets/172b3543-982b-450e-937d-3c4f84764a4f" width="728" alt="PFcloud Hosting">
</a>

<h4><strong>⚡ You can buy an 10Gbps cheap server from PFcloud Hosting with crypto (Scan Allowed).</strong></h4>

<p><strong><a href="https://pfcloud.io/aff.php?aff=80">Explore PFcloud Hosting</a></strong></p>

<br>

### ⚡ Zomro

<a href="https://zomro.com/vps?from=428115">
  <img src="https://i.postimg.cc/KcH7CG8b/vps.png" width="728" height="90" alt="Zomro Hosting">
</a>

<h4><strong>🕒 Zomro Hosting allows you to purchase an hourly server using crypto and completely anonymously.</strong></h4>

<p><strong><a href="https://zomro.com/vps?from=428115">Explore Zomro Hosting</a></strong></p>

</div>

---

<div align="center">

### MHDDoS

**Made for authorized security testing and research.**

<sub>Python 3 · Open Source · Community Driven</sub>

</div>
