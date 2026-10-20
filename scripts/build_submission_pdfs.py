"""Build all three competition manuals from their editable Markdown sources."""
from pathlib import Path
import argparse
import shutil

from openharmony_audit.reporting.pdf_report import build_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default=r"C:\Windows\Fonts\msyh.ttc")
    args = parser.parse_args()
    for source, name in [("docs/technical-report.md", "02-technical-manual"),
                         ("docs/user-manual.md", "03-user-manual"),
                         ("docs/performance.md", "05-performance")]:
        output = build_pdf(source, Path("deliverables") / (name + ".pdf"), args.font)
        print(output)
    shutil.copyfile("deliverables/02-technical-manual.pdf", "reports/technical-report.pdf")


if __name__ == "__main__":
    main()
