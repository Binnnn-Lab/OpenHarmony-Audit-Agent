"""Zip the portable recording page, narration and brief opening instructions."""
from pathlib import Path
import zipfile


def main():
    destination = Path(__file__).resolve().parents[1] / "deliverables"
    guide = """# 录屏材料

1. 解压后，双击 03-recording-demo.html，用 Chrome、Edge、Firefox 或 Safari 打开。
2. 双击 03-narration.html，在另一个窗口照读。绿色框是操作提示，正文是讲稿。
3. 录屏选择演示窗口，按讲稿点击按钮和翻页。第 4 页可直接点击 32 / 64 / 96。
4. 03-narration.md 是可编辑的讲稿原文。

演示 HTML 内含所有样式、图形、交互、环境说明和讲稿。只复制这个 HTML 到另一台电脑也能离线查看。
页面顶部“环境与操作”和“逐页讲稿”可打开内嵌内容。适用于 Windows、macOS、Linux 上的现代浏览器。
推荐 1920×1080 或 1440×900 录制，浏览器缩放 100%，按自己的语速点击。完整讲稿约 10–12 分钟。
"""
    with zipfile.ZipFile(destination / "03-recording-kit.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ["03-recording-demo.html", "03-narration.html", "03-narration.md"]:
            archive.write(destination / name, name)
        archive.writestr("README.md", guide)
    print("Packaged 03-recording-kit.zip")


if __name__ == "__main__":
    main()
