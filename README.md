# Mod Updater 🛠️

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/ExGSqUT6qk)

A Python tool to **automatically update your Minecraft mods** via [Modrinth](https://modrinth.com)'s API.  
Select your mods folder, pick your Minecraft version and loader ➟ done.

---

## 📌 Features

- ✅ Automatically detects all `.jar` mods in your mods folder
- ✅ Filter by Minecraft version **and** mod loader (Fabric, Forge, NeoForge, Quilt)
- ✅ Downloads the latest compatible version from Modrinth
- ✅ Skips mods that are already up to date
- ✅ Retry logic for failed downloads
- ✅ Saves updates in a separate `updated_mods` folder
- ✅ Detailed `update_log.txt` for easy troubleshooting

---

## 🎬 Tutorial Video

Watch this quick tutorial on how to use the tool (outdated):

[![Watch the tutorial](https://img.youtube.com/vi/LYWVLeyUHH0/hqdefault.jpg)](https://www.youtube.com/watch?v=LYWVLeyUHH0)

---

## ⚡ Installation

### [A] Download ZIP
1. Download the latest release as a `.zip` from [here](https://github.com/Sypherox/mod-updater/releases/download/v1.0.1/Mod-Updater.zip)
2. Extract the ZIP anywhere on your PC
3. Make sure **Python 3.10+** is installed: [Python Download](https://www.python.org/downloads/)  
   ⚠️ During installation, check **"Add Python to PATH"**
4. Run `run.bat`

### [B] Clone via Git
```bash
git clone https://github.com/Sypherox/mod-updater.git
cd mod-updater
Then run run.bat
```

## ⚠️ Troubleshooting
If something goes wrong, check the `update_log.txt` in the `updated_mods` folder.
It contains your system info, Minecraft version, loader and a detailed list of what happened.
Join our [Discord](discord.gg/ExGSqUT6qk) and send the log file, we are happy to help you out.

---

<div align="center"> © sypherox.dev | All rights reserved </div>