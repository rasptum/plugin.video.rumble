# Rumble Live for Kodi (`plugin.video.rumble`)

<p align="center">
  <img src="resources/icon.png" width="160" height="160" alt="Rumble Live for Kodi Icon" />
</p>

<p align="center">
  <strong>Watch Rumble live broadcasts, channels, and recent video uploads on Kodi.</strong><br>
  Engineered for <strong>Kodi 19 (Matrix)</strong>, <strong>Kodi 20 (Nexus)</strong>, and <strong>Kodi 21 (Omega)</strong>.
</p>

<p align="center">
  <a href="https://kodi.tv"><img src="https://img.shields.io/badge/Kodi-19%20%7C%2020%20%7C%2021-17B2E7.svg?logo=kodi&logoColor=white" alt="Kodi Support" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.x-3776AB.svg?logo=python&logoColor=white" alt="Python 3" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-8BC24A.svg?labelColor=111415" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Platform-All%20(Cross--Platform)-lightgrey.svg" alt="Cross Platform" />
</p>

---

## 📖 Overview

**Rumble Live** is an open-source video add-on that connects Kodi directly to [Rumble.com](https://rumble.com). Whether you are watching a major live stream, catching up on an offline creator's latest video uploads, or following multiple channels from your TV, Rumble Live provides a seamless, lean viewing experience.

Built with **pure Python 3** and standard Kodi components, Rumble Live avoids bloated external binaries or headless browsers. It extracts streams and channel manifests directly with high-performance networking, guaranteeing instant playback across low-power microcomputers and premium streaming devices alike.

---

## ✨ Key Features

- **⚡ Live Broadcast Streaming**: Plays active Rumble livestreams with adaptive HLS (`.m3u8`) and direct MP4 progressive fallback streams.
- **🎬 Recent Videos & VOD Browser**: When a creator is offline, you don't hit a dead end—click any offline channel to browse and watch their recent uploads, past livestreams, and video episodes.
- **🎮 Interactive Channel Manager**: Easily add, organize, and prune channels directly through Kodi's on-screen keyboard using creator usernames, channel slugs (e.g. `c/channelname`), or complete URLs.
- **🔴 Live Status Detection**: Real-time status indicators (`● LIVE` / `○ OFFLINE`), stream titles, viewer numbers, and preview thumbnails.
- **🔔 Background Go-Live Notifications**: An automated background service (`service.py`) checks your tracked channels and triggers desktop notifications whenever a creator begins broadcasting.
- **📦 100% Pure Python**: Fully self-contained without requiring `curl`, `ffmpeg`, or external command-line tools. Works out of the box on Android TV, CoreELEC, LibreELEC, Linux, Windows, and macOS.

---

## 🚀 Installation

### Option 1: Install from GitHub ZIP (Recommended)
1. Download the latest release `.zip` archive from the [Releases](https://github.com/rasptum/plugin.video.rumble/releases) page.
2. Transfer the `.zip` to your Kodi device.
3. In Kodi, open **Settings (gear icon) > System > Add-ons** and ensure **Unknown sources** is enabled.
4. Select **Add-ons > Install from zip file**.
5. Choose the downloaded zip file and confirm installation.

### Option 2: Manual Directory Installation (Git Clone)
Clone or copy the `plugin.video.rumble` directory into your Kodi installation's `addons` folder:

| Operating System | Addons Directory Path |
| :--- | :--- |
| **Linux (Native)** | `~/.kodi/addons/plugin.video.rumble` |
| **Linux (Flatpak)** | `~/.var/app/tv.kodi.Kodi/data/addons/plugin.video.rumble` |
| **LibreELEC / CoreELEC** | `/storage/.kodi/addons/plugin.video.rumble` |
| **Android / Google TV** | `Android/data/org.xbmc.kodi/files/.kodi/addons/plugin.video.rumble` |
| **Windows** | `%APPDATA%\Kodi\addons\plugin.video.rumble` |
| **macOS** | `~/Library/Application Support/Kodi/addons/plugin.video.rumble` |

---

## 🎯 Usage Guide

1. Open **Rumble Live** from Kodi's Video Add-ons menu.
2. Select **`[+ Add Channel / Creator]`**.
3. Enter any Rumble channel name, slug (e.g. `c/creator`), or full URL (`rumble.com/c/creator`). The add-on validates the channel and saves it to your personal watchlist.
4. Navigation:
   - **Live Channels (`● LIVE`)**: Clicking directly launches the live stream player.
   - **Offline Channels (`○ OFFLINE`)**: Clicking opens the channel's recent video library.
5. **Context Menu Actions**: Press `C` on your keyboard or long-press the Select button on your remote to:
   - **Browse Recent Videos**: View past episodes and recordings.
   - **Remove Channel**: Delete creator from watchlist.
   - **Refresh Live Status**: Manually update stream statuses.
   - **Rumble Settings**: Configure notification and playback preferences.

---

## ⚙️ Configuration & Settings

Configure via **Add-on Information > Configure**:

| Category | Setting | Default | Description |
| :--- | :--- | :--- | :--- |
| **Notifications** | Enable Go-Live Notifications | `Enabled` | Desktop alert when a followed creator goes live |
| **Notifications** | Check Interval | `60 seconds` | Polling frequency for background monitor (30s – 600s) |
| **Playback** | Preferred Quality | `Best` | Select desired video resolution (Best / 1080p / 720p / 480p) |
| **Playback** | Use InputStream Adaptive | `Enabled` | Uses `inputstream.adaptive` for multi-bitrate HLS streaming |

---

## 🛠️ Technical Details

- **Add-on ID**: `plugin.video.rumble`
- **Python Version**: 3.0.0+ (`xbmc.python`)
- **Extraction Engine**: Pure-Python JSON-LD and page-state extractor
- **Dependencies**: `script.module.inputstreamhelper` (optional)

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome!
1. Fork the repository.
2. Create your branch (`git checkout -b feature/improvement`).
3. Commit your changes (`git commit -m 'Add improvement'`).
4. Push to your fork (`git push origin feature/improvement`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

## ⚠️ Disclaimer

*This add-on is an independent, open-source community project. It is not affiliated with, endorsed by, maintained by, or sponsored by Rumble Inc.*
