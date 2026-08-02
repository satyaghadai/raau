import sys
from raau.collector import HardwareCollector
from raau.analyzer import AssessmentEngine
from raau.pdf_generator import PDFReportGenerator

def run_quick_check():
    """Runs full assessment and generates PDF report."""
    print("==================================================")
    print("      RESOFTO ASTER ASSESSMENT UTILITY (RAAU)")
    print("==================================================")
    print("Running background diagnostics...\n")

    data = HardwareCollector.collect_specs()
    results = AssessmentEngine.analyze(data)

    print(f"  • Computer Name    : {data['pc_name']}")
    print(f"  • Windows Version  : {data['os']}")
    print(f"  • Processor        : {data['cpu']}")
    print(f"  • Installed RAM    : {data['ram_gb']} GB")
    print(f"  • Readiness Score  : {results['score_pct']}% ({results['star_rating']})")
    print(f"  • Overall Status   : {results['status']}")
    print(f"  • Config Capacity  : 1 CPU = {results['capacity']} Users")
    print(f"  • 5-Year Savings   : ₹{results['five_year_savings_inr']:,}")

    # Automatically generate PDF report
    pdf_file = PDFReportGenerator.generate_pdf(data, results)
    print(f"\n[✓] Professional PDF Report created: {pdf_file}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--check", "--cli", "-c"]:
        run_quick_check()
    else:
        from raau.gui import launch_gui
        launch_gui()