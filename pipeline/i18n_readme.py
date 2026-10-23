#!/usr/bin/env python3
"""Tłumaczy README.pl.md na README.md (angielski) lokalnym LLM (LM Studio / Ollama).

Dzieli plik na linie. Kod (ogrodzenia ```), puste linie i separatory zostają bez zmian.
Pozostałe linie: prefiks (nagłówek, element listy, cytat) zostaje, tekst idzie do LLM.
Kod w backtickach, URL-e i cele linków są zamieniane na tokeny @@n@@ i przywracane po tłumaczeniu.

Walidacja każdej linii: te same tokeny, te same liczby, identyfikatory (D23, R7b…),
brak polskich znaków, ta sama liczba '|' w wierszach tabeli. Błędna linia jest ponawiana,
a po ostatniej próbie zostaje po polsku i trafia na listę do ręcznej poprawki.

Pamięć tłumaczeń pipeline/i18n/memory.json jest kluczowana hashem tekstu polskiego linii,
więc ponowny run tłumaczy tylko zmienione linie.

Użycie (z katalogu repo):
  uv run python pipeline/i18n_readme.py                      # pełne tłumaczenie -> README.md
  uv run python pipeline/i18n_readme.py --sample 20 --out <plik>   # test: 20 linii porównawczo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "README.pl.md"
DST = ROOT / "README.md"
MEMORY = ROOT / "pipeline" / "i18n" / "memory.json"
GLOSSARY = ROOT / "pipeline" / "i18n" / "glossary.json"

SWITCH_PL = "[English](README.md) | **Polski**"
SWITCH_EN = "**English** | [Polski](README.pl.md)"

PREFIX_RE = re.compile(r"^(\s*(?:#{1,6}\s+|[-*+]\s+|\d+\.\s+|>\s?)*)")
MASK_RE = re.compile(r"`[^`]+`|(?<=\])\([^)]*\)|https?://\S+|<[^>]+>")
RAW_RE = re.compile(r"\s*(-{3,}|\*{3,}|<!--.*-->)\s*")
PLACEHOLDER_RE = re.compile(r"@@\d+@@")
NUM_RE = re.compile(r"\d+")
PL_CHARS_RE = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
IDENT_RE = re.compile(r"\b[A-ZŁŚŻ][A-Za-z]{0,3}\d+[a-z]?(?:-\d+)?\b")
LETTER_RE = re.compile(r"[^\W\d_]")


def load_glossary() -> dict:
    return json.loads(GLOSSARY.read_text(encoding="utf-8"))


def system_prompt(glossary: dict) -> str:
    terms = "; ".join(f"{pl} = {en}" for pl, en in glossary["terms"].items())
    keep = ", ".join(glossary["keep"])
    return (
        "You translate ONE line of a Polish technical README (a MATSim traffic "
        "simulation of Kutno, Poland) into English.\n"
        "Rules:\n"
        "1. Output ONLY the translated line. No quotes, no notes, no code fences.\n"
        "2. Keep every token @@N@@ exactly as written, once, in the same place.\n"
        "3. Keep numbers, identifiers (D23, R7b, K1-1, A1), file names and "
        f"these names unchanged: {keep}.\n"
        "4. Keep Markdown syntax unchanged (|, **, [ ], etc.). In table rows keep the "
        "same number of '|' characters.\n"
        f"5. Use these terms: {terms}.\n"
        "6. Plain, precise English, like a software manual."
    )


def call_llm(base_url: str, model: str, system: str, user: str,
             temperature: float, timeout: int) -> str:
    payload = {
        "model": model,
        "temperature": temperature,
        "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def mask(text: str) -> tuple[str, list[str]]:
    saved: list[str] = []

    def rep(m: re.Match) -> str:
        saved.append(m.group(0))
        return f"@@{len(saved) - 1}@@"

    return MASK_RE.sub(rep, text), saved


def unmask(text: str, saved: list[str]) -> str:
    return re.sub(r"@@(\d+)@@", lambda m: saved[int(m.group(1))], text)


def clean(out: str) -> str:
    out = out.strip()
    out = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", out).strip()
    return out


def problems(src: str, out: str, table: bool) -> list[str]:
    p = []
    if not out.strip():
        return ["pusty wynik"]
    if sorted(PLACEHOLDER_RE.findall(src)) != sorted(PLACEHOLDER_RE.findall(out)):
        p.append("tokeny @@n@@")
    if sorted(NUM_RE.findall(src)) != sorted(NUM_RE.findall(out)):
        p.append("liczby")
    if len(PL_CHARS_RE.findall(out)) > len(PL_CHARS_RE.findall(src)):
        p.append("polskie znaki")
    if table and src.count("|") != out.count("|"):
        p.append("liczba '|'")
    for tok in IDENT_RE.findall(src):
        if tok not in out:
            p.append(f"identyfikator {tok}")
    return p


def split_units(lines: list[str]) -> list[dict]:
    units: list[dict] = []
    in_code = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_code = not in_code
            units.append({"kind": "raw", "text": line})
            continue
        if in_code or not line.strip() or RAW_RE.fullmatch(line) or line.startswith(("<", "![")):
            units.append({"kind": "raw", "text": line})
            continue
        if line.strip() == SWITCH_PL:
            units.append({"kind": "raw", "text": SWITCH_EN})
            continue
        if line.startswith("|"):
            # Każda komórka osobno: model nie rusza liczby '|' i struktury tabeli.
            # "cont" = ta jednostka nie kończy linii (składane bez nowej linii).
            start = len(units)
            parts = line.split("|")
            for i, part in enumerate(parts):
                if i:
                    units.append({"kind": "raw", "text": "|"})
                units.append(text_unit(part, prefix=""))
            for u in units[start:-1]:
                u["cont"] = True
            continue
        prefix = PREFIX_RE.match(line).group(1)
        body = line[len(prefix):]
        if "#" in prefix:
            # Numer rozdziału (np. "5.1") zostaje przy nagłówku, model go gubi.
            num = re.match(r"\d+(?:\.\d+)*\.?\s+", body)
            if num:
                prefix += num.group(0)
                body = body[len(num.group(0)):]
        units.append(text_unit(body, prefix=prefix))
    return units


def text_unit(text: str, prefix: str) -> dict:
    """Jednostka do tłumaczenia; pusta albo bez liter zostaje bez zmian."""
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    core = text.strip()
    if not core:
        return {"kind": "raw", "text": prefix + text}
    masked, saved = mask(core)
    if not LETTER_RE.search(masked):
        return {"kind": "raw", "text": prefix + text}
    return {"kind": "tr", "prefix": prefix + lead, "body": core, "masked": masked,
            "saved": saved, "table": False, "en": None, "suffix": trail,
            "key": hashlib.sha256(core.encode("utf-8")).hexdigest()}


def translate_unit(u: dict, glossary: dict, args) -> str | None:
    system = system_prompt(glossary)
    last: list[str] = []
    for attempt in range(1, args.retries + 1):
        temp = 0.2 if attempt == 1 else 0.4
        try:
            out = clean(call_llm(args.base_url, args.model, system,
                                 u["masked"], temp, args.timeout))
        except Exception as e:  # noqa: BLE001
            last = [f"błąd połączenia: {e}"]
            time.sleep(2 * attempt)
            continue
        last = problems(u["masked"], out, u["table"])
        if not last:
            return unmask(out, u["saved"])
    print(f"  !! zostaje po polsku ({', '.join(last)}): {u['body'][:70]}", file=sys.stderr)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(DST))
    ap.add_argument("--model", default="gemma-4-e4b")
    ap.add_argument("--base-url", default="http://localhost:1234/v1")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--sample", type=int, default=0,
                    help="przetłumacz N równomiernie wybranych linii (test) i zapisz porównanie")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    glossary = load_glossary()
    mem: dict = json.loads(MEMORY.read_text(encoding="utf-8")) if MEMORY.exists() else {}
    lines = Path(args.src).read_text(encoding="utf-8").split("\n")
    units = split_units(lines)
    todo = []
    for u in (x for x in units if x["kind"] == "tr"):
        if u["key"] in mem:
            u["en"] = mem[u["key"]]["en"]
        else:
            todo.append(u)
    print(f"linii do tłumaczenia: {sum(1 for u in units if u['kind'] == 'tr')}, "
          f"z pamięci: {sum(1 for u in units if u.get('en') is not None)}, do przetłumaczenia: {len(todo)}")

    if args.sample:
        step = max(1, len(todo) // args.sample)
        todo = todo[::step][: args.sample]

    failed = []
    for n, u in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {u['body'][:60]}")
        en = translate_unit(u, glossary, args)
        if en is None:
            failed.append(u["body"])
            continue
        u["en"] = en
        if not args.sample:
            mem[u["key"]] = {"pl": u["body"], "en": en}
            MEMORY.parent.mkdir(parents=True, exist_ok=True)
            MEMORY.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.sample:
        pairs = [u for u in todo if u["en"]]
        out = ["# Test tłumaczenia (próbka)\n", "| PL | EN |", "|---|---|"]
        out += [f"| {u['body'].replace('|', '\\|')} | {u['en'].replace('|', '\\|')} |" for u in pairs]
        Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"porównanie zapisane: {args.out}")
    else:
        result, buf = [], ""
        for u in units:
            if u["kind"] == "raw":
                piece = u["text"]
            elif u["en"] is not None:
                piece = u["prefix"] + u["en"] + u["suffix"]
            else:
                piece = u["prefix"] + u["body"] + u["suffix"]
            buf += piece
            if not u.get("cont"):
                result.append(buf)
                buf = ""
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(result))
        print(f"zapisano: {args.out}")

    print(f"niepowodzenia (zostały po polsku): {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
