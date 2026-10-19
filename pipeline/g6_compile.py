"""G6: skleja filmy (bez renderu) w jeden, lektor glowny od 0 s + opcjonalna dogrywka, muzyka -20 LUFS wzgledem lektora.
Uzycie: uv run python pipeline/g6_compile.py --out x.mp4 --voice v7.mp3 [--voice2 outro.mp3] film1.mp4 film2.mp4 ...
Filmy sa skalowane do 1920x1080 / 30 fps (letterbox). Muzyka i lektor jak w g6_mix.py."""
import argparse, subprocess, tempfile, wave
from pathlib import Path
from g6_mix import SR, synth, lufs, dur, run

ap = argparse.ArgumentParser()
ap.add_argument("videos", nargs="+"); ap.add_argument("--out", required=True); ap.add_argument("--voice", required=True)
ap.add_argument("--voice2"); ap.add_argument("--gap", type=float, default=1.5, help="przerwa miedzy lektorami [s]")
ap.add_argument("--db", type=float, default=-20.0); ap.add_argument("--voice-lufs", type=float, default=-16.0)
a = ap.parse_args()
D = sum(dur(v) for v in a.videos); n = len(a.videos); v1 = dur(a.voice)
t2 = v1 + a.gap
with tempfile.TemporaryDirectory() as tmp:
    wav = Path(tmp) / "m.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(synth(D).tobytes())
    lm = lufs(wav); lv = lufs(a.voice); vg = a.voice_lufs - lv; gain = a.voice_lufs + a.db - lm  # lektor 2 normalizowany do tego samego celu
    ins = [x for v in a.videos for x in ("-i", v)] + ["-i", a.voice, "-i", str(wav)]
    vi, mi = n, n + 1
    fc = "".join(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}];" for i in range(n))
    fc += "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vid];"
    fc += f"[{vi}:a]aresample={SR},volume={vg:.2f}dB[a1];"
    if a.voice2:
        ins += ["-i", a.voice2]; v2 = n + 2; vg2 = a.voice_lufs - lufs(a.voice2)
        fc += f"[{v2}:a]aresample={SR},volume={vg2:.2f}dB,adelay={int(t2*1000)}:all=1[a2];[a1][a2]amix=inputs=2:normalize=0[vo];"
    else:
        fc += "[a1]anull[vo];"
    fc += f"[vo]apad,atrim=0:{D:.3f}[v];[{mi}:a]volume={gain:.2f}dB[m];[v][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]"
    print(f"{n} filmow, {D:.1f} s, lektor {v1:.1f} s, dogrywka od {t2:.1f} s" if a.voice2 else f"{n} filmow, {D:.1f} s, lektor {v1:.1f} s, bez dogrywki")
    run(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-map", "[vid]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-t", f"{D:.3f}", "-movflags", "+faststart", a.out])
print("zapisano", a.out)
