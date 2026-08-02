import os
import platform
import subprocess
import json

class HardwareCollector:
    @staticmethod
    def _run_powershell(cmd: str):
        full_cmd = f"powershell -NoProfile -Command \"{cmd} | ConvertTo-Json -Compress\""
        try:
            result = subprocess.run(
                full_cmd, capture_output=True, text=True, shell=True, timeout=8
            )
            if result.stdout.strip():
                return json.loads(result.stdout)
        except Exception:
            pass
        return {}

    @classmethod
    def collect_specs(cls) -> dict:
        system_os = platform.system().lower()
        is_windows = system_os == "windows"

        if is_windows:
            # 1. Computer & BIOS Specs
            bios_info = cls._run_powershell("Get-CimInstance Win32_BIOS")
            bios_info = bios_info[0] if isinstance(bios_info, list) else bios_info
            
            sys_info = cls._run_powershell("Get-CimInstance Win32_ComputerSystem")
            sys_info = sys_info[0] if isinstance(sys_info, list) else sys_info

            # 2. Processor Specs
            cpu_info = cls._run_powershell("Get-CimInstance Win32_Processor")
            cpu_info = cpu_info[0] if isinstance(cpu_info, list) else cpu_info

            # 3. RAM Specs (Slots, Speed, Installed, Available)
            ram_info = cls._run_powershell("Get-CimInstance Win32_PhysicalMemory")
            total_ram_gb = 0
            speed = 0
            slots_used = 0
            if isinstance(ram_info, list):
                slots_used = len(ram_info)
                total_ram_gb = sum(int(m.get("Capacity", 0)) for m in ram_info) / (1024**3)
                speed = ram_info[0].get("Speed", 0) if ram_info else 0
            elif isinstance(ram_info, dict) and ram_info:
                slots_used = 1
                total_ram_gb = int(ram_info.get("Capacity", 0)) / (1024**3)
                speed = ram_info.get("Speed", 0)

            os_perf = cls._run_powershell("Get-CimInstance Win32_OperatingSystem")
            os_perf = os_perf[0] if isinstance(os_perf, list) else os_perf
            avail_ram_gb = round(int(os_perf.get("FreePhysicalMemory", 0)) / (1024**2), 1)

            # 4. Storage Specs (SSD vs HDD)
            disk_info = cls._run_powershell("Get-PhysicalDisk")
            media_types = []
            if isinstance(disk_info, list):
                media_types = [d.get("MediaType", "Unknown") for d in disk_info]
            elif isinstance(disk_info, dict) and disk_info:
                media_types = [disk_info.get("MediaType", "Unknown")]

            # 5. Graphics & Video Outputs
            gpu_info = cls._run_powershell("Get-CimInstance Win32_VideoController")
            gpu_name = gpu_info[0].get("Name", "Generic GPU") if isinstance(gpu_info, list) else gpu_info.get("Name", "Generic GPU")

            monitors = cls._run_powershell("Get-CimInstance Win32_DesktopMonitor")
            monitor_count = len(monitors) if isinstance(monitors, list) else (1 if monitors else 1)

            # 6. USB Ports Breakdown
            usb_devices = cls._run_powershell("Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -eq 'USB'}")
            usb_count = len(usb_devices) if isinstance(usb_devices, list) else 6

            # 7. Security / Health (TPM & Windows Activation)
            tpm_info = cls._run_powershell("Get-Tpm")
            tpm_present = tpm_info.get("TpmPresent", False) if isinstance(tpm_info, dict) else False

            return {
                "is_windows": True,
                "pc_name": platform.node(),
                "manufacturer": sys_info.get("Manufacturer", "Generic"),
                "model": sys_info.get("Model", "Standard PC"),
                "serial_number": bios_info.get("SerialNumber", "N/A"),
                "bios_version": bios_info.get("SMBIOSBIOSVersion", "N/A"),
                "os": f"{platform.system()} {platform.release()} ({os_perf.get('BuildNumber', '')})",
                "cpu": cpu_info.get("Name", "Intel/AMD Processor").strip(),
                "cores": cpu_info.get("NumberOfCores", 4),
                "threads": cpu_info.get("NumberOfLogicalProcessors", 4),
                "ram_gb": round(total_ram_gb, 1) or 8.0,
                "avail_ram_gb": avail_ram_gb,
                "ram_speed_mhz": speed,
                "ram_slots_used": slots_used,
                "storage_type": "/".join(set(media_types)) or "SSD/HDD",
                "gpu": gpu_name,
                "monitors_detected": monitor_count,
                "usb_ports_count": usb_count,
                "tpm_present": tpm_present
            }
        else:
            # Fallback for macOS/Linux testing
            mac_ram = 16.0
            try:
                out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
                mac_ram = round(int(out) / (1024**3), 1)
            except Exception:
                pass

            return {
                "is_windows": False,
                "pc_name": platform.node(),
                "manufacturer": "Apple",
                "model": "MacBook Air",
                "serial_number": "C02F12345678",
                "bios_version": "Apple EFI",
                "os": f"{platform.system()} {platform.release()}",
                "cpu": "Apple Silicon M-Series",
                "cores": os.cpu_count() or 8,
                "threads": os.cpu_count() or 8,
                "ram_gb": mac_ram,
                "avail_ram_gb": round(mac_ram * 0.6, 1),
                "ram_speed_mhz": 6400,
                "ram_slots_used": 1,
                "storage_type": "NVMe SSD",
                "gpu": "Apple Integrated GPU",
                "monitors_detected": 1,
                "usb_ports_count": 4,
                "tpm_present": True
            }