#!/usr/bin/env python3
"""Finds the changed regions between two screenshots and prints box coordinates (% of each image) as JSON.

    python3 -I diff_boxes.py ASIS.png TOBE.png [--cell 8] [--pad 6] [--min-area 64] [--threshold 24]

Output: {"same": bool, "size": {...}, "shifted": bool, "asis": [{"x","y","w","h"}...], "tobe": [...]}
  Values are % of each image (two decimal places). asis is the spot before something vanished or changed; tobe is the spot after something appeared or changed.
- Dependencies: standard library + numpy. Reads only 8-bit RGB/RGBA/Gray, non-interlaced PNG (the shape headless Chrome captures produce).
- Aligns row by row to separate inserted blocks (TO-BE only), removed blocks (AS-IS only), and changed blocks (both sides). When a block is inserted and pushes the rest down, the shifted part is not counted as a change.
- "anchored": true means a bottom-anchored layout, so the upper part shifted as a whole. Removal boxes caused by the shift are dropped from the output, but insertion boxes can be off by more than half a line at row boundaries, so adjust them by hand against the screenshot.
- Inserted bands are narrowed to the rows and columns with content, excluding vertical borders, but if a card's background color differs from the screen background, the whole card is captured. Eyeball insertion boxes once in the rendered image.
- Widths must be equal. If the boxes cover more than half the screen, "shifted": true, and then choose boxes by hand.
"""
import json
import struct
import sys
import zlib

import numpy as np


def read_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit(f'{path}: not a PNG')
    pos, idat, meta = 8, [], None
    while pos < len(data):
        (length,) = struct.unpack('>I', data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
            if depth != 8 or interlace:
                raise SystemExit(f'{path}: only 8-bit non-interlaced PNG is supported')
            channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
            if channels is None:
                raise SystemExit(f'{path}: palette PNG is not supported')
            meta = (w, h, channels)
        elif kind == b'IDAT':
            idat.append(body)
        elif kind == b'IEND':
            break
    w, h, ch = meta
    raw = zlib.decompress(b''.join(idat))
    stride = w * ch
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    i = 0
    for y in range(h):
        ftype = raw[i]
        line = np.frombuffer(raw, dtype=np.uint8, count=stride, offset=i + 1).astype(np.int32)
        i += 1 + stride
        if ftype == 0:
            cur = line
        elif ftype == 2:
            cur = (line + prev) & 0xFF
        elif ftype in (1, 3, 4):
            cur = np.zeros(stride, dtype=np.int32)
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0
                b = prev[x]
                if ftype == 1:
                    p = a
                elif ftype == 3:
                    p = (a + b) >> 1
                else:
                    c = prev[x - ch] if x >= ch else 0
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    p = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                cur[x] = (line[x] + p) & 0xFF
        else:
            raise SystemExit(f'{path}: unknown filter {ftype}')
        out[y] = cur
        prev = cur
    img = out.reshape(h, w, ch)[:, :, :3] if ch >= 3 else np.repeat(out.reshape(h, w, 1), 3, axis=2)
    return img.astype(np.int16)


def boxes_from_mask(mask, cell, pad, min_area):
    h, w = mask.shape
    gh, gw = -(-h // cell), -(-w // cell)
    grid = np.zeros((gh, gw), dtype=bool)
    ys, xs = np.nonzero(mask)
    grid[ys // cell, xs // cell] = True
    # Grow by one neighboring cell so nearby changes merge into one box
    grown = grid.copy()
    grown[1:, :] |= grid[:-1, :]
    grown[:-1, :] |= grid[1:, :]
    grown[:, 1:] |= grid[:, :-1]
    grown[:, :-1] |= grid[:, 1:]
    seen = np.zeros_like(grown)
    boxes = []
    for gy in range(gh):
        for gx in range(gw):
            if not grown[gy, gx] or seen[gy, gx]:
                continue
            stack, cells = [(gy, gx)], []
            seen[gy, gx] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < gh and 0 <= nx < gw and grown[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            cy0 = min(c[0] for c in cells); cy1 = max(c[0] for c in cells) + 1
            cx0 = min(c[1] for c in cells); cx1 = max(c[1] for c in cells) + 1
            sub = mask[cy0 * cell:cy1 * cell, cx0 * cell:cx1 * cell]
            sy, sx = np.nonzero(sub)
            if sy.size == 0:
                continue
            y0 = cy0 * cell + sy.min(); y1 = cy0 * cell + sy.max() + 1
            x0 = cx0 * cell + sx.min(); x1 = cx0 * cell + sx.max() + 1
            if (y1 - y0) * (x1 - x0) < min_area:
                continue
            boxes.append((int(max(0, x0 - pad)), int(max(0, y0 - pad)), int(min(w, x1 + pad)), int(min(h, y1 + pad))))
    return boxes


def background(img):
    flat = img.reshape(-1, 3)
    vals, counts = np.unique(flat[:: max(1, flat.shape[0] // 20000)], axis=0, return_counts=True)
    return vals[counts.argmax()]


def to_pct(box, W, H):
    x0, y0, x1, y1 = box
    return {'x': round(x0 / W * 100, 2), 'y': round(y0 / H * 100, 2),
            'w': round((x1 - x0) / W * 100, 2), 'h': round((y1 - y0) / H * 100, 2)}


def main(argv):
    args, opts = [], {'--cell': 8, '--pad': 6, '--min-area': 64, '--threshold': 24}
    it = iter(argv)
    for a in it:
        if a in opts:
            opts[a] = int(next(it))
        else:
            args.append(a)
    if len(args) != 2:
        raise SystemExit(__doc__)
    a, b = read_png(args[0]), read_png(args[1])
    if a.shape[1] != b.shape[1]:
        raise SystemExit('Widths differ. Recapture at the same viewport')
    W, pad, thr = a.shape[1], opts['--pad'], opts['--threshold']
    bg = background(a)
    # Align by rows to separate inserted and removed blocks first, so the shifted lower part is not caught as a change
    from difflib import SequenceMatcher
    ra = [row.tobytes() for row in a.astype(np.uint8)]
    rb = [row.tobytes() for row in b.astype(np.uint8)]
    ops = SequenceMatcher(None, ra, rb, autojunk=False).get_opcodes()
    asis, tobe = [], []

    def band_box(img, y0, y1):
        # An inserted band mixes in vertical lines running top to bottom, like card borders, and empty margin rows.
        # Columns spanning 90% or more of the band's rows are treated as vertical lines and removed; narrow to the remaining rows and columns with content
        band = np.abs(img[y0:y1] - bg).max(axis=2) > thr
        if band.shape[0] >= 4:
            band[:, band.mean(axis=0) >= 0.9] = False
        rows = np.nonzero(band.any(axis=1))[0]
        cols = np.nonzero(band.any(axis=0))[0]
        if rows.size == 0 or cols.size == 0:
            return None
        ty0, ty1 = y0 + int(rows.min()), y0 + int(rows.max()) + 1
        return (max(0, int(cols.min()) - pad), max(0, ty0 - pad), min(W, int(cols.max()) + 1 + pad), min(img.shape[0], ty1 + pad))

    def best_window(rows, img, y0, y1):
        # When empty rows repeat, the same insertion can also match positions shifted up or down.
        # Check every position where sliding the band by rows keeps the outside identical, and pick the one with the smallest content height
        n, cands = y1 - y0, [(y0, y1)]
        s = y0
        while s > 0 and rows[s - 1] == rows[s - 1 + n]:
            s -= 1; cands.append((s, s + n))
        s = y0
        while s + n < len(rows) and rows[s] == rows[s + n]:
            s += 1; cands.append((s, s + n))
        def height(c):
            box = band_box(img, *c)
            return box[3] - box[1] if box else 0
        return min(cands, key=height)

    for tag, i0, i1, j0, j1 in ops:
        if tag == 'equal':
            continue
        if tag == 'replace' and (i1 - i0) == (j1 - j0):
            diff = np.abs(a[i0:i1] - b[j0:j1]).max(axis=2) > thr
            for x0, y0, x1, y1 in boxes_from_mask(diff, opts['--cell'], pad, opts['--min-area']):
                asis.append((x0, i0 + y0, x1, i0 + y1))
                tobe.append((x0, j0 + y0, x1, j0 + y1))
            continue
        if i1 > i0 and j1 == j0:
            i0, i1 = best_window(ra, a, i0, i1)
        if j1 > j0 and i1 == i0:
            j0, j1 = best_window(rb, b, j0, j1)
        if i1 > i0:
            box = band_box(a, i0, i1)
            if box and (box[2] - box[0]) * (box[3] - box[1]) >= opts['--min-area']:
                asis.append(box)
        if j1 > j0:
            box = band_box(b, j0, j1)
            if box and (box[2] - box[0]) * (box[3] - box[1]) >= opts['--min-area']:
                tobe.append(box)
    # On bottom-anchored screens (chat dock, bottom sheet), new rows push the whole upper part up.
    # That yields a removal and an insertion of the same length together, and the insertion boundary can fall mid-row
    dels = {i1 - i0 for t, i0, i1, j0, j1 in ops if t == 'delete'}
    anchored = any(t == 'insert' and (j1 - j0) in dels for t, i0, i1, j0, j1 in ops)
    if anchored:
        asis = [x for x in asis if not any(t == 'delete' and x[1] <= i0 + pad and x[3] >= i1 - pad
                                           for t, i0, i1, j0, j1 in ops)]
    pa = [to_pct(x, W, a.shape[0]) for x in asis]
    pb = [to_pct(x, W, b.shape[0]) for x in tobe]
    covered = max(sum(p['w'] * p['h'] for p in pa), sum(p['w'] * p['h'] for p in pb)) / 100
    print(json.dumps({
        'same': not pa and not pb,
        'size': {'asis': [int(a.shape[1]), int(a.shape[0])], 'tobe': [int(b.shape[1]), int(b.shape[0])]},
        'shifted': bool(covered > 50),
        'anchored': anchored,
        'asis': pa,
        'tobe': pb,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1:])
