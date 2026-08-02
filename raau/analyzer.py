import math

class AssessmentEngine:
    # Motherboard display port database from Excel sheet "Recommended motherboards"
    MOTHERBOARD_DB = {
        "MSI PRO B660M-A": {"ports": 4, "pcie_slots": 2},
        "MSI PRO B760M-A": {"ports": 4, "pcie_slots": 2},
        "GIGABYTE B760M DS3H": {"ports": 4, "pcie_slots": 1},
        "GIGABYTE B660M DS3H": {"ports": 4, "pcie_slots": 1},
        "MSI B760M GAMING PLUS": {"ports": 4, "pcie_slots": 2},
        "MSI B760 GAMING PLUS": {"ports": 2, "pcie_slots": 5},
        "MSI PRO B760-P": {"ports": 2, "pcie_slots": 5},
        "MSI PRO B760-VC": {"ports": 0, "pcie_slots": 5},
        "ASROCK ATX FATAL1TY B450": {"ports": 3, "pcie_slots": 2},
        "GIGABYTE Z590 AORUS ELITE": {"ports": 2, "pcie_slots": 3},
        "MSI B450M TOMAHAWK": {"ports": 2, "pcie_slots": 2},
        "MSI X470": {"ports": 2, "pcie_slots": 3}
    }

    @classmethod
    def _get_motherboard_ports(cls, mobo_string: str) -> int:
        mobo_upper = mobo_string.upper()
        for key, info in cls.MOTHERBOARD_DB.items():
            if key in mobo_upper:
                return info["ports"]
        # Default fallback for unknown motherboards
        return 2

    @classmethod
    def analyze(cls, data: dict) -> dict:
        score = 0
        alerts = []
        recommendations = []

        # ---------------------------------------------------------
        # 1. Operating System Audit
        # ---------------------------------------------------------
        is_windows = data.get("is_windows", True)
        if not is_windows:
            alerts.append("ASTER requires Windows OS (10/11). Deploy on a Windows machine.")

        # ---------------------------------------------------------
        # 2. CPU Scoring & Core Assessment
        # ---------------------------------------------------------
        cpu_name = data.get("cpu", "").upper()
        cores = data.get("cores", 4)
        has_integrated_gpu = "G" in cpu_name or "INTEL" in cpu_name or "RYZEN 5 5600G" in cpu_name or "RYZEN 5 5700G" in cpu_name

        if any(chip in cpu_name for chip in ["I7", "I9", "RYZEN 7", "RYZEN 9"]):
            cpu_eval = "EXCELLENT"
            score += 35
        elif any(chip in cpu_name for chip in ["I5", "RYZEN 5"]) or cores >= 6:
            cpu_eval = "EXCELLENT"
            score += 30
        elif any(chip in cpu_name for chip in ["I3", "RYZEN 3"]) or cores >= 4:
            cpu_eval = "GOOD"
            score += 20
        else:
            cpu_eval = "FAIR"
            score += 10
            alerts.append("Entry-level processor. Recommended for 2 basic user seats max.")

        # Warn if CPU lacks Integrated Graphics (e.g., Intel 'F' series or AMD non-'G')
        if "F" in cpu_name and "INTEL" in cpu_name:
            has_integrated_gpu = False
            alerts.append("CPU lacks Integrated Graphics ('F' variant). Motherboard display outputs will not work.")

        # ---------------------------------------------------------
        # 3. RAM & Workplace Capacity Calculation Matrix
        # ---------------------------------------------------------
        ram = data.get("ram_gb", 16)
        
        # Sizing Rule: 4GB for Host OS + 4GB per concurrent ASTER user seat
        available_ram_for_seats = max(0, ram - 4)
        ram_capacity = (available_ram_for_seats // 4) + 1  # 1 Host + N Additional Seats

        if ram >= 32:
            ram_eval = "EXCELLENT (32GB+)"
            score += 35
        elif ram >= 16:
            ram_eval = "GOOD (16GB)"
            score += 25
        else:
            ram_eval = "NEEDS UPGRADE"
            score += 10
            alerts.append("RAM below 16GB. Upgrade RAM for multi-seat workplaces.")

        # Determine Workplace Capacity (Bottleneck = MIN of RAM Capacity, Cores, or Spec Tier Limit)
        capacity = int(min(ram_capacity, max(1, cores)))
        
        # Cap based on Excel Spreadsheet Tiers (i3 -> max 4, i5 -> max 8, i7 -> max 12)
        if "I3" in cpu_name:
            capacity = min(capacity, 4)
        elif "I5" in cpu_name or "RYZEN 5" in cpu_name:
            capacity = min(capacity, 8)
        elif "I7" in cpu_name or "I9" in cpu_name or "RYZEN 7" in cpu_name:
            capacity = min(capacity, 12)

        # ---------------------------------------------------------
        # 4. Storage Assessment
        # ---------------------------------------------------------
        storage_type = data.get("storage_type", "").upper()
        if "SSD" in storage_type or "NVME" in storage_type:
            storage_eval = "EXCELLENT (SSD)"
            score += 15
        else:
            storage_eval = "FAIR (HDD)"
            alerts.append("HDD detected. Upgrade OS drive to SSD for fast multi-seat performance.")

        # ---------------------------------------------------------
        # 5. Motherboard Video Outputs & Discrete GPU Calculation
        # ---------------------------------------------------------
        mobo_name = data.get("motherboard", "")
        onboard_ports = cls._get_motherboard_ports(mobo_name) if has_integrated_gpu else 0
        
        # Calculate video port deficit
        monitors_detected = data.get("monitors_detected", 1)
        needed_ports = max(capacity, monitors_detected)
        port_deficit = max(0, needed_ports - onboard_ports)

        # Discrete GPUs required (e.g. ASUS GT710/GT730 4HDMI provides 4 display ports each)
        gpus_needed = math.ceil(port_deficit / 4.0) if port_deficit > 0 else 0
        
        adapter_cost = 0

        # Display Adapters & GPU Recommendations
        if gpus_needed > 0:
            gpu_cost = gpus_needed * 4500  # Approx. ₹4,500 per ASUS 4HDMI GPU
            adapter_cost += gpu_cost
            recommendations.append(
                f"Add {gpus_needed}x 4-Port Graphics Card (e.g., ASUS GT710/GT730 4HDMI) (~₹{gpu_cost:,})"
            )

        # Active DisplayPort to HDMI Adapters (Excel recommends DP-to-HDMI active adapters for DP ports)
        dp_adapters_needed = min(2, capacity) if onboard_ports >= 2 else 0
        if dp_adapters_needed > 0:
            dp_cost = dp_adapters_needed * 450
            adapter_cost += dp_cost
            recommendations.append(f"Add {dp_adapters_needed}x Active DisplayPort-to-HDMI Adapters (~₹{dp_cost:,})")

        # ---------------------------------------------------------
        # 6. USB Peripherals Ratio & Hub Allocation
        # ---------------------------------------------------------
        usb_ports = data.get("usb_ports_count", 4)
        # Excel spec: 1 USB Hub per workplace OR 1 4-Port Hub per 2 workplaces
        hubs_needed = math.ceil(capacity / 2.0)
        
        if usb_ports < (capacity * 2):
            hub_cost = hubs_needed * 350
            adapter_cost += hub_cost
            recommendations.append(f"Add {hubs_needed}x 4-Port USB Hubs for keyboards/mice (~₹{hub_cost:,})")

        # ---------------------------------------------------------
        # 7. Final Score Scaling & Status
        # ---------------------------------------------------------
        total_score = min(score + 15, 98)
        
        if total_score >= 85 and is_windows:
            stars = "★★★★★"
            status = "READY FOR ASTER"
        elif total_score >= 65:
            stars = "★★★★☆"
            status = "NEEDS MINOR UPGRADE"
        else:
            stars = "★★☆☆☆"
            status = "NOT RECOMMENDED"

        # ---------------------------------------------------------
        # 8. Financial ROI & 5-Year Savings Engine (Per PC)
        # ---------------------------------------------------------
        # Hardware PC Avoided: ₹35,000 saved per N-1 physical PC avoided
        pcs_avoided = max(0, capacity - 1)
        hardware_saved_per_pc = pcs_avoided * 35000 
        
        # Power Savings: 38% annual reduction per avoided PC (~₹1,200/year power savings)
        elec_savings_pct = 38 if capacity >= 2 else 0
        annual_elec_saved = pcs_avoided * 1200
        
        # Net 5-Year Benefit = (Hardware Saved + 5 Yrs Power Saved) - Accessory Hardware Upgrades Cost
        five_year_savings = (hardware_saved_per_pc + (annual_elec_saved * 5)) - adapter_cost

        return {
            "score_pct": total_score,
            "star_rating": stars,
            "status": status,
            "capacity": capacity,
            "cpu_eval": cpu_eval,
            "ram_eval": ram_eval,
            "storage_eval": storage_eval,
            "onboard_ports": onboard_ports,
            "gpus_needed": gpus_needed,
            "recommendations": recommendations,
            "alerts": alerts,
            "hardware_saved_inr": hardware_saved_per_pc,
            "adapter_cost_inr": adapter_cost,
            "elec_savings_pct": elec_savings_pct,
            "five_year_savings_inr": max(0, five_year_savings)
        }