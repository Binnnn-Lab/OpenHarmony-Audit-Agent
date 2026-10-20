"""Package the silent video with matching voiceover and source attribution."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"deliverables"
FILES=["03-operation-demo.mp4","03-operation-voiceover.html","03-operation-voiceover.md",
       "03-operation-voiceover.srt","03-operation-replay.html"]


def main():
    manifest=[]
    with zipfile.ZipFile(DEST/"03-operation-video-kit.zip","w",zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            data=(DEST/name).read_bytes()
            z.writestr(name,data)
            manifest.append({"file":name,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
        z.write(ROOT/"docs/operation-video.md","README.md")
        z.write(ROOT/"reports/operation-demo/SOURCE-LICENSE.txt","SOURCE-LICENSE.txt")
        for p in sorted((ROOT/"reports/operation-demo").glob("*")):
            if p.is_file():z.write(p,"run-records/"+p.name)
        z.writestr("MANIFEST.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print("Packaged video, timed voiceover, replay and run records")


if __name__=="__main__":main()
