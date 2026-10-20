"""Create the captioned MP4 from capture_demo.cjs outputs.

Optional authoring dependencies: Pillow and imageio-ffmpeg. No audio is generated.
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default=r"C:\Windows\Fonts\msyh.ttc")
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    if args.ffmpeg:
        ffmpeg = args.ffmpeg
    else:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    root = Path(__file__).resolve().parents[1]
    folder = root / "tmp/video"
    frames = json.loads((folder / "frames.json").read_text(encoding="utf-8"))["frames"]
    font = ImageFont.truetype(args.font, 27)
    title_font = ImageFont.truetype(args.font, 19)
    concat, subtitles, timestamp = [], [], 0

    def timecode(seconds):
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02},000"

    for index, frame in enumerate(frames, 1):
        image = Image.new("RGB", (1440, 1080), "#08141a")
        image.paste(Image.open(folder / frame["file"]).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(image)
        draw.line((0, 900, 1440, 900), fill="#4a7566", width=2)
        draw.text((50, 916), f"{index:02} / {len(frames):02}   {frame['title']}", font=title_font, fill="#a9ddc6")
        line, lines = "", []
        for char in frame["caption"]:
            if draw.textlength(line + char, font=font) > 1330:
                lines.append(line)
                line = ""
            line += char
        lines.append(line)
        if len(lines) > 2:
            raise ValueError("Caption is too long for the dedicated band")
        for row, line in enumerate(lines):
            draw.text((50, 954 + row * 42), line, font=font, fill="#edf2e9")
        name = f"caption-{index:02}.png"
        image.save(folder / name)
        concat.extend([f"file '{name}'", f"duration {frame['duration']}"])
        subtitles.append(f"{index}\n{timecode(timestamp)} --> {timecode(timestamp+frame['duration'])}\n{frame['caption']}\n")
        timestamp += frame["duration"]
    concat.append(f"file 'caption-{len(frames):02}.png'")
    (folder / "concat.txt").write_text("\n".join(concat) + "\n", encoding="utf-8")
    destination = root / "deliverables"
    destination.mkdir(exist_ok=True)
    (destination / "03-demo-captioned.srt").write_text("\n".join(subtitles), encoding="utf-8")
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "warning", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(folder / "concat.txt"), "-t", str(timestamp), "-vf", "fps=15", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(destination / "03-demo-captioned.mp4")], check=True)
    print(f"Video: {timestamp} seconds, 1440 x 1080, 15 fps, captions, no audio.")


if __name__ == "__main__":
    main()
