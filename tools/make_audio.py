"""Render recorded audio for every flashcard so it plays through CarPlay and Bluetooth.

Usage: python3 tools/make_audio.py path/to/en-us-lessac-medium.onnx [--jobs 4]

Needs `pip install piper-tts` and ffmpeg. The voice comes from
https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz

Each clip is named by a hash of the card text it reads (see fnv1a in index.html),
so editing questions.json and rerunning this only renders the cards that changed.
Clips no card uses any more are deleted. audio/index.json lists the clips that exist;
cards without a clip fall back to the browser's own voice.
"""
import json, os, re, subprocess, sys, tempfile, wave
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, "audio")


def fnv1a(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def question_text(q):
    return (q["case"] + " ... " if q.get("case") else "") + q["question"]


def speakable(t):
    # Same rewrites as speakable() in index.html, plus a few the browser voice handled itself.
    t = re.sub(r"(\d)\s*Gy\b", r"\1 gray", t)
    t = re.sub(r"\bGy\b", "gray", t)
    t = re.sub(r"(\d+(?:\.\d+)?) gray\s*/\s*(\d+)\s*(?:fx|fractions)?", r"\1 gray in \2 fractions", t, flags=re.I)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*/\s*(\d+)\s*(?:fx|fractions)\b", r"\1 in \2 fractions", t, flags=re.I)
    t = re.sub(r"\bfx\b", "fractions", t, flags=re.I)
    t = re.sub(r"\bcGy\b", "centigray", t)
    t = re.sub(r"\bcm\b", "centimeters", t)
    t = re.sub(r"\bmm\b", "millimeters", t)
    t = re.sub(r"(\d)\s*cc\b", r"\1 c c", t)
    t = re.sub(r"\bcc\b", "c c", t)
    t = re.sub(r"\byo\b", "year old", t, flags=re.I)
    t = re.sub(r"(\d)\s*([MF])\b", lambda m: m.group(1) + (" year old man" if m.group(2) == "M" else " year old woman"), t)
    t = t.replace("≥", " at least ").replace("≤", " at most ").replace("~", "about ")
    t = t.replace("→", " then ").replace("->", " then ").replace("+/-", " with or without ")
    t = re.sub(r"\s*mg\s*/\s*m(2|²)", " milligrams per meter squared", t)
    t = t.replace("<", " less than ").replace(">", " more than ")
    t = t.replace("%", " percent").replace("&", " and ")
    return re.sub(r"\s+", " ", t).strip()


VOICE = None


def render(job):
    global VOICE
    model, text, out = job
    if VOICE is None:
        from piper import PiperVoice
        VOICE = PiperVoice.load(model)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            VOICE.synthesize_wav(speakable(text), w)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-ac", "1", "-b:a", "40k", out], check=True)
    return out


def main():
    model = sys.argv[1]
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else os.cpu_count()
    bank = json.load(open(os.path.join(ROOT, "questions.json")))
    os.makedirs(AUDIO, exist_ok=True)
    wanted = {}
    for q in bank:
        for text in (question_text(q), q["answer"]):
            wanted[fnv1a(text)] = text
    todo = [(model, t, os.path.join(AUDIO, h + ".mp3")) for h, t in wanted.items()
            if not os.path.exists(os.path.join(AUDIO, h + ".mp3"))]
    print(f"{len(wanted)} clips needed, {len(todo)} to render")
    with ProcessPoolExecutor(jobs) as pool:
        for i, _ in enumerate(pool.map(render, todo), 1):
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)
    for f in os.listdir(AUDIO):
        if f.endswith(".mp3") and f[:-4] not in wanted:
            os.remove(os.path.join(AUDIO, f))
    have = sorted(f[:-4] for f in os.listdir(AUDIO) if f.endswith(".mp3"))
    json.dump(have, open(os.path.join(AUDIO, "index.json"), "w"))
    print(f"done: {len(have)} clips")


if __name__ == "__main__":
    main()
