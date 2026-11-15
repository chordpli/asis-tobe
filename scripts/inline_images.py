#!/usr/bin/env python3
"""Puts every local image of the document inside the HTML file as a data URI, so the one file can be shared as it is.

    python3 -I inline_images.py DOC.html [--out OTHER.html]      # rewrites DOC.html in place unless --out is given

- Run it after the screenshots are final and before the gates (render_check, text_lint), so the gates check the file that is shared.
- <img src="..."> pointing at a file next to the document (relative path or file:// URL) is replaced by its base64 content.
  http(s) and existing data: sources are left alone. A missing file is an error: the document would show a broken image.
- Prints JSON: how many images went in, the size of the result, and any image over 1.5 MB (shrink those: capture at a smaller
  viewport or device scale; a document over about 15 MB is slow to open and may bounce off a mail or chat upload limit).
- The image folder is no longer needed by the HTML. Keep it only for the markdown edition (PR bodies need image files).
- Standard library only.
"""
import base64
import json
import mimetypes
import os
import re
import sys
from urllib.parse import unquote, urlparse

IMG = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])(.*?)\2', re.I | re.S)


def die(msg):
    sys.stderr.write(f'inline_images.py: {msg}\n')
    raise SystemExit(2)


def main(argv):
    args = [a for a in argv[1:] if a != '--out']
    out = None
    if '--out' in argv:
        k = argv.index('--out')
        if k + 1 >= len(argv):
            die('--out needs a path')
        out = argv[k + 1]
        args.remove(out)
    if len(args) != 1:
        die('usage: inline_images.py DOC.html [--out OTHER.html]')
    doc = args[0]
    base = os.path.dirname(os.path.abspath(doc))
    with open(doc, encoding='utf-8') as f:
        text = f.read()
    count, big, missing = 0, [], []

    def swap(m):
        nonlocal count
        src = m.group(3).strip()
        if not src or src.startswith(('data:', 'http://', 'https://', '//')) or '{{' in src:
            return m.group(0)
        path = unquote(urlparse(src).path) if src.startswith('file:') else unquote(src.split('#')[0].split('?')[0])
        if not os.path.isabs(path):
            path = os.path.join(base, path)
        if not os.path.isfile(path):
            missing.append(src)
            return m.group(0)
        kind = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) > 1_500_000:
            big.append({'src': src, 'bytes': len(data)})
        count += 1
        return f'{m.group(1)}{m.group(2)}data:{kind};base64,{base64.b64encode(data).decode("ascii")}{m.group(2)}'

    text = IMG.sub(swap, text)
    if missing:
        die('image file not found: ' + ', '.join(missing))
    with open(out or doc, 'w', encoding='utf-8') as f:
        f.write(text)
    print(json.dumps({'inlined': count, 'bytes': len(text.encode('utf-8')), 'big': big, 'out': os.path.abspath(out or doc)}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv)
