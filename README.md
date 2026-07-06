# ctf-font-decode

Small tool for Web CTF custom-font tricks.

## Background

Some CTF challenges hide text by abusing custom fonts instead of JavaScript or encryption. The HTML may contain emoji or weird Unicode characters, but the loaded font maps those characters to glyphs that look like normal letters.

Example:

```text
emoji emoji emoji emoji
```

may render as:

```text
v 1 t {
```

This project exists so you can quickly upload a suspicious font, paste the challenge text, and see the CMAP mapping without opening FontForge or manually inspecting every glyph.

## Status

This is still an early-stage tool. It currently focuses on simple CMAP-based tricks where glyph names are readable, such as `v`, `one`, `braceleft`, or `underscore`.

It does not brute force flags and it does not guess mappings. It only decodes mappings that are directly present in the font.

## How to Use

You can use this in two ways.

### Option 1: Simple Web UI

Open the web version:

[https://gokongggggggg.github.io/ctf-font-decode/](https://gokongggggggg.github.io/ctf-font-decode/)

Then:

1. Upload the suspicious `.ttf` / `.otf` font.
2. Paste the suspicious text from the challenge.
3. Click Decode.
4. Check the decoded output and mapping table.

### Option 2: CLI

Clone this repo and install it locally:

```powershell
git clone https://github.com/Gokongggggggg/ctf-font-decode.git
cd ctf-font-decode
pip install -e .
```

Then run:

```powershell
font-decode --font .\NotoSans-Regular.ttf --text-file .\payload.txt --only emoji --mapping
```

You can also run it without installing the console command:

```powershell
python -m ctf_font_decode.cli --font .\NotoSans-Regular.ttf --text-file .\embedded.srt --only emoji
```

Example output:

```text
Font: Emoji To AZ Regular
Decoded: v1t{g04t_mck_hvl}
```

## Current Limitations

- Best for `.ttf` / `.otf` fonts.
- Browser UI does not support `.woff` / `.woff2` yet.
- CMAP glyph-name decoding only.
- Advanced GSUB ligatures and visual OCR are not implemented yet.
