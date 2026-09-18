"""Simple Czech substitution / Caesar ciphers for families."""

from __future__ import annotations

from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase

MESSAGES = [
    "AHOJ KAMARÁDI",
    "ČAS NA HRU",
    "MILUJEME KNIHY",
    "SVĚT JE KRÁSNÝ",
    "POJĎME VEN",
    "DOBRÉ RÁNO",
    "ŠŤASTNÝ DEN",
    "MALÝ DETEKTIV",
]

SYMBOLS = list("★◆●▲■♠♣♥♦○△□♤♧♡♢✦✧")


def caesar(text: str, shift: int) -> str:
    alphabet = "AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPRŘSŠTŤUÚŮVXYÝZŽ"
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        up = ch.upper()
        if up not in alphabet:
            out.append(ch)
            continue
        i = alphabet.index(up)
        out.append(alphabet[(i + shift) % len(alphabet)])
    return "".join(out)


def symbol_sub(text: str, rng) -> tuple[str, dict[str, str]]:
    letters = sorted({c for c in text.upper() if c.isalpha() or c in "ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"})
    pool = SYMBOLS[:]
    rng.shuffle(pool)
    mapping = {lett: pool[i] for i, lett in enumerate(letters)}
    encoded = "".join(mapping.get(c, c) for c in text.upper())
    return encoded, mapping


@register
class CipherGenerator(GameGenerator):
    kind = "cipher"

    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        params = params or {}
        rng = make_rng(seed)
        plain = params.get("message") or rng.choice(MESSAGES)
        mode = params.get("mode") or (
            "caesar" if difficulty == Difficulty.easy else "symbols"
        )
        if mode == "caesar":
            shift = int(params.get("shift") or rng.randint(1, 5))
            encoded = caesar(plain, shift)
            hint = f"Každé písmeno je posunuté o {shift} v abecedě (A→…)."
            answer = {"plaintext": plain, "mode": "caesar", "shift": shift}
            data = {"mode": "caesar", "ciphertext": encoded, "shift": shift, "hint": hint}
        else:
            encoded, mapping = symbol_sub(plain, rng)
            # Provide a few free letters as crib
            crib_letters = sorted(mapping.keys())[:3]
            crib = {lett: mapping[lett] for lett in crib_letters}
            hint = "Některé symboly už znáš — doplň zbytek abecedy."
            answer = {
                "plaintext": plain,
                "mode": "symbols",
                "mapping": {v: k for k, v in mapping.items()},
            }
            data = {
                "mode": "symbols",
                "ciphertext": encoded,
                "crib": crib,
                "hint": hint,
            }
        if answer["plaintext"].upper() != plain.upper():
            raise ValueError("Cipher answer mismatch")
        return PuzzleBase(
            kind=self.kind,
            title=title or "Šifra",
            instructions=data["hint"] + " Napiš vyluštěnou větu pod šifru.",
            difficulty=difficulty,
            seed=seed,
            data=data,
            answer=answer,
        )
