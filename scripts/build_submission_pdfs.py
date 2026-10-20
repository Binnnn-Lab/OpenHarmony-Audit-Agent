"""Build all three competition manuals from their editable Markdown sources."""
from pathlib import Path
import argparse
import shutil

from openharmony_audit.reporting.pdf_report import build_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default=r"C:\Windows\Fonts\msyh.ttc")
    args = parser.parse_args()
    for source, name in [("docs/technical-report.md", "工具源代码技术说明书"),
                         ("docs/user-manual.md", "工具使用说明书"),
                         ("docs/performance.md", "工具性能说明")]:
        output = build_pdf(source, Path("deliverables") / (name + ".pdf"), args.font)
        print(output)
    shutil.copyfile("deliverables/工具源代码技术说明书.pdf", "reports/technical-report.pdf")


if __name__ == "__main__":
    main()
