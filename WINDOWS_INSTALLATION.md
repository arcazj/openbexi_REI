# Windows installation

## Install and launch

1. Download **[REIResearchExplorer-1.0.0-Windows-x64-Setup.exe](https://github.com/arcazj/openbexi_REI/releases/download/v1.0.0/REIResearchExplorer-1.0.0-Windows-x64-Setup.exe)** from the project release.
2. Run Setup. It installs for the current Windows account, adds Start menu shortcuts, and offers a desktop shortcut.
3. Launch **REI Research Explorer**. It opens your default browser and runs the local Python service in the background.
4. Browse evidence immediately. To enable AI, click **Connect AI**, enter your own OpenAI key, and choose **Save key & connect**.

Supported package: **Windows 10/11, x64**, with a modern browser. Python and dependencies are bundled; neither Python installation nor administrator access is required. Installation works offline after download; public sources and OpenAI require internet. Native ARM64 and 32-bit packages are not supplied or tested.

Use the REI icon in the Windows notification area to **Open research workspace** or **Quit REI Research Explorer**. Closing the browser tab leaves the service running. Launching again opens the existing instance. There is no Windows service, firewall rule, or startup-at-login entry.

## Private data and updates

Default application folder: `%LOCALAPPDATA%\Programs\REIResearchExplorer`.

Private settings folder: `%LOCALAPPDATA%\REIResearchExplorer`. The API key is saved in its `.env`; `desktop.json` remembers the local port and instance identity. No key is included in the installer or copied into the browser.

Saved questions remain in your browser profile. Export JSON backups from Saved research. The app normally reuses its port (`18080` initially); if another program occupies it, another loopback port is selected. Each browser origin has separate storage, so import a backup if your briefs do not appear at a new address.

Rerun Setup to update. Uninstall through **Windows Settings → Apps → REI Research Explorer**, or the Start menu Uninstall shortcut. Updates and uninstall preserve private settings and browser research. The uninstaller deletes only packaged files, retaining additional user files in the installation folder.

## Troubleshooting

- **Windows warning:** this build is unsigned. Download only from the GitHub release; compare its SHA-256 with `SHA256SUMS-Windows.txt`. Windows may show an unknown-publisher/SmartScreen prompt. Managed PCs can require IT approval; do not disable security software.
- **Browser did not open:** use the tray icon's Open command, or relaunch from the Start menu. The app listens only on `127.0.0.1`.
- **Update cannot close the app:** choose Quit from the tray, then retry Setup.
- **AI unavailable:** check your own key, model access, internet, and API billing in AI settings. Browsing/manual briefs remain available.
- **Briefs missing:** confirm the same browser/profile and restore a JSON backup if the local port changed.

## Build and verify

Build on Windows x64 with Python 3.12 and [NSIS](https://nsis.sourceforge.io/Download). From the current source checkout:

```powershell
py -3.12 -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r requirements.lock.txt -r installer/requirements-build.txt
.\.build-venv\Scripts\python.exe -m scripts.build_windows
.\.build-venv\Scripts\python.exe -m scripts.test_windows_install
```

Output: `dist/REIResearchExplorer-1.0.0-Windows-x64-Setup.exe` and `dist/SHA256SUMS-Windows.txt`. The GitHub Windows installer workflow performs the same build and installation checks on Windows Server 2022. The smoke test uses isolated temporary folders and refuses to replace an existing registered installation.

The installer build records its source commit, Python, PyInstaller, and NSIS versions in `BUILD-INFO.json`. Packaging uses an explicit public-asset list and checks for private paths/keys. Python, PyInstaller, NSIS, and dependency license texts are included. Original-code licensing remains pending owner selection; review [commercial notes](COMMERCIAL_LICENSING.md) and [third-party notices](THIRD_PARTY_NOTICES.md) before redistribution.
