"""G6: film + lektor + muzyka syntezowana w kodzie (jak score.js w gisboost-filmy, ale numpy), muzyka -20 dB (LUFS) wzgledem glosu.

Uzycie: uv run python pipeline/g6_mix.py --video story_v7.mp4 --voice "New tts node.mp3" --out story_v7_lektor.mp4 [--db -20]
Krok po kroku: (1) glosnosc lektora w LUFS, (2) synteza muzyki na dlugosc filmu, (3) muzyka = LUFS lektora + db, (4) miks ffmpeg.
Gdy lektor jest dluzszy niz film, ostatnia klatka jest przedluzana (tpad) i obraz kodowany ponownie; inaczej strumien wideo jest kopiowany.
"""
import argparse, re, subprocess, wave, tempfile, os
from pathlib import Path
import numpy as np

SR = 44100
BEAT = 60 / 76  # wolno, spokojnie, nie konkuruje z mowa
NOTE = {n: i for i, n in enumerate("C Cs D Ds E F Fs G Gs A As B".split())}
def hz(n):  # np. 'Fs4'
    m = re.fullmatch(r"([A-G]s?)(\d)", n); return 440 * 2 ** ((NOTE[m[1]] + 12 * (int(m[2]) + 1) - 69) / 12)

# D-dur, powolna progresja: Dmaj7 - Bm7 - Gmaj7 - A(sus) ; co 4 takty
CHORDS = [["D3", "A3", "Cs4", "Fs4"], ["B2", "Fs3", "A3", "D4"], ["G2", "D3", "Fs3", "B3"], ["A2", "E3", "A3", "Cs4"]]
SCALE = ["D4", "E4", "Fs4", "A4", "B4", "D5", "E5", "Fs5"]  # pentatonika D

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def lufs(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])

def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout)

def synth(D, seed=7):
    rng = np.random.default_rng(seed)
    n = int(D * SR); t = np.arange(n) / SR; out = np.zeros((2, n))
    def env(t0, t1, att, rel):
        e = np.clip((t - t0) / att, 0, 1) * np.clip((t1 - t) / rel, 0, 1); return e * e * (3 - 2 * e)
    clen = 4 * 4 * BEAT  # akord = 4 takty 4/4
    k = 0
    while k * clen < D:
        t0, t1 = k * clen, (k + 1) * clen; ch = CHORDS[k % 4]
        for j, nn in enumerate(ch):
            f = hz(nn); e = env(t0 - 2, t1 + 2, 2.5, 2.5)
            for d in (-0.15, 0, 0.15):  # lekki detune = chorus
                v = 0.5 * np.sin(2 * np.pi * f * 2 ** (d / 12) * t) + 0.12 * np.sin(2 * np.pi * 2 * f * t)
                out[j % 2] += 0.02 * e * v; out[(j + 1) % 2] += 0.014 * e * v
        f = hz(ch[0]) / 2  # bas: jeden dlugi dzwiek na akord
        out += (0.05 * env(t0, t1, 0.6, 1.5) * np.sin(2 * np.pi * f * t))[None]
        k += 1
    # rzadkie piorka: ~jedna nuta na takt, losowa pauza, tylko tony akordu/pentatoniki
    b = 2 * BEAT
    while b < D - 3:
        if rng.random() < 0.65:
            f = hz(rng.choice(SCALE)); m = t >= b; tt = (t - b) * m
            p = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt)
            p = p * m * np.exp(-tt / 0.9) * np.clip(tt / 0.005, 0, 1)
            pan = rng.uniform(0.2, 0.8); out[0] += 0.05 * (1 - pan) * p; out[1] += 0.05 * pan * p
        b += rng.choice([1, 2, 2, 3]) * BEAT
    # pogłos jako ping-pong delay z tlumieniem
    wet = np.zeros_like(out); d = int(0.43 * SR)
    for i in range(1, 7):
        s = i * d; g = 0.38 ** i
        if s < n: wet[i % 2, s:] += g * out[0, :n - s]; wet[(i + 1) % 2, s:] += g * out[1, :n - s]
    out += 0.7 * wet
    out *= np.clip(t / 2.0, 0, 1) * np.clip((D - t) / 3.0, 0, 1)  # fade in 2 s, fade out 3 s
    out /= max(1e-9, np.abs(out).max()) / 0.8
    return (out.T * 32767).astype(np.int16)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--voice", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--db", type=float, default=-20.0, help="muzyka wzgledem glosu [LUFS]")
    ap.add_argument("--voice-lufs", type=float, default=-16.0, help="docelowa glosnosc lektora [LUFS], 0 = bez zmian")
    ap.add_argument("--tail", type=float, default=1.0, help="cisza po ostatnim slowie [s]")
    a = ap.parse_args()
    vd, ad = dur(a.video), dur(a.voice); D = max(vd, ad + a.tail)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "music.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(synth(D).tobytes())
        lv, lm = lufs(a.voice), lufs(wav); vg = (a.voice_lufs - lv) if a.voice_lufs else 0.0; gain = lv + vg + a.db - lm
        print(f"film {vd:.2f} s, lektor {ad:.2f} s ({lv:.1f} LUFS), muzyka {lm:.1f} LUFS -> gain lektora {vg:+.1f} dB, muzyki {gain:+.1f} dB, wynik {D:.2f} s")
        vf = ["-vf", f"tpad=stop_mode=clone:stop_duration={D - vd:.3f}", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p"] if D - vd > 0.05 else ["-c:v", "copy"]
        fc = f"[1:a]aresample={SR},volume={vg:.2f}dB,apad,atrim=0:{D:.3f}[v];[2:a]volume={gain:.2f}dB[m];[v][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]"
        run(["ffmpeg", "-y", "-i", a.video, "-i", a.voice, "-i", str(wav), "-filter_complex", fc, "-map", "0:v", "-map", "[a]", *vf,
             "-c:a", "aac", "-b:a", "256k", "-t", f"{D:.3f}", "-movflags", "+faststart", a.out])
    print("zapisano", a.out)

if __name__ == "__main__":
    main()
