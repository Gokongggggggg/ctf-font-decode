# ctf-font-decode

Small CLI for Web CTF font tricks. It reads a TTF/OTF font CMAP and decodes suspicious text when Unicode characters map to readable glyph names such as `v`, `one`, `braceleft`, or `underscore`.

## Usage

```powershell
python -m ctf_font_decode.cli --font .\NotoSans-Regular.ttf --text "😀😃😄😁😆😅😂🤣🥲😊😇🙂🥲🙃😉😌😍"
```

Or from a file:

```powershell
python -m ctf_font_decode.cli --font .\NotoSans-Regular.ttf --text-file .\embedded.srt --only emoji
```

Example output:

```text
Font: Emoji To AZ Regular
Decoded: v1t{g04t_mck_hvl}
```

This tool does not brute force. It only decodes mappings that are directly present in the font.

## Simple Frontend

Open [web/index.html](web/index.html) in a browser. Upload a font, paste text, then click Decode.
