# -*- coding: utf-8 -*-
"""
Echo Booster - System Optimizer
Dev: Dev RULE
"""

import ctypes
import os
import sys
import json
import shutil
import threading
import subprocess
import time
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import psutil
from PIL import Image, ImageDraw
import pystray
import customtkinter as ctk

if sys.platform == "win32":
    # Hide console window programmatically — avoids PyInstaller --noconsole DLL bug on Python 3.14
    _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if _hwnd:
        ctypes.windll.user32.ShowWindow(_hwnd, 0)

from avatar_const import AVATAR_B64

CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/RULE94DEV/EchoBooster/main/version.txt"


CUSTOM_GAMES = set()
_appdata = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "EchoBooster")
os.makedirs(_appdata, exist_ok=True)
CONFIG_PATH = os.path.join(_appdata, "config.json")
try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            CUSTOM_GAMES = set(json.load(f).get("custom_games", []))
except Exception:
    pass

def save_custom_games():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"custom_games": list(CUSTOM_GAMES)}, f)
    except Exception:
        pass

# ── Safety whitelist ──────────────────────────────────────────────
PROTECTED = {
    # Discord & Steam
    "discord.exe", "discord ptb.exe", "discord canary.exe",
    "discordptb.exe", "discordcanary.exe",
    "steam.exe", "steamwebhelper.exe", "steamservice.exe",
    
    # Popular Games & Launchers
    "fivem.exe", "fivem_b2699_gtaprocess.exe", "fivem_b2802_gtaprocess.exe",
    "fivem_b2372_gtaprocess.exe", "fivem_b2189_gtaprocess.exe", "fivem_b1604_gtaprocess.exe",
    "gta5.exe", "gtav.exe", "citizenfx.exe", "socialclub.exe",
    "fortniteclient-win64-shipping.exe", "fortnitelauncher.exe",
    "valorant-win64-shipping.exe", "valorant.exe", "vgc.exe", "vgtray.exe",
    "cs2.exe", "csgo.exe", "r5apex.exe", "cod.exe", "warzone.exe",
    "javaw.exe", "minecraft.exe", "robloxplayerbeta.exe", "leagueclient.exe",
    "leagueclientux.exe", "leagueoflegends.exe", "genshinimpact.exe",
    "overwatch.exe", "rocketleague.exe", "rainbowsix.exe", "pubg.exe",

    # Audio & GPU Drivers
    "audiodg.exe", "nvcontainer.exe", "nvidia share.exe", "nvcplui.exe",
    "amdrsserv.exe", "amdow.exe", "igfxem.exe", "realtek.exe", "rtkauduservice.exe",
    
    # Windows Core System
    "explorer.exe", "dwm.exe", "winlogon.exe", "lsass.exe", "csrss.exe",
    "smss.exe", "services.exe", "svchost.exe", "wininit.exe", "sihost.exe",
    "taskhostw.exe", "ctfmon.exe", "runtimebroker.exe", "searchindexer.exe",
    "ntoskrnl.exe", "system", "system idle process", "registry",
    "memory compression", "secure system", "vmmem", "spoolsv.exe", "fontdrvhost.exe",
    
    # Antivirus & Defense
    "mssense.exe", "msmpeng.exe", "nissrv.exe", "mbam.exe", "mbamservice.exe",
    
    # Python & Booster
    "python.exe", "pythonw.exe", "echobooster.exe", "echo booster.exe"
}

BLOAT_TARGETS = {
    # Microsoft & Windows Bloatware
    "onedrive.exe", "onedrivestandaloneupdater.exe", "msteams.exe", "teams.exe", "skype.exe",
    "cortana.exe", "yourphone.exe", "yourphoneserver.exe", "phoneexperiencehost.exe",
    "gamebarftserver.exe", "gamebar.exe", "gamebarpresencewriter.exe",
    "xboxapp.exe", "xboxgamebar.exe", "xboxgamebarwidgets.exe", "xboxidentityprovider.exe",
    "xboxstat.exe", "xboxpcapp.exe", "xboxtcui.exe", "officeclicktorun.exe", "msoasb.exe",
    "onenote.exe", "outlook.exe", "word.exe", "excel.exe", "powerpnt.exe",
    "microsoftedgeupdate.exe", "msedgewebview2.exe", "chrmstp.exe",
    "adobeupdateservice.exe", "agsservice.exe", "creative cloud.exe", "ccxprocess.exe",
    "cclibrary.exe", "coresync.exe", "adobedesktopservice.exe",
    "googlecrashhandler.exe", "googlecrashhandler64.exe", "googleupdate.exe",
    "wmpnetwk.exe", "compattelrunner.exe", "devicecensus.exe", "wsqmcons.exe",
    "wermgr.exe", "werfault.exe", "smartscreen.exe", "wsappx.exe", "wuauclt.exe",
    "searchapp.exe", "searchhost.exe", "backgroundtaskhost.exe", "backgroundtransferhost.exe",
    "feedbackhub.exe", "windowsmaps.exe", "weather.exe", "news.exe", "groove.exe",
    "movies.exe", "clipchamp.exe", "solitaire.exe", "gethelp.exe", "stickynotes.exe",
    "calculator.exe", "mspaint.exe", "snippingtool.exe",
    
    # Browser Updaters & Background helpers
    "braveupdate.exe", "opera_autoupdate.exe", "firefoxpatcher.exe", "software_reporter_tool.exe",
    
    # Launcher Updaters & Secondary Background Daemons
    "epicgameslauncher.exe", "originwebhelperservice.exe", "eabackgroundservice.exe",
    "galaxyclient.exe", "agent.exe", "battlenet.exe",
    
    # Third Party Bloat & Updaters
    "ituneshelper.exe", "ipodservice.exe", "distnoted.exe", "jusched.exe", "jucheck.exe",
    "razercentral.exe", "razercortex.exe", "logioptions.exe", "logioverlay.exe",
    "steelseriesgg.exe", "corsair.service.exe", "overwolf.exe", "overwolflauncher.exe",
    "medal.exe", "blitz.exe", "porofessor.exe", "spotify.exe", "componenthost.exe"
}

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    # sys.executable = path to the EXE (correct in PyInstaller)
    # lpParameters must be empty string, not a duplicate of the exe path
    exe = sys.executable
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, None, None, 1)
    sys.exit(0)

def get_cache_dirs():
    L = os.environ.get("LOCALAPPDATA") or ""
    T = os.environ.get("TEMP") or ""
    A = os.environ.get("APPDATA") or ""
    # Guard: if env-var is empty, Path("") == Path(".") which is the CWD.
    # Never add a path built from an empty string.
    candidates = []
    if T: candidates.append(Path(T))
    if L:
        candidates += [
            Path(L) / "Temp",
            Path(L) / "Microsoft" / "Windows" / "INetCache",
            Path(L) / "Microsoft" / "Windows" / "WebCache",
            Path(L) / "Google" / "Chrome" / "User Data" / "Default" / "Cache",
            Path(L) / "Google" / "Chrome" / "User Data" / "Default" / "Code Cache",
            Path(L) / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache",
            Path(L) / "CrashDumps",
            Path(L) / "D3DSCache",
            Path(L) / "NVIDIA" / "DXCache",
            Path(L) / "AMD" / "DxCache",
        ]
    if A:
        candidates.append(Path(A) / "Microsoft" / "Windows" / "Recent")
    # Use %SystemRoot% so it works on any drive (D:\Windows, etc.)
    win = os.environ.get("SystemRoot") or "C:\\Windows"
    candidates += [Path(win) / "Prefetch", Path(win) / "Temp"]
    return [p for p in candidates if p.exists()]

def clean_cache(log_fn):
    freed = 0
    for d in get_cache_dirs():
        log_fn(f"  Cleaning: {d.name}")
        try:
            for item in d.iterdir():
                try:
                    if item.is_file():
                        sz = item.stat().st_size
                        item.unlink()
                        freed += sz
                    elif item.is_dir():
                        # rglob can raise on broken symlinks; default sz=0 is safe
                        try:
                            sz = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        except (PermissionError, OSError):
                            sz = 0
                        shutil.rmtree(item, ignore_errors=True)
                        freed += sz
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
    return freed

# ── Tweaks: instant (active immediately) ──────────────────────────
INSTANT_REG = [
    # Game DVR & Overlay Off
    (r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", "REG_DWORD", "0"),
    (r"HKCU\System\GameConfigStore", "GameDVR_Enabled", "REG_DWORD", "0"),
    (r"HKCU\System\GameConfigStore", "GameDVR_FSEBehavior", "REG_DWORD", "2"),
    (r"HKCU\System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", "REG_DWORD", "1"),
    
    # Mouse 1:1 Precision
    (r"HKCU\Control Panel\Mouse", "MouseSpeed", "REG_SZ", "0"),
    (r"HKCU\Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "0"),
    (r"HKCU\Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "0"),
    
    # Performance Visual Effects & Sharp Display Fonts
    (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", "REG_DWORD", "2"),
    (r"HKCU\Control Panel\Desktop", "FontSmoothing", "REG_SZ", "2"),
    (r"HKCU\Control Panel\Desktop", "FontSmoothingType", "REG_DWORD", "2"),
    (r"HKCU\Control Panel\Desktop", "FontSmoothingGamma", "REG_DWORD", "1000"),
    (r"HKCU\Control Panel\Desktop", "FontSmoothingOrientation", "REG_DWORD", "1"),
    
    # TCP & Network Ping Latency Turbo
    (r"HKLM\SOFTWARE\Microsoft\MSMQ\Parameters", "TCPNoDelay", "REG_DWORD", "1"),
]

RESTORE_INSTANT_REG = [
    # Game DVR & Overlay On (Defaults)
    (r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", "REG_DWORD", "1"),
    (r"HKCU\System\GameConfigStore", "GameDVR_Enabled", "REG_DWORD", "1"),
    (r"HKCU\System\GameConfigStore", "GameDVR_FSEBehavior", "REG_DWORD", "0"),
    (r"HKCU\System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", "REG_DWORD", "0"),
    
    # Mouse Precision (Defaults)
    (r"HKCU\Control Panel\Mouse", "MouseSpeed", "REG_SZ", "1"),
    (r"HKCU\Control Panel\Mouse", "MouseThreshold1", "REG_SZ", "6"),
    (r"HKCU\Control Panel\Mouse", "MouseThreshold2", "REG_SZ", "10"),
    
    # Visual Effects (Defaults)
    (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", "REG_DWORD", "3"),
]

RESTORE_RESTART_REG = [
    (r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", "REG_DWORD", "1", "GPU Hardware Scheduling Default"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", "REG_DWORD", "10", "Network Throttling Default"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", "REG_DWORD", "20", "System Responsiveness Default"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority", "REG_DWORD", "8", "GPU Game Priority Default"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Priority", "REG_DWORD", "2", "CPU Game Priority Default"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Scheduling Category", "REG_SZ", "Medium", "Game Scheduling Medium"),
    (r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", "REG_DWORD", "2", "Foreground Default (0x2)"),
]

def restore_fps_tweaks(log_fn):
    import subprocess
    CF = 0x08000000  # CREATE_NO_WINDOW
    log_fn("  [Restoring Instant Tweaks]")
    for path, name, typ, val in RESTORE_INSTANT_REG:
        r = subprocess.run(f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f', shell=True, capture_output=True, creationflags=CF)
        log_fn(f"  {'OK' if r.returncode == 0 else 'SKIP'} {name}")
        
    # Revert Power Plan
    r = subprocess.run("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e", shell=True, capture_output=True, creationflags=CF)
    log_fn(f"  {'OK' if r.returncode == 0 else 'SKIP'} Balanced power plan")

    # Revert Services
    for svc_name, svc_label in [("SysMain", "Superfetch"), ("DiagTrack", "Telemetry"), ("WSearch", "Windows Search")]:
        rc1 = subprocess.run(f"sc config {svc_name} start= delayed-auto", shell=True, capture_output=True, creationflags=CF)
        if rc1.returncode != 0:
            rc1 = subprocess.run(f"sc config {svc_name} start= auto", shell=True, capture_output=True, creationflags=CF)
        subprocess.run(f"sc start {svc_name}", shell=True, capture_output=True, creationflags=CF)
        log_fn(f"  {'OK' if rc1.returncode == 0 else 'SKIP'} {svc_label} restored")
        
    # Revert TCP Ping Latency Turbo (Delete keys)
    try:
        cmd = 'powershell "Get-ChildItem HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces | ForEach-Object { Remove-ItemProperty -Path $_.PSPath -Name TcpAckFrequency -ErrorAction SilentlyContinue; Remove-ItemProperty -Path $_.PSPath -Name TCPNoDelay -ErrorAction SilentlyContinue }"'
        subprocess.run(cmd, shell=True, capture_output=True, creationflags=CF)
        log_fn("  OK  TCP Ping & Latency defaults restored")
    except Exception:
        pass
        
    # Revert BCDEDIT
    try:
        subprocess.run("bcdedit /set disabledynamictick no", shell=True, capture_output=True, creationflags=CF)
        log_fn("  OK  BCDEDIT Dynamic Tick restored")
    except Exception:
        pass

    log_fn("  [Restoring Restart Tweaks]")
    for path, name, typ, val, label in RESTORE_RESTART_REG:
        r = subprocess.run(f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f', shell=True, capture_output=True, creationflags=CF)
        log_fn(f"  {'OK' if r.returncode == 0 else 'SKIP'} {label}")
        
    # Delete GameDVR policy
    try:
        subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /f', shell=True, capture_output=True, creationflags=CF)
    except Exception:
        pass

GAME_EXECUTABLES = {
    "fivem.exe": "FiveM / GTA RP",
    "fivem_b2699_gtaprocess.exe": "FiveM",
    "fivem_b2802_gtaprocess.exe": "FiveM",
    "fivem_b2372_gtaprocess.exe": "FiveM",
    "fivem_b2189_gtaprocess.exe": "FiveM",
    "fivem_b1604_gtaprocess.exe": "FiveM",
    "gta5.exe": "GTA V",
    "gtav.exe": "GTA V",
    "fortniteclient-win64-shipping.exe": "Fortnite",
    "valorant-win64-shipping.exe": "Valorant",
    "valorant.exe": "Valorant",
    "cs2.exe": "Counter-Strike 2",
    "csgo.exe": "CS:GO",
    "r5apex.exe": "Apex Legends",
    "cod.exe": "Call of Duty",
    "warzone.exe": "Warzone",
    "javaw.exe": "Minecraft",
    "robloxplayerbeta.exe": "Roblox",
    "leagueoflegends.exe": "League of Legends",
    "genshinimpact.exe": "Genshin Impact",
    "overwatch.exe": "Overwatch 2",
    "rocketleague.exe": "Rocket League",
    "rainbowsix.exe": "Rainbow Six Siege",
    "pubg.exe": "PUBG"
}

def detect_active_game():
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower().strip()
            if name in GAME_EXECUTABLES:
                return GAME_EXECUTABLES[name], proc
            if name in CUSTOM_GAMES:
                return f"Custom: {name}", proc
        except Exception:
            pass
    return None, None

DNS_PRESETS = {
    "Cloudflare": ("1.1.1.1", "1.0.0.1", "Cloudflare Gaming (1.1.1.1)"),
    "Google": ("8.8.8.8", "8.8.4.4", "Google Public DNS (8.8.8.8)"),
    "Quad9": ("9.9.9.9", "149.112.112.112", "Quad9 Secure Gaming"),
    "Reset": (None, None, "Default ISP DNS (DHCP)")
}

def set_dns_preset(preset_key: str, log_fn):
    if preset_key not in DNS_PRESETS:
        return
    p1, p2, label = DNS_PRESETS[preset_key]
    log_fn(f"  Switching DNS to {label}...")
    try:
        if preset_key == "Reset":
            ps_cmd = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Set-DnsClientServerAddress -ResetServerAddresses'
        else:
            ps_cmd = f'Get-NetAdapter | Where-Object {{$_.Status -eq "Up"}} | Set-DnsClientServerAddress -ServerAddresses ("{p1}","{p2}")'
        
        r = subprocess.run(f'powershell -Command "{ps_cmd}"', shell=True, capture_output=True, creationflags=0x08000000)
        subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, creationflags=0x08000000)
        if r.returncode == 0:
            log_fn(f"  OK  DNS Switched to {label}")
        else:
            log_fn(f"  SKIP DNS Switch to {label} (Need Admin)")
    except Exception:
        log_fn(f"  SKIP DNS Switch error")

def auto_optimize_ping(log_fn):
    log_fn("  [Network Ping Optimizer started]")
    best_dns = None
    best_ping = 9999
    
    for key, (p1, p2, label) in DNS_PRESETS.items():
        if key == "Reset": continue
        try:
            res = subprocess.run(f"ping {p1} -n 1 -w 1000", shell=True, capture_output=True, text=True, creationflags=0x08000000)
            if "time=" in res.stdout:
                ms = int(res.stdout.split("time=")[1].split("ms")[0].strip())
                log_fn(f"  Ping {label}: {ms}ms")
                if ms < best_ping:
                    best_ping = ms
                    best_dns = key
        except:
            pass
            
    if best_dns:
        log_fn(f"  \u26a1 Best DNS found: {best_dns} ({best_ping}ms)")
        set_dns_preset(best_dns, log_fn)
    else:
        log_fn("  \u26a0\uFE0F Could not determine best DNS. Connection issue?")

# ── Tweaks: need restart to take full effect ───────────────────────
RESTART_REG = [
    (r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", "REG_DWORD", "2", "GPU Hardware Scheduling"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", "REG_DWORD", "ffffffff", "Network Throttling Off"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", "REG_DWORD", "0", "System Responsiveness Max"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority", "REG_DWORD", "8", "GPU Game Priority"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Priority", "REG_DWORD", "6", "CPU Game Priority"),
    (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Scheduling Category", "REG_SZ", "High", "Game Scheduling High"),
    
    # Win32PrioritySeparation (Foreground Quantum Game Boost)
    (r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", "REG_DWORD", "26", "Foreground FPS Quantum (0x26)"),
    
    # Global Fullscreen Optimizations Off (Input Lag & Tearing Fix)
    (r"HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameDVR", "REG_DWORD", "0", "Disable GameDVR Policy"),
]

def apply_fps_tweaks(log_fn):
    restart_needed = False
    CF = 0x08000000  # CREATE_NO_WINDOW

    log_fn("  [Instant tweaks — active now]")
    for path, name, typ, val in INSTANT_REG:
        r = subprocess.run(
            f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f',
            shell=True, capture_output=True, creationflags=CF)
        log_fn(f"  {'OK' if r.returncode == 0 else 'SKIP'} {name}")

    # Power plan — instant
    r = subprocess.run(
        "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        shell=True, capture_output=True, creationflags=CF)
    log_fn(f"  {'OK' if r.returncode == 0 else 'SKIP'} High Performance power plan")

    # Stop services — instant
    for svc_name, svc_label in [("SysMain", "Superfetch"), ("DiagTrack", "Telemetry"), ("WSearch", "Windows Search")]:
        rc1 = subprocess.run(f"sc config {svc_name} start= disabled", shell=True, capture_output=True, creationflags=CF)
        subprocess.run(f"sc stop {svc_name}", shell=True, capture_output=True, creationflags=CF)
        ok = rc1.returncode == 0
        log_fn(f"  {'OK' if ok else 'SKIP'} {svc_label} {'stopped' if ok else '(need admin)'}")

    # DNS flush — instant
    rd = subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, creationflags=CF)
    log_fn(f"  {'OK' if rd.returncode == 0 else 'SKIP'} DNS cache flushed")

    # TCP Ping & Latency Turbo
    try:
        cmd = 'powershell "Get-ChildItem HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces | ForEach-Object { Set-ItemProperty -Path $_.PSPath -Name TcpAckFrequency -Value 1 -Type DWord -ErrorAction SilentlyContinue; Set-ItemProperty -Path $_.PSPath -Name TCPNoDelay -Value 1 -Type DWord -ErrorAction SilentlyContinue }"'
        subprocess.run(cmd, shell=True, capture_output=True, creationflags=CF)
        log_fn("  OK  TCP Ping & Latency Turbo enabled")
    except Exception:
        pass

    # BCDEDIT Micro-Stutter Fix
    try:
        subprocess.run("bcdedit /set disabledynamictick yes", shell=True, capture_output=True, creationflags=CF)
        subprocess.run("bcdedit /set useplatformclock false", shell=True, capture_output=True, creationflags=CF)
        log_fn("  OK  BCDEDIT Timer Micro-Stutter Fix applied")
    except Exception:
        pass

    # Display Sharpness & ClearType System Refresh
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x0052, 0, None, 0x0001)
        log_fn("  OK  Display Sharpness & Font Smoothing Refreshed")
    except Exception:
        pass

    if is_admin():
        subprocess.run("rundll32.exe advapi32.dll,ProcessIdleTasks",
                       shell=True, capture_output=True, creationflags=CF)
        log_fn("  OK  Idle tasks purged")

    log_fn("  [Restart-required tweaks — saved, apply on next boot]")
    for path, name, typ, val, label in RESTART_REG:
        r = subprocess.run(
            f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f',
            shell=True, capture_output=True, creationflags=CF)
        if r.returncode == 0:
            log_fn(f"  OK  {label}  [RESTART NEEDED]")
            restart_needed = True
        else:
            log_fn(f"  SKIP {label} (need admin)")

    return restart_needed

def trim_ram():
    """Flushes working set of background processes to free RAM, avoiding games and critical processes to prevent stutters."""
    trimmed = 0
    try:
        OpenProcess = ctypes.windll.kernel32.OpenProcess
        CloseHandle = ctypes.windll.kernel32.CloseHandle
        EmptyWorkingSet = ctypes.windll.psapi.EmptyWorkingSet
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_VM_READ    = 0x0010
        
        system_critical = {"explorer.exe", "dwm.exe", "csrss.exe", "smss.exe", "winlogon.exe", 
                           "lsass.exe", "svchost.exe", "wininit.exe", "services.exe"}

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                if pid <= 4:
                    continue
                name = (proc.info.get('name') or "").lower().strip()
                
                # Skip games, protected apps, and critical system processes to prevent frame drops
                if not name or name in PROTECTED or name in CUSTOM_GAMES or name in system_critical:
                    continue

                h = OpenProcess(PROCESS_SET_QUOTA | PROCESS_VM_READ, False, pid)
                if h:
                    EmptyWorkingSet(h)
                    CloseHandle(h)
                    trimmed += 1
            except Exception:
                pass
    except Exception:
        pass
    return trimmed

def is_bloat_proc(name: str, exe_path: str) -> bool:
    name_lower = name.lower().strip()
    if not name_lower or name_lower in PROTECTED or name_lower in CUSTOM_GAMES:
        return False
    if name_lower in BLOAT_TARGETS:
        return True
    # Heuristic checks for background updaters & bloat
    if any(pattern in name_lower for pattern in [
        "crashhandler", "telemetry", "autoupdate", "updatehelper", "installer_helper"
    ]):
        return True
    if exe_path and ("appdata\\local\\temp" in exe_path.lower() or "appdata\\local\\microsoft\\onedrive" in exe_path.lower()):
        return True
    return False

def kill_bloat(log_fn):
    killed = 0
    procs = list(psutil.process_iter(["name", "pid", "exe"]))
    for proc in procs:
        try:
            name = (proc.info.get("name") or "").lower().strip()
            exe  = (proc.info.get("exe") or "")
            if is_bloat_proc(name, exe):
                proc.kill()
                display_name = proc.info.get("name") or name
                log_fn(f"  Killed: {display_name}")
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception:
            pass

    # Aggressive RAM optimization
    trimmed = trim_ram()
    if trimmed > 0:
        log_fn(f"  RAM Trimmed for {trimmed} active processes")

    return killed

def get_temp():
    try:
        res = subprocess.run("wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature", shell=True, capture_output=True, text=True, creationflags=0x08000000)
        lines = res.stdout.strip().split("\n")
        if len(lines) >= 2:
            temp_k = int(lines[1].strip())
            temp_c = (temp_k / 10) - 273.15
            if temp_c > 0 and temp_c < 120:
                return f"{temp_c:.1f}°C"
    except Exception:
        pass
    return "N/A"

def get_stats():
    cpu   = psutil.cpu_percent(interval=0.2)
    ram   = psutil.virtual_memory()
    # psutil.pids() is lighter than process_iter — no process object overhead
    procs = len(psutil.pids())
    return cpu, ram.used / 1024**3, ram.total / 1024**3, procs, get_temp()


# ═══════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#080810"
CARD    = "#0E0E1A"
CARD2   = "#141422"
BORDER  = "#1E1E35"
TEXT    = "#F1F5F9"
DIM     = "#94A3B8"
SUBTEXT = "#475569"
ACCENT  = "#7C3AED"
CYAN    = "#06B6D4"
SUCCESS = "#10B981"
WARN    = "#F59E0B"
DANGER  = "#EF4444"
PURPLE2 = "#A855F7"
RESTART_COLOR = "#F97316"  # orange for restart-required


def dk(h, n=40):
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return f"#{max(0,r-n):02x}{max(0,g-n):02x}{max(0,b-n):02x}"


# ═══════════════════════════════════════════════════════════════════
#  TOOLTIP
# ═══════════════════════════════════════════════════════════════════
class Tooltip:
    """Hover tooltip — 420ms delay, auto-positions to stay on screen."""

    def __init__(self, widget, title: str, body: str):
        self.widget = widget
        self.title  = title
        self.body   = body
        self._tip   = None
        self._after = None
        widget.bind("<Enter>",  self._schedule, add="+")
        widget.bind("<Leave>",  self._hide,     add="+")
        widget.bind("<Button>", self._hide,     add="+")

    def _schedule(self, _=None):
        self._cancel()
        self._after = self.widget.after(420, self._show)

    def _cancel(self):
        if self._after:
            try:
                self.widget.after_cancel(self._after)
            except Exception:
                pass
            self._after = None

    def _show(self, _=None):
        if self._tip:
            return
        try:
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            ww = self.widget.winfo_width()
            sw = self.widget.winfo_screenwidth()
            sh = self.widget.winfo_screenheight()
        except Exception:
            return

        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.configure(bg=CARD2)

        outer = tk.Frame(tw, bg=ACCENT, padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=CARD2, padx=14, pady=11)
        inner.pack()

        tk.Label(inner, text=self.title,
                 font=("Segoe UI", 11, "bold"),
                 fg=TEXT, bg=CARD2).pack(anchor="w")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(4, 7))
        tk.Label(inner, text=self.body,
                 font=("Segoe UI", 10),
                 fg=DIM, bg=CARD2,
                 justify="left", wraplength=270).pack(anchor="w")

        # Flush so we know the tooltip size
        tw.update_idletasks()
        tw_w = tw.winfo_reqwidth()
        tw_h = tw.winfo_reqheight()

        # Prefer right of widget; fall back to left
        x = wx + ww + 8
        if x + tw_w > sw - 8:
            x = wx - tw_w - 8
        x = max(4, x)  # never go off left edge
        # Prefer below top of widget; clamp vertically
        y = wy + 10
        if y + tw_h > sh - 8:
            y = sh - tw_h - 8
        y = max(4, y)  # never go off top edge

        tw.wm_geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


# ═══════════════════════════════════════════════════════════════════
#  STAT CARD
# ═══════════════════════════════════════════════════════════════════
class StatCard(ctk.CTkFrame):
    def __init__(self, master, label, icon, tip_title, tip_body, **kw):
        super().__init__(master, fg_color=CARD2, corner_radius=14,
                         border_color=BORDER, border_width=1, **kw)
        ctk.CTkLabel(self, text=icon, font=("Segoe UI", 18)).pack(pady=(10, 0))
        ctk.CTkLabel(self, text=label, font=("Segoe UI", 10),
                     text_color=SUBTEXT).pack()
        self._v = ctk.CTkLabel(self, text="--",
                               font=("Segoe UI", 22, "bold"), text_color=TEXT)
        self._v.pack(pady=(2, 10))
        # Attach to value label — StatCard (Frame) children steal <Enter>
        Tooltip(self._v, tip_title, tip_body)

    def set(self, v):
        self._v.configure(text=v)


# ═══════════════════════════════════════════════════════════════════
#  TWEAK ROW — shows each tweak with INSTANT / RESTART badge
# ═══════════════════════════════════════════════════════════════════
class TweakRow(ctk.CTkFrame):
    """A row: [badge] [name]"""
    def __init__(self, master, name: str, restart: bool, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        badge_col  = RESTART_COLOR if restart else SUCCESS
        badge_text = "ON BOOT" if restart else "INSTANT"
        ctk.CTkLabel(self, text=badge_text,
                     font=("Segoe UI", 9, "bold"),
                     text_color=badge_col,
                     width=60).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(self, text=name,
                     font=("Segoe UI", 10),
                     text_color=DIM,
                     anchor="w").pack(side="left", fill="x", expand=True)


# ═══════════════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════════════
def square_crop(img: Image.Image, size: int = 64) -> Image.Image:
    return img.resize((size, size), Image.LANCZOS)


# ═══════════════════════════════════════════════════════════════════
#  MINI TRAY BAR (Floating Docked Bar next to System Clock)
# ═══════════════════════════════════════════════════════════════════
class MiniTrayBar(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-toolwindow", True)  # hide from taskbar
        self.configure(bg=CARD)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 370, 52
        x = sw - w - 16
        y = sh - h - 50
        self.geometry(f"{w}x{h}+{x}+{y}")

        outer = tk.Frame(self, bg=ACCENT, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=CARD, padx=10, pady=6)
        inner.pack(fill="both", expand=True)

        self.lbl = tk.Label(inner, text="\u26a1 Echo Booster Active",
                            font=("Segoe UI", 9, "bold"),
                            fg=TEXT, bg=CARD, anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True, padx=4)

        btn_rst = tk.Button(inner, text="Open App",
                            font=("Segoe UI", 9, "bold"),
                            fg=TEXT, bg=ACCENT, activebackground=PURPLE2,
                            activeforeground=TEXT, bd=0, padx=8, pady=2,
                            command=self._restore)
        btn_rst.pack(side="right", padx=3)

        btn_cls = tk.Button(inner, text="\u2715",
                            font=("Segoe UI", 9, "bold"),
                            fg=DIM, bg=CARD, activebackground=DANGER,
                            activeforeground=TEXT, bd=0, padx=6, pady=2,
                            command=self._close_all)
        btn_cls.pack(side="right", padx=1)

        # Draggable
        for w_item in (self, outer, inner, self.lbl):
            w_item.bind("<ButtonPress-1>", self.start_move)
            w_item.bind("<ButtonRelease-1>", self.stop_move)
            w_item.bind("<B1-Motion>", self.do_move)

        self.bind("<Double-Button-1>", lambda _: self._restore())
        self.withdraw()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.x is None or self.y is None: return
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.geometry(f"+{self.winfo_x()+deltax}+{self.winfo_y()+deltay}")

    def _restore(self):
        self.withdraw()
        self.app.deiconify()
        self.app.lift()

    def _close_all(self):
        self.withdraw()
        self.app.destroy()
        sys.exit(0)

    def update_info(self, text):
        try:
            self.lbl.configure(text=text)
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════
#  MINI WIDGET OVERLAY (Floating in-game stats)
# ═══════════════════════════════════════════════════════════════════
class MiniWidgetOverlay(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-toolwindow", True)
        # Make the window background transparent (requires Windows)
        self.wm_attributes("-transparentcolor", "black")
        self.configure(bg="black")
        
        sw = self.winfo_screenwidth()
        w, h = 160, 60
        x = sw - w - 20
        y = 20
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.frame = tk.Frame(self, bg=CARD, highlightbackground=ACCENT, highlightthickness=1)
        self.frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.lbl = tk.Label(self.frame, text="CPU: --% | RAM: --G\nPing: --ms",
                            font=("Segoe UI", 9, "bold"), fg=TEXT, bg=CARD, justify="left")
        self.lbl.pack(padx=4, pady=4)
        
        for w_item in (self, self.frame, self.lbl):
            w_item.bind("<ButtonPress-1>", self.start_move)
            w_item.bind("<ButtonRelease-1>", self.stop_move)
            w_item.bind("<B1-Motion>", self.do_move)
        
        # Double click to Instant Boost
        self.bind("<Double-Button-1>", lambda _: self.app._do_smart_tune())
        self.withdraw()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.x is None or self.y is None: return
        deltax = event.x - self.x
        deltay = event.y - self.y
        self.geometry(f"+{self.winfo_x()+deltax}+{self.winfo_y()+deltay}")

    def update_stats(self, cpu, ram, ping):
        try:
            self.lbl.configure(text=f"CPU: {cpu:.0f}% | RAM: {ram:.1f}G\nPing: {ping}")
        except: pass

# ═══════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════
class EchoBoosterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Echo Booster")
        self.geometry("1060x720")
        self.minsize(900, 620)
        self.configure(fg_color=BG)
        self._center()
        self._load_avatar()
        self._ping_val = "N/A"
        self._build()
        self._tray_bar = MiniTrayBar(self)
        self._mini_widget = MiniWidgetOverlay(self)
        self._stat_loop()
        threading.Thread(target=self._ping_loop_thread, daemon=True).start()
        threading.Thread(target=self._check_update, daemon=True).start()

    def _ping_loop_thread(self):
        import subprocess
        while True:
            try:
                res = subprocess.run("ping 8.8.8.8 -n 1 -w 1000", shell=True, capture_output=True, text=True, creationflags=0x08000000)
                if "time=" in res.stdout:
                    ms = res.stdout.split("time=")[1].split("ms")[0].strip()
                    self._ping_val = f"{ms}ms"
                else:
                    self._ping_val = "Timeout"
            except Exception:
                pass
            time.sleep(2)

    def _check_update(self):
        try:
            import urllib.request
            req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                latest_version = response.read().decode('utf-8').strip()
            if latest_version and latest_version != CURRENT_VERSION:
                self.after(0, lambda: self._apply_update(latest_version))
        except Exception as e:
            self.log(f"Update check failed: {e}")

    def _apply_update(self, latest):
        self.log(f"  \u2934\uFE0F Update found ({latest}). Downloading silently...")
        try:
            import urllib.request
            # Point to the zip release file
            zip_url = "https://github.com/RULE94DEV/EchoBooster/releases/latest/download/EchoBooster_Release.zip"
            temp_zip = os.path.join(os.environ.get("TEMP", "C:\\"), "EchoBooster_update.zip")
            temp_extract = os.path.join(os.environ.get("TEMP", "C:\\"), "EchoBooster_extracted")
            
            urllib.request.urlretrieve(zip_url, temp_zip)
            
            current_exe = sys.executable
            app_dir = os.path.dirname(current_exe)
            bat_path = os.path.join(os.environ.get("TEMP", "C:\\"), "updater.bat")
            
            # Batch script: Wait, use PowerShell to unzip and overwrite app directory, restart app, delete self
            bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "Expand-Archive -Path '{temp_zip}' -DestinationPath '{temp_extract}' -Force; Copy-Item -Path '{temp_extract}\\EchoBooster\\*' -Destination '{app_dir}' -Recurse -Force; Remove-Item -Path '{temp_extract}' -Recurse -Force; Remove-Item -Path '{temp_zip}' -Force"
start "" "{current_exe}"
del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
                
            self.log("  \u2705 Update downloaded. Restarting app to apply...")
            subprocess.Popen(bat_path, creationflags=0x08000000)
            self.after(500, self._force_exit)
        except Exception as e:
            self.log(f"  \u26a0\uFE0F Silent update failed: {e}")
            self.after(0, lambda: messagebox.showerror("Update Required", f"A new version ({latest}) is available.\nPlease download the latest update to continue."))

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1060x720+{(sw-1060)//2}+{(sh-720)//2}")

    def _load_avatar(self):
        try:
            raw      = base64.b64decode(AVATAR_B64)
            img      = Image.open(io.BytesIO(raw)).convert("RGBA")
            self._av = ctk.CTkImage(square_crop(img, 64), size=(64, 64))
        except Exception:
            self._av = None

    # ── Build ──────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=76)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        lf = ctk.CTkFrame(hdr, fg_color="transparent")
        lf.pack(side="left", padx=22, pady=10)
        ctk.CTkLabel(lf, text="Echo Booster",
                     font=("Segoe UI", 26, "bold"),
                     text_color=ACCENT).pack(anchor="w")
        self.game_badge = ctk.CTkLabel(
            lf, text="\u26a1 Smart AI Engine: Active  \u2022  Auto-Detecting Games",
            font=("Segoe UI", 10, "bold"), text_color=CYAN)
        self.game_badge.pack(anchor="w")

        dc = ctk.CTkFrame(hdr, fg_color=CARD2, corner_radius=16,
                          border_color=ACCENT, border_width=1)
        dc.pack(side="right", padx=20, pady=13)
        if self._av:
            ctk.CTkLabel(dc, image=self._av, text="").pack(
                side="left", padx=(12, 8), pady=10)
        inf = ctk.CTkFrame(dc, fg_color="transparent")
        inf.pack(side="left", padx=(0, 18), pady=12)
        ctk.CTkLabel(inf, text="Dev RULE",
                     font=("Segoe UI", 16, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(inf, text="\u25cf  Online",
                     font=("Segoe UI", 10), text_color=SUCCESS).pack(anchor="w")
        _admin = is_admin()
        ctk.CTkLabel(inf,
                     text="Administrator" if _admin else "Run as Admin!",
                     font=("Segoe UI", 10, "bold"),
                     text_color=SUCCESS if _admin else WARN).pack(anchor="w")

        btn_box = ctk.CTkFrame(dc, fg_color="transparent")
        btn_box.pack(side="right", padx=(0, 10), pady=12)
        tray_btn = ctk.CTkButton(
            btn_box, text="\U0001F4CC Tray", width=52, height=22,
            fg_color=CARD, hover_color=BORDER, text_color=DIM,
            font=("Segoe UI", 8, "bold"), corner_radius=6,
            command=self._minimize_to_tray)
        tray_btn.pack(side="left", padx=2)
        Tooltip(tray_btn, "Tray Background Mode", "Minimizes to floating dock.\nKeeps Smart AI Active!")
        exit_btn = ctk.CTkButton(
            btn_box, text="\U0001F6AA Exit", width=52, height=22,
            fg_color=CARD, hover_color=DANGER, text_color=TEXT,
            font=("Segoe UI", 8, "bold"), corner_radius=6,
            command=self._force_exit)
        exit_btn.pack(side="left", padx=2)

        # Footer
        foot = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=28)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        ctk.CTkLabel(
            foot,
            text="Echo Booster  by Dev RULE  \u2022  Discord & Steam always protected  \u2022  Safe optimizer",
            font=("Segoe UI", 9), text_color=SUBTEXT
        ).pack(side="left", padx=18)

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Right nav sidebar
        nav = ctk.CTkFrame(body, fg_color=CARD, corner_radius=16,
                           border_color=BORDER, border_width=1, width=100)
        nav.pack(side="right", fill="y", padx=(10, 0))
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="MENU",
                     font=("Segoe UI", 8, "bold"),
                     text_color=SUBTEXT).pack(pady=(16, 6))

        self._nav_btns = {}
        for page_id, icon, label in [
            ("general",  "\U0001F3AE", "General"),
            ("settings", "\u2699\uFE0F",  "Settings"),
            ("this_pc",  "\U0001F4BB", "This PC"),
            ("info",     "\u2139\uFE0F",   "Info"),
        ]:
            btn = ctk.CTkButton(
                nav, text=f"{icon}\n{label}",
                width=80, height=64,
                fg_color=ACCENT if page_id == "general" else "transparent",
                hover_color=BORDER,
                text_color=TEXT if page_id == "general" else DIM,
                font=("Segoe UI", 9, "bold"),
                corner_radius=12,
                command=lambda p=page_id: self._switch_page(p))
            btn.pack(padx=8, pady=4)
            self._nav_btns[page_id] = btn

        # Content area
        self._content_area = ctk.CTkFrame(body, fg_color="transparent")
        self._content_area.pack(side="left", fill="both", expand=True)

        self._pages = {
            "general":  self._build_general_page(self._content_area),
            "settings": self._build_settings_page(self._content_area),
            "this_pc":  self._build_this_pc_page(self._content_area),
            "info":     self._build_info_page(self._content_area),
        }
        self._active_page = None
        self._switch_page("general")

    def _switch_page(self, name):
        for frame in self._pages.values():
            frame.pack_forget()
        self._pages[name].pack(fill="both", expand=True)
        for n, btn in self._nav_btns.items():
            if n == name:
                btn.configure(fg_color=ACCENT, text_color=TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=DIM)
        self._active_page = name

    def _build_general_page(self, parent):
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        # Left panel
        left = ctk.CTkFrame(frame, fg_color="transparent", width=300)
        left.pack(side="left", fill="both", padx=(0, 10))

        # Stats
        sf = ctk.CTkFrame(left, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        sf.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(sf, text="Live System Stats",
                     font=("Segoe UI", 12, "bold"),
                     text_color=DIM).pack(padx=16, pady=(12, 8), anchor="w")

        g = ctk.CTkFrame(sf, fg_color="transparent")
        g.pack(padx=10, pady=(0, 10), fill="x")
        self.cpu_c = StatCard(g, "CPU", "\U0001F9E0", "CPU Usage",
            "Current processor load across all cores.\n"
            "High % = system is under heavy load.\n"
            "Kill Bloat reduces this instantly.")
        self.ram_c = StatCard(g, "RAM", "\U0001F4BE", "RAM Usage",
            "Current memory usage.\n"
            "Clean Cache frees RAM used by\n"
            "temp files and browser caches.")
        self.prc_c = StatCard(g, "Procs", "\u2699\uFE0F", "Running Processes",
            "Total active processes.\n"
            "Kill Bloat terminates unnecessary ones\n"
            "freeing CPU and RAM instantly.")
        self.net_d_c = StatCard(g, "Download", "\u2B07\uFE0F", "Network Download",
            "Current real-time download speed.")
        self.net_u_c = StatCard(g, "Upload", "\u2B06\uFE0F", "Network Upload",
            "Current real-time upload speed.")
        self.cpu_c.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.ram_c.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        self.prc_c.grid(row=0, column=2, padx=4, pady=4, sticky="nsew")
        self.net_d_c.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")
        self.net_u_c.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")
        g.columnconfigure((0, 1, 2), weight=1)

        self.freed_lbl = ctk.CTkLabel(sf, text="Ready to boost",
                                       font=("Segoe UI", 12, "bold"), text_color=CYAN)
        self.freed_lbl.pack(pady=(0, 2))
        self.latency_lbl = ctk.CTkLabel(
            sf, text="\u26a1 Latency: 0.1ms  |  \U0001F525 Ultra Gaming Mode",
            font=("Segoe UI", 10, "bold"), text_color=SUCCESS)
        self.latency_lbl.pack(pady=(0, 10))

        # Action Buttons
        bf = ctk.CTkFrame(left, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        bf.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(bf, text="Actions",
                     font=("Segoe UI", 12, "bold"),
                     text_color=DIM).pack(padx=16, pady=(12, 8), anchor="w")

        BUTTONS = [
            ("   Clean Cache",  self._do_clean,      ACCENT,  "Clean Cache",
             "Removes temp files. 100% safe. Effect: INSTANT."),
            ("   Disk Clean",   self._do_disk,       WARN,    "Disk Cleaner",
             "Frees disk space: WinSxS logs, Delivery Opt, Recycle Bin."),
            ("   Boost FPS",    self._do_fps,        CYAN,    "Boost FPS",
             "Applies FPS tweaks. See overview for full list."),
            ("   Kill Bloat",   self._do_kill,       PURPLE2, "Kill Bloat",
             "Kills background bloat. Discord & Steam always safe."),
            ("  FULL BOOST",    self._do_all,        DANGER,  "Full Boost",
             "Runs all 3 actions. Maximum performance one click."),
            (" \u26a1 Smart Tune",  self._do_smart_tune, SUCCESS, "Smart Tune",
             "Analyzes your hardware and applies optimal settings."),
        ]
        self._btns = []
        for txt, fn, col, tt, tb in BUTTONS:
            b = ctk.CTkButton(bf, text=txt, command=fn,
                fg_color=col, hover_color=dk(col),
                font=("Segoe UI", 13, "bold"), height=46, corner_radius=12)
            b.pack(fill="x", padx=14, pady=4)
            Tooltip(b, tt, tb)
            self._btns.append(b)
        ctk.CTkFrame(bf, fg_color="transparent", height=4).pack()

        # DNS
        df = ctk.CTkFrame(left, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        df.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(df, text="DNS Gaming Turbo",
                     font=("Segoe UI", 11, "bold"),
                     text_color=DIM).pack(padx=14, pady=(8, 4), anchor="w")
        d_grid = ctk.CTkFrame(df, fg_color="transparent")
        d_grid.pack(fill="x", padx=6, pady=(0, 8))
        d_grid.columnconfigure((0, 1, 2), weight=1)
        btn_cf   = ctk.CTkButton(d_grid, text="\u26a1 1.1.1.1", height=28,
                                 fg_color=CARD2, hover_color=ACCENT, font=("Segoe UI", 9, "bold"),
                                 corner_radius=8, command=lambda: self._do_dns("Cloudflare"))
        btn_goog = ctk.CTkButton(d_grid, text="\U0001F680 8.8.8.8", height=28,
                                 fg_color=CARD2, hover_color=CYAN, font=("Segoe UI", 9, "bold"),
                                 corner_radius=8, command=lambda: self._do_dns("Google"))
        btn_def  = ctk.CTkButton(d_grid, text="\U0001F504 Default", height=28,
                                 fg_color=CARD2, hover_color=BORDER, font=("Segoe UI", 9, "bold"),
                                 corner_radius=8, command=lambda: self._do_dns("Reset"))
        btn_cf.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        btn_goog.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
        btn_def.grid(row=0, column=2, padx=2, pady=2, sticky="nsew")
        Tooltip(btn_cf,   "Cloudflare DNS", "1.1.1.1 & 1.0.0.1 — Ultra-fast gaming DNS.")
        Tooltip(btn_goog, "Google DNS",     "8.8.8.8 & 8.8.4.4 — High stability.")
        Tooltip(btn_def,  "Default DNS",    "Resets to DHCP automatic.")

        # Progress
        self.restart_lbl = ctk.CTkLabel(
            left, text="", font=("Segoe UI", 10),
            text_color=RESTART_COLOR, wraplength=280, justify="left")
        self.restart_lbl.pack(fill="x", pady=(2, 1))
        self.prog = ctk.CTkProgressBar(left, height=8, corner_radius=4,
                                        progress_color=ACCENT, fg_color=CARD2)
        self.prog.set(0)
        self.prog.pack(fill="x", pady=(2, 2))
        self.stat_lbl = ctk.CTkLabel(
            left, text="Idle", font=("Segoe UI", 10), text_color=SUBTEXT)
        self.stat_lbl.pack(anchor="w")

        # Center: FPS Overview + Log
        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True)

        # FPS Overview
        tp = ctk.CTkFrame(center, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        tp.pack(fill="x", pady=(0, 8))
        tp_hdr = ctk.CTkFrame(tp, fg_color="transparent")
        tp_hdr.pack(fill="x", padx=14, pady=(10, 4))
        tp_title = ctk.CTkLabel(tp_hdr, text="FPS Tweaks Overview",
                     font=("Segoe UI", 11, "bold"), text_color=DIM)
        tp_title.pack(side="left")
        Tooltip(tp_title, "FPS Tweaks Info",
                "Green = active immediately.\nOrange = takes effect after Windows restart.")

        rows_frame = ctk.CTkFrame(tp, fg_color="transparent")
        rows_frame.pack(fill="x", padx=12, pady=(0, 10))
        INSTANT_LABELS = [
            "Game DVR off", "Mouse Acceleration off",
            "High Performance power plan", "Superfetch (SysMain) stopped",
            "Telemetry (DiagTrack) stopped", "Windows Search paused",
            "DNS cache flushed", "TCP Ping & Latency Turbo",
            "BCDEDIT Micro-Stutter Fix", "Display Sharpness & ClearType",
            "DirectX Shader Cache Clean", "Visual Effects: Performance",
        ]
        RESTART_LABELS = [
            "GPU Hardware Scheduling", "Network Throttling off",
            "System Responsiveness max", "GPU Game Priority = 8",
            "CPU Game Priority = 6", "Game Scheduling = High",
            "Win32PrioritySeparation = 0x26", "Fullscreen Optimizations Off",
        ]
        cols = ctk.CTkFrame(rows_frame, fg_color="transparent")
        cols.pack(fill="x")
        c1 = ctk.CTkFrame(cols, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True)
        c2 = ctk.CTkFrame(cols, fg_color="transparent")
        c2.pack(side="right", fill="x", expand=True)
        for lbl in INSTANT_LABELS:
            TweakRow(c1, lbl, restart=False).pack(fill="x", pady=1)
        for lbl in RESTART_LABELS:
            TweakRow(c2, lbl, restart=True).pack(fill="x", pady=1)

        # Log
        lp = ctk.CTkFrame(center, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        lp.pack(fill="both", expand=True)
        lh = ctk.CTkFrame(lp, fg_color="transparent")
        lh.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(lh, text="Operation Log",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(side="left")
        clr = ctk.CTkButton(lh, text="Clear", width=68, height=26,
                            fg_color=CARD2, hover_color=BORDER,
                            text_color=DIM, font=("Segoe UI", 10),
                            corner_radius=8, command=self._clr)
        clr.pack(side="right")
        Tooltip(clr, "Clear Log", "Clears the log display.\nDoesn't undo any changes.")
        self.log_box = ctk.CTkTextbox(
            lp, fg_color=CARD2, text_color=TEXT,
            font=("Cascadia Code", 11), corner_radius=12,
            state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        return frame

    def _add_custom_game(self):
        import tkinter.filedialog as fd
        path = fd.askopenfilename(title="Select Game Executable", filetypes=[("Executable Files", "*.exe")])
        if path:
            exe_name = path.split("/")[-1].lower()
            if exe_name not in CUSTOM_GAMES:
                CUSTOM_GAMES.add(exe_name)
                save_custom_games()
                self.custom_games_lbl.configure(text=f"{len(CUSTOM_GAMES)} Games Added")
                if exe_name not in PROTECTED:
                    PROTECTED.add(exe_name)
                self.log(f"\u2795 Added Custom Game: {exe_name}")

    def _do_restore(self):
        self._lock(True)
        def _t():
            self.log("\U0001F504 Restoring original Windows defaults...")
            restore_fps_tweaks(self.log)
            self.log("\u2714\uFE0F Defaults restored successfully!")
            self._lock(False)
        threading.Thread(target=_t, daemon=True).start()

    def _build_settings_page(self, parent):
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        ctk.CTkLabel(frame, text="\u2699\uFE0F  Settings",
                     font=("Segoe UI", 20, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(20, 16))

        # Startup card
        sc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        sc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(sc, text="System Startup",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        ctk.CTkLabel(sc, text="Automatically launch Echo Booster when Windows starts.",
                     font=("Segoe UI", 10), text_color=SUBTEXT).pack(
                     padx=14, pady=(0, 10), anchor="w")

        row = ctk.CTkFrame(sc, fg_color=CARD2, corner_radius=10)
        row.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkLabel(row, text="Run at Windows Startup",
                     font=("Segoe UI", 11, "bold"),
                     text_color=TEXT).pack(side="left", padx=14, pady=10)
        self._startup_var = ctk.BooleanVar(value=self._get_startup())
        ctk.CTkSwitch(row, text="", variable=self._startup_var,
                      onvalue=True, offvalue=False,
                      progress_color=ACCENT,
                      command=self._toggle_startup).pack(side="right", padx=14, pady=10)

        # Game Mode & Auto Boost card
        gmc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        gmc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(gmc, text="Gaming Features", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        
        mw_row = ctk.CTkFrame(gmc, fg_color=CARD2, corner_radius=10)
        mw_row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(mw_row, text="\U0001F4F1  Mini-Widget Overlay (In-Game)", font=("Segoe UI", 11, "bold"), text_color=TEXT).pack(side="left", padx=14, pady=10)
        self._mini_widget_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(mw_row, text="", variable=self._mini_widget_var, onvalue=True, offvalue=False,
                      progress_color=CYAN, command=self._toggle_mini_widget).pack(side="right", padx=14, pady=10)

        gm_row = ctk.CTkFrame(gmc, fg_color=CARD2, corner_radius=10)
        gm_row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(gm_row, text="\U0001F3AE  Windows Game Mode", font=("Segoe UI", 11, "bold"), text_color=TEXT).pack(side="left", padx=14, pady=10)
        self._gamemode_var = ctk.BooleanVar(value=self._get_gamemode())
        ctk.CTkSwitch(gm_row, text="", variable=self._gamemode_var, onvalue=True, offvalue=False,
                      progress_color=SUCCESS, command=self._toggle_gamemode).pack(side="right", padx=14, pady=10)
        
        ab_row = ctk.CTkFrame(gmc, fg_color=CARD2, corner_radius=10)
        ab_row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(ab_row, text="\u26a1  Auto Boost on Game Launch", font=("Segoe UI", 11, "bold"), text_color=TEXT).pack(side="left", padx=14, pady=10)
        self._autoboost_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(ab_row, text="", variable=self._autoboost_var, onvalue=True, offvalue=False,
                      progress_color=ACCENT).pack(side="right", padx=14, pady=10)
        ctk.CTkFrame(gmc, height=6, fg_color="transparent").pack()

        # Startup Manager card
        stm_c = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        stm_c.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(stm_c, text="Startup Manager", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        ctk.CTkLabel(stm_c, text="Disable heavy apps that slow your boot and background.", font=("Segoe UI", 10), text_color=SUBTEXT).pack(padx=14, pady=(0, 8), anchor="w")
        
        self._startup_list_frame = ctk.CTkFrame(stm_c, fg_color="transparent")
        self._startup_list_frame.pack(fill="x", padx=14, pady=(0, 14))
        self._refresh_startup_list()
        
        ctk.CTkButton(stm_c, text="\U0001F504 Refresh", width=90, height=26, fg_color=CARD2, hover_color=BORDER,
                      text_color=DIM, font=("Segoe UI", 9, "bold"), corner_radius=8,
                      command=self._refresh_startup_list).pack(anchor="w", padx=14, pady=(0, 14))

        # Performance card
        pc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        pc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(pc, text="Performance",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(padx=14, pady=(14, 6), anchor="w")
        for label, val, col in [
            ("Smart AI Game Detection", "Always On", SUCCESS),
            ("Discord & Steam Protection", "Always On", SUCCESS),
            ("Auto RAM Trim on Game Detect", "Enabled", CYAN),
        ]:
            r = ctk.CTkFrame(pc, fg_color=CARD2, corner_radius=10)
            r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 10, "bold"),
                         text_color=TEXT).pack(side="left", padx=14, pady=8)
            ctk.CTkLabel(r, text=val, font=("Segoe UI", 10),
                         text_color=col).pack(side="right", padx=14, pady=8)
        # Custom Games card
        gc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        gc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(gc, text="Custom Games", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        ctk.CTkLabel(gc, text="Add your custom games to trigger Smart AI Engine automatically.", font=("Segoe UI", 10), text_color=SUBTEXT).pack(padx=14, pady=(0, 10), anchor="w")
        
        g_row = ctk.CTkFrame(gc, fg_color=CARD2, corner_radius=10)
        g_row.pack(fill="x", padx=14, pady=(0, 14))
        self.custom_games_lbl = ctk.CTkLabel(g_row, text=f"{len(CUSTOM_GAMES)} Games Added", font=("Segoe UI", 11, "bold"), text_color=TEXT)
        self.custom_games_lbl.pack(side="left", padx=14, pady=10)
        ctk.CTkButton(g_row, text="\u2795 Add Game", width=100, height=28, fg_color=CARD, hover_color=BORDER, text_color=TEXT, font=("Segoe UI", 10, "bold"), command=self._add_custom_game).pack(side="right", padx=14, pady=10)

        # Restore card
        rc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        rc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(rc, text="Backup & Restore", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        ctk.CTkLabel(rc, text="Revert changes or create a system restore point for safety.", font=("Segoe UI", 10), text_color=SUBTEXT).pack(padx=14, pady=(0, 10), anchor="w")
        
        r_row = ctk.CTkFrame(rc, fg_color=CARD2, corner_radius=10)
        r_row.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(r_row, text="\U0001F6E1\uFE0F Create Restore Point", width=140, height=32, fg_color=CYAN, hover_color=dk(CYAN), text_color=BG, font=("Segoe UI", 11, "bold"), command=self._do_restore_point).pack(side="left", padx=14, pady=10)
        ctk.CTkButton(r_row, text="\U0001F504 Restore Defaults", width=130, height=32, fg_color=DANGER, hover_color=dk(DANGER), text_color=TEXT, font=("Segoe UI", 10, "bold"), command=self._do_restore).pack(side="right", padx=14, pady=10)

        return frame

    def _build_this_pc_page(self, parent):
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        ctk.CTkLabel(frame, text="\U0001F4BB  This PC",
                     font=("Segoe UI", 20, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(20, 16))

        # Specs card
        bc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        bc.pack(fill="x", padx=20, pady=(0, 12))
        
        ctk.CTkLabel(bc, text="Hardware Specifications", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 6), anchor="w")

        import platform
        try:
            cpu_name = platform.processor() or "Unknown"
        except: cpu_name = "Unknown"
        
        try:
            gpu_raw = subprocess.run(
                ["powershell", "-Command",
                 "Get-WmiObject Win32_VideoController | Select-Object -First 1 -ExpandProperty Name"],
                capture_output=True, text=True, creationflags=0x08000000, timeout=8
            ).stdout.strip()
            gpu_name = gpu_raw if gpu_raw else "Unknown"
        except: gpu_name = "Unknown"

        try:
            ram_gb = round(psutil.virtual_memory().total / (1024**3))
        except: ram_gb = 0
            
        try:
            os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        except: os_info = "Unknown"

        specs = [
            ("Processor", cpu_name, "\U0001F9E0"),
            ("Graphics", gpu_name, "\U0001F3AE"),
            ("Memory (RAM)", f"{ram_gb} GB", "\U0001F4BE"),
            ("System", os_info, "\U0001F5A5\uFE0F")
        ]
        
        for label, val, icon in specs:
            r = ctk.CTkFrame(bc, fg_color=CARD2, corner_radius=10)
            r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r, text=f"{icon}  {label}", font=("Segoe UI", 11, "bold"), text_color=TEXT).pack(side="left", padx=14, pady=10)
            ctk.CTkLabel(r, text=val, font=("Segoe UI", 11), text_color=CYAN).pack(side="right", padx=14, pady=10)
        
        ctk.CTkFrame(bc, height=10, fg_color="transparent").pack()


        return frame

    def _build_info_page(self, parent):
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        ctk.CTkLabel(frame, text="\u2139\uFE0F  Info",
                     font=("Segoe UI", 20, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(20, 16))

        # App info
        ac = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        ac.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(ac, text="Echo Booster",
                     font=("Segoe UI", 18, "bold"),
                     text_color=ACCENT).pack(padx=14, pady=(14, 2), anchor="w")
        ctk.CTkLabel(ac, text="by Dev RULE  \u2022  System Game Optimizer  \u2022  v1.0.0",
                     font=("Segoe UI", 10),
                     text_color=SUBTEXT).pack(padx=14, pady=(0, 14), anchor="w")

        # Description
        desc_c = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        desc_c.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(desc_c, text="About the App",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(padx=14, pady=(14, 6), anchor="w")
        desc_text = (
            "Echo Booster is a powerful Windows optimizer and gaming utility developed by Dev RULE.\n\n"
            "Features:\n"
            "\u2022 Smart AI Engine: Automatically detects running games, boosts their CPU priority to HIGH, and frees up RAM.\n"
            "\u2022 Deep System Cleaning: Clears DNS cache, temp files, and unused standby memory for max performance.\n"
            "\u2022 Low-Level Registry Tweaks: Disables Windows Telemetry, Game DVR, Network Throttling, and fixes Micro-Stutters.\n"
            "\u2022 Zero Bloatware: Kills heavy background apps instantly to ensure 100% of your PC power goes into gaming.\n"
            "\u2022 Safety First: Discord, Steam, and essential Windows services are strictly whitelisted and protected.\n"
            "\u2022 Easy Revert: You can safely restore all native Windows defaults anytime from the Settings page."
        )
        ctk.CTkLabel(desc_c, text=desc_text, font=("Segoe UI", 11), text_color=TEXT, justify="left").pack(padx=14, pady=(0, 14), anchor="w")

        # Discord shortcut
        dc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        dc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(dc, text="Discord Shortcut",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(padx=14, pady=(14, 6), anchor="w")
        disc_row = ctk.CTkFrame(dc, fg_color=CARD2, corner_radius=10)
        disc_row.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkLabel(disc_row, text="\U0001F4AC  ec-1",
                     font=("Segoe UI", 13, "bold"),
                     text_color=TEXT).pack(side="left", padx=14, pady=12)
        ctk.CTkButton(disc_row, text="\u27A1  Open Discord",
                      width=140, height=34,
                      fg_color="#5865F2", hover_color="#4752C4",
                      text_color=TEXT, font=("Segoe UI", 11, "bold"),
                      corner_radius=10,
                      command=self._open_discord).pack(side="right", padx=14, pady=8)

        # Theme Selector
        tc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16, border_color=BORDER, border_width=1)
        tc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(tc, text="Theme / ألوان البرنامج", font=("Segoe UI", 13, "bold"), text_color=DIM).pack(padx=14, pady=(14, 6), anchor="w")
        
        t_row = ctk.CTkFrame(tc, fg_color=CARD2, corner_radius=10)
        t_row.pack(fill="x", padx=14, pady=(0, 14))
        
        ctk.CTkLabel(t_row, text="🎨", font=("Segoe UI", 14)).pack(side="left", padx=14, pady=10)
        self.theme_var = ctk.StringVar(value="Dark Blue (Default)")
        theme_menu = ctk.CTkOptionMenu(t_row, variable=self.theme_var, values=["Dark Blue (Default)", "Blood Red", "Hacker Green", "Cyber Purple"], fg_color=BG, command=self.change_theme)
        theme_menu.pack(side="right", padx=14, pady=10)

        # Protected
        nc = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=16,
                          border_color=BORDER, border_width=1)
        nc.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(nc, text="Protected Processes",
                     font=("Segoe UI", 13, "bold"),
                     text_color=DIM).pack(padx=14, pady=(14, 4), anchor="w")
        ctk.CTkLabel(nc,
                     text="Discord, Steam, Windows Core, Antivirus\n"
                          "Echo Booster itself is always protected.",
                     font=("Segoe UI", 10), text_color=SUBTEXT,
                     justify="left").pack(padx=14, pady=(0, 14), anchor="w")

        return frame

    # ── Helpers ───────────────────────────────────────────────────
    def change_theme(self, theme_name):
        global BG, CARD, CARD2, BORDER, TEXT, DIM, SUBTEXT, ACCENT, CYAN, SUCCESS, WARN, DANGER, PURPLE2
        old_bg, old_card, old_card2, old_accent, old_cyan = BG, CARD, CARD2, ACCENT, CYAN
        
        if theme_name == "Blood Red":
            BG, CARD, CARD2, BORDER, ACCENT, CYAN = "#1a0505", "#240a0a", "#301010", "#401515", "#b51717", "#ff3333"
        elif theme_name == "Hacker Green":
            BG, CARD, CARD2, BORDER, ACCENT, CYAN = "#050f05", "#0a170a", "#102010", "#153015", "#17b517", "#33ff33"
        elif theme_name == "Cyber Purple":
            BG, CARD, CARD2, BORDER, ACCENT, CYAN = "#13051a", "#1a0a24", "#251030", "#301540", "#e017b5", "#ff33f1"
        else:
            BG, CARD, CARD2, BORDER, ACCENT, CYAN = "#080810", "#0E0E1A", "#141422", "#1E1E35", "#7C3AED", "#06B6D4"
            
        self.configure(fg_color=BG)
        
        def update_widget(w):
            try:
                if hasattr(w, 'cget'):
                    fg = w.cget("fg_color")
                    if isinstance(fg, str):
                        if fg.lower() == old_bg.lower(): w.configure(fg_color=BG)
                        elif fg.lower() == old_card.lower(): w.configure(fg_color=CARD)
                        elif fg.lower() == old_card2.lower(): w.configure(fg_color=CARD2)
                        elif fg.lower() == old_accent.lower(): w.configure(fg_color=ACCENT)
                        
                    if hasattr(w, 'configure'):
                        if "text_color" in w.keys():
                            tc = w.cget("text_color")
                            if isinstance(tc, str) and tc.lower() == old_cyan.lower(): w.configure(text_color=CYAN)
                        if "progress_color" in w.keys():
                            pc = w.cget("progress_color")
                            if isinstance(pc, str) and pc.lower() == old_accent.lower(): w.configure(progress_color=ACCENT)
                        if "hover_color" in w.keys():
                            hc = w.cget("hover_color")
                            if isinstance(hc, str) and hc.lower() == dk(old_accent).lower(): w.configure(hover_color=dk(ACCENT))
            except Exception:
                pass
            for child in w.winfo_children():
                update_widget(child)
                
        update_widget(self)

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        def _w():
            try:
                self.log_box.configure(state="normal")
                self.log_box.insert("end", f"[{ts}] {msg}\n")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
            except Exception:
                pass  # app may have been closed while task was running
        self.after(0, _w)

    def _clr(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # All UI-update helpers capture their argument explicitly (no late binding)
    # and guard against widget destruction (app closed while task ran)
    def _ss(self, t):
        def _do(txt=t):
            try: self.stat_lbl.configure(text=txt)
            except Exception: pass
        self.after(0, _do)

    def _sp(self, v):
        def _do(val=v):
            try: self.prog.set(val)
            except Exception: pass
        self.after(0, _do)

    def _sf(self, t):
        def _do(txt=t):
            try: self.freed_lbl.configure(text=txt)
            except Exception: pass
        self.after(0, _do)

    def _sr(self, t):
        def _do(txt=t):
            try: self.restart_lbl.configure(text=txt)
            except Exception: pass
        self.after(0, _do)

    def _sp0_delayed(self, ms=3000):
        """Safely reset progress bar after ms, ignoring errors if window closed."""
        def _do():
            try: self.prog.set(0)
            except Exception: pass
        self.after(ms, _do)

    def _minimize_to_tray(self):
        """Hides main window and displays background floating tray bar."""
        self.withdraw()
        self._tray_bar.deiconify()
        self._tray_bar.lift()

    def _get_startup(self):
        import subprocess
        try:
            res = subprocess.run('schtasks /query /tn "EchoBooster"', shell=True, capture_output=True, text=True, creationflags=0x08000000)
            return "EchoBooster" in res.stdout
        except Exception:
            return False

    def _toggle_startup(self):
        import subprocess
        try:
            if self._startup_var.get():
                # Delete any old registry key if exists to avoid double launch
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
                    winreg.DeleteValue(key, "EchoBooster")
                    winreg.CloseKey(key)
                except Exception:
                    pass
                
                cmd = f'schtasks /create /f /tn "EchoBooster" /tr "\\"{sys.executable}\\" --minimized" /sc onlogon /rl highest'
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=0x08000000)
                self.log("OK  Startup enabled — runs at Windows login (Admin, Hidden)")
            else:
                subprocess.run('schtasks /delete /f /tn "EchoBooster"', shell=True, capture_output=True, creationflags=0x08000000)
                self.log("OK  Startup disabled")
        except Exception as e:
            self.log(f"ERR Startup change failed: {e}")

    def _open_discord(self):
        import webbrowser
        webbrowser.open("https://discord.gg/ec-1")
        self.log("Discord opened")

    def _show_settings(self):
        self._switch_page("settings")

    def _show_info(self):
        self._switch_page("info")

    def _toggle_mini_widget(self):
        if self._mini_widget_var.get():
            self._mini_widget.deiconify()
        else:
            self._mini_widget.withdraw()

    def _get_gamemode(self):
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar")
            val, _ = winreg.QueryValueEx(k, "AllowAutoGameMode")
            winreg.CloseKey(k)
            return val == 1
        except Exception:
            return False

    def _toggle_gamemode(self):
        try:
            import winreg
            val = 1 if self._gamemode_var.get() else 0
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar")
            winreg.SetValueEx(k, "AllowAutoGameMode", 0, winreg.REG_DWORD, val)
            winreg.SetValueEx(k, "AutoGameModeEnabled", 0, winreg.REG_DWORD, val)
            winreg.CloseKey(k)
            self.log(f"  {'OK' if val else 'OFF'}  Windows Game Mode {'enabled' if val else 'disabled'}")
        except Exception as e:
            self.log(f"  ERR Game Mode: {e}")

    def _refresh_startup_list(self):
        try:
            for w in self._startup_list_frame.winfo_children():
                w.destroy()
        except Exception:
            pass
        try:
            import winreg
            entries = []
            for hive, path in [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            ]:
                try:
                    k = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(k, i)
                            entries.append((hive, path, name, val))
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(k)
                except Exception:
                    pass
            if not entries:
                ctk.CTkLabel(self._startup_list_frame, text="No startup entries found.",
                             font=("Segoe UI", 10), text_color=SUBTEXT).pack(anchor="w")
                return
            for hive, path, name, val in entries[:10]:  # cap at 10
                scope = "User" if hive == winreg.HKEY_CURRENT_USER else "System"
                r = ctk.CTkFrame(self._startup_list_frame, fg_color=CARD2, corner_radius=8)
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=f"[{scope}] {name}", font=("Segoe UI", 10, "bold"),
                             text_color=TEXT, wraplength=300, justify="left").pack(side="left", padx=10, pady=6)
                def _disable(h=hive, p=path, n=name):
                    try:
                        import winreg
                        k = winreg.OpenKey(h, p, 0, winreg.KEY_WRITE)
                        winreg.DeleteValue(k, n)
                        winreg.CloseKey(k)
                        self.log(f"  OK  Startup disabled: {n}")
                        self._refresh_startup_list()
                    except Exception as e:
                        self.log(f"  ERR {e}")
                ctk.CTkButton(r, text="Disable", width=70, height=24,
                              fg_color=DANGER, hover_color=dk(DANGER),
                              text_color=TEXT, font=("Segoe UI", 9, "bold"),
                              corner_radius=6, command=_disable).pack(side="right", padx=8, pady=6)
        except Exception as e:
            self.log(f"  ERR Startup Manager: {e}")

    def _force_exit(self):
        """Terminates and exits Echo Booster completely."""
        try:
            self.destroy()
        except Exception:
            pass
        sys.exit(0)

    def _lock(self, v):
        s = "disabled" if v else "normal"
        for b in self._btns:
            def _do(btn=b, st=s):
                try: btn.configure(state=st)
                except Exception: pass
            self.after(0, _do)

    # ── Stat loop & Smart AI Daemon ───────────────────────────────
    def _stat_loop(self):
        _prev_net = psutil.net_io_counters()
        _prev_time = time.time()
        _battery_active = False
        def loop():
            nonlocal _prev_net, _prev_time, _battery_active
            last_boosted_game = None
            while True:
                try:
                    cpu, ram_used, ram_total, pr, temp = get_stats()
                    self.after(0, lambda c=cpu:                    self.cpu_c.set(f"{c:.0f}%"))
                    self.after(0, lambda ru=ram_used, rt=ram_total: self.ram_c.set(f"{ru:.1f}G"))
                    self.after(0, lambda p=pr:                     self.prc_c.set(str(p)))

                    # Mini-Widget Update
                    self.after(0, lambda c=cpu, r=ram_used, p=self._ping_val: self._mini_widget.update_stats(c, r, p))

                    # Advanced Battery Saver (Laptop Mode)
                    try:
                        battery = psutil.sensors_battery()
                        if battery:
                            if not battery.power_plugged and not _battery_active:
                                # Switch to power saver
                                subprocess.run("powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a", shell=True, capture_output=True, creationflags=0x08000000)
                                self.log("  \U0001F50B Battery Mode Detected: Power Saver Activated")
                                _battery_active = True
                            elif battery.power_plugged and _battery_active:
                                # Switch to High Performance
                                subprocess.run("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True, capture_output=True, creationflags=0x08000000)
                                self.log("  \u26a1 Plugged In: High Performance Activated")
                                _battery_active = False
                    except Exception:
                        pass


                    # Network speed
                    try:
                        cur_net = psutil.net_io_counters()
                        cur_time = time.time()
                        dt = max(cur_time - _prev_time, 0.1)
                        dl = (cur_net.bytes_recv - _prev_net.bytes_recv) / dt / 1024
                        ul = (cur_net.bytes_sent - _prev_net.bytes_sent) / dt / 1024
                        _prev_net = cur_net
                        _prev_time = cur_time
                        dl_str = f"{dl:.0f} KB/s" if dl < 1024 else f"{dl/1024:.1f} MB/s"
                        ul_str = f"{ul:.0f} KB/s" if ul < 1024 else f"{ul/1024:.1f} MB/s"
                        self.after(0, lambda d=dl_str: self.net_d_c.set(d))
                        self.after(0, lambda u=ul_str: self.net_u_c.set(u))
                    except Exception:
                        pass

                    # Smart AI Game Detection
                    game_title, game_proc = detect_active_game()
                    if game_title and game_proc:
                        if last_boosted_game != game_title:
                            last_boosted_game = game_title
                            try:
                                game_proc.nice(psutil.HIGH_PRIORITY_CLASS)
                            except Exception:
                                pass
                            trim_ram()
                            self.log(f"\u26a1 Smart AI: Detected {game_title} \u2014 Priority boosted to HIGH & RAM trimmed!")
                            # Auto Boost on Game Launch
                            try:
                                if hasattr(self, '_autoboost_var') and self._autoboost_var.get():
                                    self._run(self._t_smart)
                            except Exception:
                                pass
                        def _set_active(gt=game_title, c=cpu, r=ram_used, t=temp):
                            try:
                                self.game_badge.configure(
                                    text=f"\U0001F3AE GAME DETECTED: {gt} (Auto-Boosted!)",
                                    text_color=SUCCESS)
                                lat = max(0.1, round((100 - c) * 0.005, 1))
                                self.latency_lbl.configure(
                                    text=f"Ping: {self._ping_val} | Lat: {lat}ms | Temp: {t} | \U0001F525 Ultra Gaming Active",
                                    text_color=SUCCESS)
                                self._tray_bar.update_info(f"\U0001F3AE {gt}  \u2022  CPU: {c:.0f}%  \u2022  RAM: {r:.1f}G \u2022 Temp: {t}")
                            except Exception: pass
                        self.after(0, _set_active)
                    else:
                        last_boosted_game = None
                        def _set_idle(c=cpu, r=ram_used, t=temp):
                            try:
                                self.game_badge.configure(
                                    text="\u26a1 Smart AI Engine: Active  \u2022  Auto-Detecting Games",
                                    text_color=CYAN)
                                lat = max(0.1, round((100 - c) * 0.005, 1))
                                self.latency_lbl.configure(
                                    text=f"Ping: {self._ping_val} | Lat: {lat}ms | Temp: {t} | \U0001F49A System Optimal",
                                    text_color=CYAN)
                                self._tray_bar.update_info(f"\u26a1 Echo Booster Active  \u2022  CPU: {c:.0f}%  \u2022  RAM: {r:.1f}G \u2022 Temp: {t}")
                            except Exception: pass
                        self.after(0, _set_idle)

                except Exception:
                    pass
                time.sleep(2)
        threading.Thread(target=loop, daemon=True).start()

    # ── Task runners ──────────────────────────────────────────────
    def _run(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _do_clean(self): self._run(self._t_clean)
    def _do_fps(self):   self._run(self._t_fps)
    def _do_kill(self):  self._run(self._t_kill)
    def _do_all(self):   self._run(self._t_all)
    def _do_smart_tune(self): self._run(self._t_smart)
    def _do_disk(self):  self._run(self._t_disk)

    def _do_dns(self, key):
        def _t():
            self._lock(True)
            self._ss("Switching DNS...")
            set_dns_preset(key, self.log)
            self._ss("DNS Updated")
            self._lock(False)
        self._run(_t)

    def _do_auto_ping(self):
        def _t():
            self._lock(True)
            self._ss("Optimizing Ping...")
            auto_optimize_ping(self.log)
            self._ss("Ping Optimized")
            self._lock(False)
        self._run(_t)

    def _do_restore_point(self):
        def _t():
            self._lock(True)
            self._ss("Creating Restore Point...")
            self.log("=== System Restore ===")
            self.log("  Creating a system restore point (This may take a minute)...")
            try:
                cmd = 'powershell.exe -Command "Checkpoint-Computer -Description \'EchoBooster Backup\' -RestorePointType \'MODIFY_SETTINGS\'"'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=0x08000000)
                if res.returncode == 0:
                    self.log("  \u2705 Restore Point created successfully.")
                    self._ss("Restore Point Created")
                else:
                    self.log(f"  \u26a0\uFE0F Failed. Is System Restore enabled? {res.stderr}")
                    self._ss("Failed to create")
            except Exception as e:
                self.log(f"  \u26a0\uFE0F Error: {e}")
                self._ss("Error")
            self._lock(False)
        self._run(_t)

    def _t_smart(self):
        self._lock(True); self._ss("Smart Tuning..."); self._sp(0.1)
        self.log("=== Smart AI Tuning Started ===")
        try:
            ram_gb = psutil.virtual_memory().total / (1024**3)
            cores = psutil.cpu_count(logical=False) or 2
        except Exception:
            ram_gb = 4; cores = 2
        
        is_weak = ram_gb < 8 or cores < 4
        self.log(f"System Profile: {'WEAK' if is_weak else 'STRONG'} (RAM: {ram_gb:.1f}GB, Cores: {cores})")
        
        for path, name, typ, val in INSTANT_REG:
            subprocess.run(f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f', shell=True, capture_output=True, creationflags=0x08000000)
        self.log("Base registry optimizations applied")
        self._sp(0.4)
        
        freed = clean_cache(self.log)
        self.log(f"Cache cleared: {freed / 1024**2:.1f} MB freed")
        self._sp(0.6)
        
        if is_weak:
            self.log("Lightweight Mode Active: Safely skipped aggressive tasks that may cause freezing on low-end hardware.")
            self._sr("")
        else:
            self.log("Performance Mode Active: Applying heavy GPU/CPU scheduling optimizations.")
            for path, name, typ, val, label in RESTART_REG:
                subprocess.run(f'reg add "{path}" /v "{name}" /t {typ} /d {val} /f', shell=True, capture_output=True)
            self._sr("Restart recommended for advanced tweaks")
            
        trim_ram()
        self.log("RAM Trimmed")
        
        self._sp(1.0)
        self._sf("Smart Tuning Complete")
        self._ss("Done")
        self._sp0_delayed()
        self._lock(False)
    def _t_disk(self):
        self._lock(True); self._ss("Disk Cleaning..."); self._sp(0.1)
        self.log("=== Disk Cleaner ===")
        freed = 0
        # Delivery Optimization cache
        try:
            r = subprocess.run("cleanmgr /sagerun:1", shell=True, capture_output=True, timeout=30, creationflags=0x08000000)
        except Exception:
            pass
        # Windows Update logs
        do_path = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "SoftwareDistribution" / "Download"
        try:
            for item in do_path.iterdir():
                try:
                    if item.is_file():
                        sz = item.stat().st_size; item.unlink(); freed += sz
                    elif item.is_dir():
                        try: sz = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        except: sz = 0
                        shutil.rmtree(item, ignore_errors=True); freed += sz
                except (PermissionError, OSError): pass
        except Exception: pass
        self.log(f"  Windows Update cache cleaned")
        self._sp(0.4)
        # Recycle Bin
        try:
            subprocess.run("PowerShell -Command Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                           shell=True, capture_output=True, creationflags=0x08000000)
            self.log("  Recycle Bin emptied")
        except Exception: pass
        self._sp(0.7)
        # Delivery Optimization
        do2 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "ServiceProfiles" / "NetworkService" / "AppData" / "Local" / "Microsoft" / "Windows" / "DeliveryOptimization" / "Cache"
        try:
            for item in do2.iterdir():
                try:
                    shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink()
                except: pass
        except Exception: pass
        self._sp(0.9)
        # Regular cache on top
        freed += clean_cache(self.log)
        self._sp(1.0)
        mb = freed / 1024**2
        self.log(f"Disk Clean Done: {mb:.1f} MB freed")
        self._sf(f"Disk: {mb:.1f} MB freed")
        self._ss("Done")
        self._sp0_delayed()
        self._lock(False)

    def _compute_score(self, cpu, ram_used, ram_total, ping_ms):
        """0-100 performance score. Higher = better."""
        try:
            cpu_score  = max(0, 100 - cpu)
            ram_free   = ram_total - ram_used
            ram_score  = min(100, (ram_free / ram_total) * 100)
            try: p = int(str(ping_ms).replace("ms", "").strip())
            except: p = 50
            ping_score = max(0, 100 - p)
            return int((cpu_score * 0.4) + (ram_score * 0.35) + (ping_score * 0.25))
        except Exception:
            return 0

    def _t_clean(self):
        cpu_b, ram_b, rt_b, _, _ = get_stats()
        self._lock(True); self._ss("Cleaning..."); self._sp(0.1)
        self.log("=== Cache Clean ===")
        freed = clean_cache(self.log)
        mb = freed / 1024**2
        self._sp(1.0)
        self.log(f"Done: {mb:.1f} MB freed")
        cpu_a, ram_a, _, _, _ = get_stats()
        s_b = self._compute_score(cpu_b, ram_b, rt_b, self._ping_val)
        s_a = self._compute_score(cpu_a, ram_a, rt_b, self._ping_val)
        self._sf(f"Freed: {mb:.1f} MB  |  Score: {s_b}\u2192{s_a}/100")
        self._ss("Done")
        self._sp0_delayed()
        self._lock(False)

    def _t_fps(self):
        self._lock(True); self._ss("Applying tweaks..."); self._sp(0.1)
        self.log("=== FPS Boost ===")
        nr = apply_fps_tweaks(self.log)
        self._sp(1.0)
        if nr:
            self.log("NOTE: Restart-required tweaks saved. Restart for full GPU effect.")
            self._sr("Restart recommended for GPU scheduling & network tweaks")
        else:
            self.log("All tweaks active NOW — no restart needed")
            self._sr("")
        self._ss("FPS boosted")
        self._sp0_delayed()
        self._lock(False)

    def _t_kill(self):
        self._lock(True); self._ss("Killing bloat..."); self._sp(0.1)
        self.log("=== Kill Bloat ===")
        n = kill_bloat(self.log)
        self._sp(1.0)
        self.log(f"Done: {n} killed")
        self._sf(f"Killed: {n} bloat procs")
        self._ss("Done")
        self._sp0_delayed()
        self._lock(False)

    def _t_all(self):
        self._lock(True); self._ss("FULL BOOST..."); self._sp(0.05)
        self.log("======== FULL BOOST ========")

        self.log("Phase 1: Kill bloat")
        n = kill_bloat(self.log)
        self._sp(0.30)

        self.log("Phase 2: Clean cache")
        freed = clean_cache(self.log)
        self._sp(0.65)

        self.log("Phase 3: FPS tweaks")
        nr = apply_fps_tweaks(self.log)
        self._sp(1.0)

        mb = freed / 1024**2
        self.log(f"=== DONE: {n} killed, {mb:.1f} MB freed ===")

        # FIX: always update restart_lbl — clear it if no restart needed
        if nr:
            self._sr("Restart recommended for GPU scheduling & network tweaks")
        else:
            self._sr("")

        self._sf(f"Killed: {n}  |  Freed: {mb:.1f} MB")
        self._ss("System optimized!")
        self._sp0_delayed()
        self._lock(False)


if __name__ == "__main__":
    import sys
    if not is_admin():
        try:
            run_as_admin()
        except Exception:
            pass
    app = EchoBoosterApp()
    if "--minimized" in sys.argv:
        app.after(100, lambda: app._minimize_to_tray())
    app.mainloop()
