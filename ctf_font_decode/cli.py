from __future__ import annotations

import argparse
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from fontTools.ttLib import TTFont


GLYPH_NAME_TO_TEXT = {
    "space": " ",
    "exclam": "!",
    "quotedbl": '"',
    "numbersign": "#",
    "dollar": "$",
    "percent": "%",
    "ampersand": "&",
    "quotesingle": "'",
    "parenleft": "(",
    "parenright": ")",
    "asterisk": "*",
    "plus": "+",
    "comma": ",",
    "hyphen": "-",
    "minus": "-",
    "period": ".",
    "slash": "/",
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "colon": ":",
    "semicolon": ";",
    "less": "<",
    "equal": "=",
    "greater": ">",
    "question": "?",
    "at": "@",
    "bracketleft": "[",
    "backslash": "\\",
    "bracketright": "]",
    "asciicircum": "^",
    "underscore": "_",
    "grave": "`",
    "braceleft": "{",
    "bar": "|",
    "braceright": "}",
    "asciitilde": "~",
}

EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
)

VARIATION_SELECTOR_RANGES = (
    (0xFE00, 0xFE0F),
    (0xE0100, 0xE01EF),
)


@dataclass
class DecodedChar:
    char: str
    codepoint: int
    glyph_name: str
    decoded: str


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def load_font_path(font_arg: str) -> tuple[Path, NamedTemporaryFile | None]:
    if not is_url(font_arg):
        return Path(font_arg), None

    tmp = NamedTemporaryFile(delete=False, suffix=Path(font_arg).suffix or ".ttf")
    with urllib.request.urlopen(font_arg) as response:
        tmp.write(response.read())
    tmp.close()
    return Path(tmp.name), tmp


def read_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.text_file is not None:
        return Path(args.text_file).read_text(encoding="utf-8")
    data = sys.stdin.read()
    if data:
        return data
    raise SystemExit("Provide --text, --text-file, or stdin.")


def build_cmap(font: TTFont) -> dict[int, str]:
    cmap: dict[int, str] = {}
    for table in font["cmap"].tables:
        cmap.update(table.cmap)
    return cmap


def glyph_name_to_text(name: str | None) -> str | None:
    if not name:
        return None
    if name in GLYPH_NAME_TO_TEXT:
        return GLYPH_NAME_TO_TEXT[name]
    if len(name) == 1 and name.isprintable():
        return name
    if name.startswith("uni") and len(name) == 7:
        try:
            return chr(int(name[3:], 16))
        except ValueError:
            return None
    return None


def is_emoji(cp: int) -> bool:
    return any(start <= cp <= end for start, end in EMOJI_RANGES)


def is_variation_selector(cp: int) -> bool:
    return any(start <= cp <= end for start, end in VARIATION_SELECTOR_RANGES)


def should_consider(cp: int, mode: str) -> bool:
    if mode == "all":
        return True
    if mode == "non-ascii":
        return cp >= 0x80
    if mode == "emoji":
        return is_emoji(cp)
    if mode == "variation":
        return is_variation_selector(cp)
    raise ValueError(f"unknown mode: {mode}")


def decode_text(text: str, cmap: dict[int, str], mode: str) -> list[DecodedChar]:
    decoded: list[DecodedChar] = []
    for char in text:
        cp = ord(char)
        if not should_consider(cp, mode):
            continue
        glyph = cmap.get(cp)
        rendered = glyph_name_to_text(glyph)
        if rendered is None:
            continue
        decoded.append(DecodedChar(char, cp, glyph, rendered))
    return decoded


def unique_by_char(items: Iterable[DecodedChar]) -> list[DecodedChar]:
    seen: set[str] = set()
    unique: list[DecodedChar] = []
    for item in items:
        if item.char in seen:
            continue
        seen.add(item.char)
        unique.append(item)
    return unique


def font_name(font: TTFont, name_id: int) -> str:
    return font["name"].getDebugName(name_id) or "-"


def codepoint(cp: int) -> str:
    return f"U+{cp:04X}" if cp <= 0xFFFF else f"U+{cp:X}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="font-decode",
        description="Decode CTF text by reading readable glyph names from a font CMAP.",
    )
    parser.add_argument("--font", required=True, help="Path or URL to .ttf/.otf font.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Text to decode.")
    source.add_argument("--text-file", help="UTF-8 text file to decode.")
    parser.add_argument(
        "--only",
        choices=("emoji", "non-ascii", "variation", "all"),
        default="emoji",
        help="Which input characters to try decoding. Default: emoji.",
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Decode only the first occurrence of each character.",
    )
    parser.add_argument(
        "--mapping",
        action="store_true",
        help="Print per-character codepoint to glyph mapping.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    text = read_text(args)
    font_path, tmp = load_font_path(args.font)

    try:
        font = TTFont(str(font_path))
        cmap = build_cmap(font)
        decoded = decode_text(text, cmap, args.only)
        if args.unique:
            decoded = unique_by_char(decoded)

        output = "".join(item.decoded for item in decoded)

        print(f"Font family: {font_name(font, 1)}")
        print(f"Font full name: {font_name(font, 4)}")
        print(f"Decoded: {output}")

        if args.mapping:
            print()
            print("Mapping:")
            for item in decoded:
                print(f"{codepoint(item.codepoint)} -> {item.glyph_name} -> {item.decoded}")

        if not decoded:
            print("No readable CMAP glyph mappings found for the selected character filter.")
            return 2
        return 0
    finally:
        if tmp is not None:
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
