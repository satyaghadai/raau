import os
from raau.collector import HardwareCollector
from raau.analyzer import AssessmentEngine
from raau.pdf_generator import PDFReportGenerator

def launch_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("\n[!] GUI Error: Tkinter is not installed on this system.")
        print("    Run terminal mode using: python main.py --check\n")
        return

    class RAAUApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Resofto ASTER Assessment Utility (RAAU)")
            self.geometry("640x720")
            self.resizable(False, False)
            self._create_widgets()
            self.run_assessment()

        def _create_widgets(self):
            header_frame = tk.Frame(self, bg="#0d47a1", height=70)
            header_frame.pack(fill=tk.X)
            title_lbl = tk.Label(
                header_frame, 
                text="RESOFTO ASTER ASSESSMENT UTILITY", 
                fg="white", bg="#0d47a1", font=("Helvetica", 14, "bold")
            )
            title_lbl.pack(pady=20)

            specs_lbl = tk.LabelFrame(self, text=" System Summary ", font=("Helvetica", 10, "bold"))
            specs_lbl.pack(fill=tk.X, padx=15, pady=8)

            self.lbl_pc = tk.Label(specs_lbl, text="Computer Name: ...", anchor="w")
            self.lbl_pc.pack(fill=tk.X, padx=10, pady=1)
            
            self.lbl_os = tk.Label(specs_lbl, text="OS Version: ...", anchor="w")
            self.lbl_os.pack(fill=tk.X, padx=10, pady=1)

            self.lbl_cpu = tk.Label(specs_lbl, text="Processor: ...", anchor="w")
            self.lbl_cpu.pack(fill=tk.X, padx=10, pady=1)

            self.lbl_ram = tk.Label(specs_lbl, text="RAM: ...", anchor="w")
            self.lbl_ram.pack(fill=tk.X, padx=10, pady=1)

            self.lbl_storage = tk.Label(specs_lbl, text="Storage: ...", anchor="w")
            self.lbl_storage.pack(fill=tk.X, padx=10, pady=1)

            self.lbl_gpu = tk.Label(specs_lbl, text="Graphics: ...", anchor="w")
            self.lbl_gpu.pack(fill=tk.X, padx=10, pady=1)

            results_lbl = tk.LabelFrame(self, text=" ASTER Readiness Score ", font=("Helvetica", 10, "bold"))
            results_lbl.pack(fill=tk.X, padx=15, pady=8)

            self.lbl_score = tk.Label(results_lbl, text="Readiness: --%", font=("Helvetica", 15, "bold"), fg="#1b5e20")
            self.lbl_score.pack(pady=2)

            self.lbl_stars = tk.Label(results_lbl, text="★ ★ ★ ★ ★", font=("Helvetica", 12), fg="#fbc02d")
            self.lbl_stars.pack(pady=1)

            self.lbl_status = tk.Label(results_lbl, text="Status: Evaluating...", font=("Helvetica", 11, "bold"))
            self.lbl_status.pack(pady=1)

            self.lbl_capacity = tk.Label(results_lbl, text="Recommended Config: --", font=("Helvetica", 10))
            self.lbl_capacity.pack(pady=1)

            rec_lbl = tk.LabelFrame(self, text=" Recommendations & ROI ", font=("Helvetica", 10, "bold"))
            rec_lbl.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

            self.txt_rec = tk.Text(rec_lbl, height=7, font=("Consolas", 9))
            self.txt_rec.pack(fill=tk.BOTH, padx=10, pady=5)

            btn_frame = tk.Frame(self)
            btn_frame.pack(fill=tk.X, padx=15, pady=8)

            ttk.Button(btn_frame, text="Re-Scan System", command=self.run_assessment).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Export PDF Report", command=self.export_report).pack(side=tk.RIGHT, padx=5)

        def run_assessment(self):
            self.data = HardwareCollector.collect_specs()
            self.results = AssessmentEngine.analyze(self.data)

            self.lbl_pc.config(text=f"Computer Name: {self.data['pc_name']} ({self.data['manufacturer']} {self.data['model']})")
            self.lbl_os.config(text=f"OS Version: {self.data['os']}")
            self.lbl_cpu.config(text=f"Processor: {self.data['cpu']} ({self.data['cores']} Cores)")
            self.lbl_ram.config(text=f"RAM: {self.data['ram_gb']} GB ({self.data['avail_ram_gb']} GB Free @ {self.data['ram_speed_mhz']} MHz)")
            self.lbl_storage.config(text=f"Storage: {self.data['storage_type']}")
            self.lbl_gpu.config(text=f"Graphics: {self.data['gpu']}")

            self.lbl_score.config(text=f"Compatibility Score: {self.results['score_pct']}%")
            self.lbl_stars.config(text=self.results['star_rating'])
            self.lbl_status.config(text=f"Status: {self.results['status']}")
            self.lbl_capacity.config(text=f"Recommended Configuration: 1 CPU = {self.results['capacity']} Users")

            self.txt_rec.delete("1.0", tk.END)
            self.txt_rec.insert(tk.END, f"ESTIMATED FINANCIAL SAVINGS (PER PC):\n")
            self.txt_rec.insert(tk.END, f" • Hardware Savings : ₹{self.results['hardware_saved_inr']:,}\n")
            self.txt_rec.insert(tk.END, f" • Power Reduction  : {self.results['elec_savings_pct']}%\n")
            self.txt_rec.insert(tk.END, f" • 5-Year Savings   : ₹{self.results['five_year_savings_inr']:,}\n\n")
            
            if self.results["recommendations"]:
                self.txt_rec.insert(tk.END, "ACTION ITEMS / PURCHASES:\n")
                for rec in self.results["recommendations"]:
                    self.txt_rec.insert(tk.END, f" [✓] {rec}\n")
            else:
                self.txt_rec.insert(tk.END, "ACTION ITEMS:\n [✓] Hardware is fully optimal for ASTER setup!\n")

            if self.results["alerts"]:
                self.txt_rec.insert(tk.END, "\nWARNINGS / ALERTS:\n")
                for alert in self.results["alerts"]:
                    self.txt_rec.insert(tk.END, f" [!] {alert}\n")

        def export_report(self):
            pdf_path = PDFReportGenerator.generate_pdf(self.data, self.results)
            messagebox.showinfo("Report Exported", f"Branded PDF Report saved to:\n{pdf_path}")

    app = RAAUApp()
    app.mainloop()