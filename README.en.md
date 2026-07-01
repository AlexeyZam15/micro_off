<div align="center">

# 🎤 MicroOff

**Desktop application for microphone control from the system tray**

[![Русский](https://img.shields.io/badge/Язык-Русский-blue)](README.md)
[![English](https://img.shields.io/badge/Language-English-red)](README.en.md)

</div>

---

## 📦 Download the ready-to-use program

**For Windows users** — a ready-made EXE file is available, no Python installation required:

➡️ **[Download the latest version](https://github.com/AlexeyZam15/micro_off/releases/latest)**

1. Go to the **Releases** section on GitHub
2. Download the `MicroOff.exe` file
3. Run the file — no installation required

---

## 💝 Support the author

If you find this program useful, you can support the author:

➡️ **[Support the author](https://dalink.to/wolfgunt)**

Thank you for your support! ❤️

---

## Features

🔇 **Quick mute/unmute** — one click or hotkey to control your microphone

🎤 **Device switching** — switch between multiple recording devices on the fly

⌨️ **Global hotkeys** — control microphone from any application

🔄 **Auto-detection** — automatically detects the currently active microphone

📱 **Adaptive interface** — scales properly on different screen sizes

🖥️ **System tray** — runs minimized in the system tray with context menu

⚡ **Instant response** — direct control via Windows Core Audio API with no delays

---

## 🎮 Usage

### Hotkeys

| Action | Hotkey |
|--------|--------|
| Toggle microphone | `F4` |
| Mute microphone | `F2` |
| Unmute microphone | `F3` |

### System Tray Menu

| Action | Description |
|--------|-------------|
| Show | Show the main window |
| Mute | Turn off the microphone |
| Unmute | Turn on the microphone |
| Exit | Close the application |

### Main Window

| Element | Description |
|---------|-------------|
| Status indicator | Shows current microphone state (ON/OFF) |
| Mute/Unmute buttons | Manual microphone control |
| Device selector | Switch between available microphones |
| Refresh button | Update the list of devices |
| Minimize to tray | Hide window to system tray |

---

## 🔧 Program Settings

All settings are managed through the main window interface:

### Device Management

- **Device list** — shows all available recording devices
- **Auto-select** — automatically selects the active microphone
- **Refresh** — manually update the device list

### Interface

- **Adaptive layout** — automatically adjusts to window size
- **Dark theme** — modern dark purple gradient design
- **Status indicators** — visual feedback for microphone state

---

## 📂 Data storage structure

On first launch, the program creates the following files in the application directory:

```

MicroOff/
└── error_log.txt # Error log file

```

**Important:**
- The error log helps with debugging if issues occur
- All devices are detected in real-time via Windows Core Audio API
- No caching is used — the device list is always up to date

---

## 🛠️ System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Architecture**: x64
- **Libraries**: All required libraries are included in the EXE file

---

## 🔧 Build from Source

### Prerequisites

1. Install Python 3.8 or higher (64-bit)
2. Clone the repository:

```bash
git clone https://github.com/AlexeyZam15/micro_off.git
cd micro_off
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build Executable

Run the build script:

```bash
build_exe.bat
```

The EXE file will be created in the `dist` folder.

---

## 📁 Project Structure

```
micro_off/
├── micro_off.py              # Entry point
├── build_exe.bat             # Build script
├── requirements.txt          # Dependencies
├── README.md                 # Documentation (Russian)
├── README.en.md              # Documentation (English)
└── src/
    ├── __init__.py
    ├── logger.py             # Logging module
    ├── microphone_controller.py  # Microphone control logic (pycaw)
    ├── widgets.py            # Custom UI widgets
    ├── tray_icon.py          # System tray integration
    ├── hotkey_manager.py     # Global hotkey management
    ├── workers.py            # Background threads
    ├── ui_builder.py         # UI builder
    └── main_window.py        # Main application window
```

---

## 🛠️ Technologies Used

| Component | Purpose |
|-----------|---------|
| **pycaw** | Direct audio device control via Windows Core Audio API |
| **PyQt5** | Graphical user interface (GUI) |
| **keyboard** | Global hotkey support |
| **comtypes** | COM object handling for Windows |
| **PyInstaller** | EXE packaging |

### Advantages of pycaw over PowerShell:

- **Instant operation** — no delays from PowerShell calls
- **No dependencies** — doesn't require AudioDeviceCmdlets installation
- **Direct access** — to Windows API without intermediate layers
- **Stability** — fewer points of failure

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is distributed under the MIT license. This means free use, modification, and distribution with attribution.

---

## 🙏 Acknowledgments

- [pycaw](https://github.com/AndreMiras/pycaw) — Python Core Audio Windows
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI framework
- [keyboard](https://github.com/boppreh/keyboard) — Global hotkey support
- [comtypes](https://github.com/enthought/comtypes) — COM interfaces for Python
- [PyInstaller](https://pyinstaller.org/) — EXE packaging

---

<div align="center">

**⭐ Star this project if you find it useful!**

</div>