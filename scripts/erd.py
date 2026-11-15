#!/usr/bin/env python3
"""Draws the AS-IS and TO-BE entity diagrams of the Data layer as inline SVG and prints an HTML fragment.

    python3 -I erd.py spec.json [--lang ko|en] > erd.html     # paste the output under the Data section's .lead

spec.json:
{
  "asis": {                                # null (or omitted) when AS-IS had no stored schema
    "entities": [
      {"name": "todos", "fields": [
        {"name": "id", "type": "TEXT", "key": "pk"},          # key: "pk" | "fk" | "uk", or several joined: "pk,fk"
        {"name": "title", "type": "TEXT"},
        {"name": "note", "type": "TEXT", "null": true}        # null: true marks a nullable field with "?"
      ]}
    ],
    "relations": [{"from": "reminders.todo_id", "to": "todos.id", "card": "N:1"}]   # child field -> parent field; card "N:1" (default) or "1:1"
  },
  "tobe": { ... same shape ... },
  "asis_note": "메모리에만 있었다 (src/infrastructure/memory.rs:12)"                 # shown instead of a diagram when a side is null
}

- Only the changed entities and the ones directly attached to them go in. More than 6 entities on a side: the script exits with an error; use the table.
- The script compares the two sides by entity and field name and marks: + added, − removed, ~ changed (type, key, or nullability).
  A renamed field is a removal plus an addition; say it is a rename in the field table.
- When one side is null, every entity on the other side is marked new (or removed).
- Both sides are laid out on one grid computed from both: parents left, children right, the same column positions and widths.
  An entity that exists on both sides sits in the same column on both; a column that is empty on one side stays empty there.
- A diagram wider than half the page makes the pair stack (AS-IS above TO-BE, class "wide") so nothing hides behind a scrollbar.
  Each side is drawn twice: the grid layout, and a one-column layout (entities stacked, lines down the right side) that the
  template shows instead on screens narrower than 760px, so nothing has to be scrolled sideways on a phone.
- Relations anchor field to field. The forked end is the "many" side. Lines that cannot go straight to the next column run under the boxes.
- Colours and fonts come from the template's CSS (.erd rules); the SVG carries classes only. Standard library only.
"""
import html
import json
import sys

ROW, HEAD, PAD, VGAP = 22, 30, 16, 24
CHAR = 7.3            # width of one monospace character at 12px
STR = {
    'ko': {'new': '신설', 'gone': '삭제', 'none': '실물 없음', 'key': '<b>+</b> 추가, <b>−</b> 삭제, <b>~</b> 변경. 선은 필드와 필드를 잇고, 갈라진 쪽이 여러 행이다.',
           'title': '{side} 엔티티 관계도', 'desc': '엔티티 {n}개, 관계 {r}개.'},
    'en': {'new': 'new', 'gone': 'removed', 'none': 'No real artifact', 'key': '<b>+</b> added, <b>−</b> removed, <b>~</b> changed. Lines join field to field; the forked end is the many side.',
           'title': '{side} entity diagram', 'desc': '{n} entities, {r} relations.'},
}


def die(msg):
    sys.stderr.write(f'erd.py: {msg}\n')
    raise SystemExit(2)


def width(text):
    return sum(2 if ord(c) > 0x2E7F else 1 for c in text)


def index(side):
    """{'entity': {'field': fielddict}} for one side (None -> {})."""
    out = {}
    for e in (side or {}).get('entities', []):
        out[e['name']] = {f['name']: f for f in e.get('fields', [])}
    return out


def keys(f):
    return [k.strip().upper() for k in str(f.get('key') or '').split(',') if k.strip()]


def sig(f):
    return (f.get('type', ''), tuple(keys(f)), bool(f.get('null')))


def ent(r, end):
    return r[end].split('.')[0]


def grid(spec):
    """One layout grid for both sides: column per entity, column x positions, box width."""
    names, parents, sides = [], {}, [spec.get('asis') or {}, spec.get('tobe') or {}]
    for s in sides:
        for e in s.get('entities', []):
            if e['name'] not in names:
                names.append(e['name'])
        for r in s.get('relations', []):
            if ent(r, 'from') != ent(r, 'to'):
                parents.setdefault(ent(r, 'from'), set()).add(ent(r, 'to'))
    depth = {}

    def walk(n, seen):
        if n in depth:
            return depth[n]
        if n in seen:
            return 0
        d = 0
        for p in parents.get(n, ()):
            if p in names:
                d = max(d, walk(p, seen | {n}) + 1)
        depth[n] = d
        return d

    for n in names:
        walk(n, frozenset())

    allf = [(e, f) for s in sides for e in s.get('entities', []) for f in e.get('fields', [])]
    multi = any(len(keys(f)) > 1 for _, f in allf)
    name_x = 60 if multi else 44                       # where the field name starts: after the change mark and the key tags
    longest = max([width(e['name']) + 8 for s in sides for e in s.get('entities', [])] +
                  [width(f['name']) + width(f.get('type', '')) + 3 for _, f in allf] + [18])
    box_w = int(min(360, max(196, name_x + longest * CHAR + 14)) // 4 * 4)

    cols = sorted(set(depth.values()))
    entering, selfcols, back = {c: 0 for c in cols}, set(), 0
    for s in sides:
        n = {c: 0 for c in cols}
        b = 0
        for r in s.get('relations', []):
            if ent(r, 'from') == ent(r, 'to'):
                selfcols.add(depth[ent(r, 'from')])
                continue
            n[depth[ent(r, 'from')]] += 1
            if cols.index(depth[ent(r, 'from')]) != cols.index(depth[ent(r, 'to')]) + 1:
                b += 1
        for c in cols:
            entering[c] = max(entering[c], n[c])
        back = max(back, b)
    col_x, x = {}, 12
    for i, c in enumerate(cols):
        if i:
            # every line entering this column gets its own vertical channel; lines leaving the previous column to run
            # under the boxes need room too, and so does a self-reference looping out of the previous column
            x += 44 + 12 * max(1, entering[c]) + 10 * back + (28 if cols[i - 1] in selfcols else 0)
        col_x[c] = x
        x += box_w
    right = x + 12 + (28 if cols[-1] in selfcols else 0) + 10 * back
    return {'names': names, 'depth': depth, 'cols': cols, 'col_x': col_x, 'box_w': box_w, 'right': right,
            'name_x': name_x, 'selfcols': selfcols}


def rounded(points, r=6):
    """SVG path through orthogonal points with rounded corners."""
    d = [f'M{points[0][0]:.1f} {points[0][1]:.1f}']
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]
        a = min(r, (abs(x1 - x0) + abs(y1 - y0)) / 2, (abs(x2 - x1) + abs(y2 - y1)) / 2)
        ux, uy = (x1 - x0, y1 - y0)
        n1 = (abs(ux) + abs(uy)) or 1
        vx, vy = (x2 - x1, y2 - y1)
        n2 = (abs(vx) + abs(vy)) or 1
        d.append(f'L{x1 - ux / n1 * a:.1f} {y1 - uy / n1 * a:.1f}')
        d.append(f'Q{x1:.1f} {y1:.1f} {x1 + vx / n2 * a:.1f} {y1 + vy / n2 * a:.1f}')
    d.append(f'L{points[-1][0]:.1f} {points[-1][1]:.1f}')
    return ' '.join(d)


def draw(side_key, spec, g, lang, uid, narrow=False):
    side = spec.get(side_key)
    other_key = 'tobe' if side_key == 'asis' else 'asis'
    other, has_other = index(spec.get(other_key)), bool(spec.get(other_key))
    t = STR[lang]
    ents = list(side['entities'])
    if len(ents) > 6:
        die(f'{side_key}: {len(ents)} entities. Keep the changed entities and their direct neighbours (6 or fewer), or use the table.')
    rels = side.get('relations', [])
    depth, cols, col_x, box_w, name_x = g['depth'], g['cols'], g['col_x'], g['box_w'], g['name_x']
    order = {n: i for i, n in enumerate(g['names'])}
    ents.sort(key=lambda e: (depth[e['name']], order[e['name']]))
    by_name = {e['name']: e for e in ents}

    pos, col_y = {}, {c: PAD for c in cols}
    for e in ents:
        c = cols[0] if narrow else depth[e['name']]    # narrow: one column, entities stacked, lines down the right side
        h = HEAD + ROW * max(1, len(e.get('fields', []))) + 6
        pos[e['name']] = (12 if narrow else col_x[c], col_y[c], h)
        col_y[c] += h + VGAP
    bottom = max(col_y.values()) - VGAP

    def row_y(entity, field):
        if entity not in pos:
            die(f'{side_key}: a relation names entity {entity}, which is not listed')
        fields = [f['name'] for f in by_name[entity].get('fields', [])]
        if field not in fields:
            die(f'{side_key}: a relation names {entity}.{field}, which is not in the entity')
        return pos[entity][1] + HEAD + ROW * fields.index(field) + ROW / 2

    def state(entity, field=None):
        """'add' / 'del' / 'mod' / '' for an entity or a field, seen from this side."""
        mark = 'del' if side_key == 'asis' else 'add'
        if not has_other:                              # the other side had no stored schema: every entity here is new (or gone)
            return mark if field is None else ''
        if entity not in other:
            return mark
        if field is None:
            return ''
        if field not in other[entity]:
            return mark
        mine = next(f for f in by_name[entity]['fields'] if f['name'] == field)
        return 'mod' if sig(mine) != sig(other[entity][field]) else ''

    other_rels = {(r['from'], r['to']) for r in ((spec.get(other_key) or {}).get('relations', []))}

    # Plan every line before drawing: how many leave each parent field (their attach points fan out),
    # which go straight to the next column, and which have to run under the boxes.
    fan = {}
    for r in rels:
        fan[r['to']] = fan.get(r['to'], 0) + 1
    seen_fan, plans = {}, []
    for r in rels:
        ce, cf = r['from'].split('.')
        pe, pf = r['to'].split('.')
        k = seen_fan.get(r['to'], 0)
        seen_fan[r['to']] = k + 1
        n = fan[r['to']]
        step = min(7, (ROW - 6) / max(1, n - 1)) if n > 1 else 0
        py = row_y(pe, pf) + (k - (n - 1) / 2) * step
        cy = row_y(ce, cf)
        kind = 'side' if narrow else 'self' if ce == pe else ('near' if cols.index(depth[ce]) == cols.index(depth[pe]) + 1 else 'under')
        plans.append({'r': r, 'ce': ce, 'pe': pe, 'py': py, 'cy': cy, 'kind': kind, 'first': k == 0,
                      'px': pos[pe][0] + box_w, 'cx': pos[ce][0]})
    # Vertical channels in the gap left of each column, one per line, ordered so that elbows in one gap nest instead of crossing.
    chan = {}
    for c in cols:
        here = [p for p in plans if p['kind'] != 'self' and depth[p['ce']] == c]
        here.sort(key=lambda p: (p['kind'] == 'under', p['py'] if p['kind'] == 'near' else 0, p['cy']))
        for i, p in enumerate(here):
            chan[id(p)] = i
    # Lines under the boxes: the shortest sits highest, so a longer one wraps around it instead of crossing it.
    under = sorted([p for p in plans if p['kind'] == 'under'], key=lambda p: abs(p['cx'] - p['px']))
    for i, p in enumerate(under):
        p['level'] = i
    # Narrow layout: every line leaves and returns on the right edge; the shortest sits innermost.
    for i, p in enumerate(sorted([p for p in plans if p['kind'] == 'side'], key=lambda p: abs(p['cy'] - p['py']))):
        p['lane'] = i
    out = []
    for p in plans:
        r, px, py, cx, cy = p['r'], p['px'], p['py'], p['cx'], p['cy']
        if p['kind'] == 'side':
            lx = px + 16 + 12 * p['lane']
            pts, end, direction = [(px, py), (lx, py), (lx, cy), (px, cy)], (px, cy), -1
        elif p['kind'] == 'self':
            lx = px + 16
            pts, end, direction = [(px, py), (lx, py), (lx, cy), (px, cy)], (px, cy), -1
        else:
            vx = cx - 22 - 12 * chan[id(p)]
            if p['kind'] == 'near':
                pts = [(px, py), (vx, py), (vx, cy), (cx, cy)] if abs(py - cy) > 1 else [(px, py), (cx, cy)]
            else:
                by = bottom + 16 + 12 * p['level']
                ox = px + 14 + 10 * p['level'] + (28 if depth[p['pe']] in g['selfcols'] else 0)
                pts = [(px, py), (ox, py), (ox, by), (vx, by), (vx, cy), (cx, cy)]
            end, direction = (cx, cy), 1
        cls = 'rel'
        if (r['from'], r['to']) not in other_rels:
            cls += ' del' if side_key == 'asis' else ' add'
        out.append(f'<path class="{cls}" d="{rounded(pts)}"/>')
        if p['first']:                                                                                  # one "one" bar per parent field
            n = fan[r['to']]
            half = 5 + ((n - 1) * min(7, (ROW - 6) / max(1, n - 1)) / 2 if n > 1 else 0)
            my = row_y(p['pe'], r['to'].split('.')[1])
            out.append(f'<path class="rel end" d="M{px + 6:.1f} {my - half:.1f}V{my + half:.1f}"/>')
        ex, ey = end
        if r.get('card', 'N:1').upper().startswith('N'):                                                # crow's foot at the child
            out.append(f'<path class="{cls} end" d="M{ex - 10 * direction:.1f} {ey:.1f}L{ex:.1f} {ey - 5:.1f}M{ex - 10 * direction:.1f} {ey:.1f}L{ex:.1f} {ey + 5:.1f}"/>')
        else:
            out.append(f'<path class="{cls} end" d="M{ex - 6 * direction:.1f} {ey - 5:.1f}V{ey + 5:.1f}"/>')
    bottom += (16 + 12 * len(under)) if under else 0

    for e in ents:
        ex, ey, h = pos[e['name']]
        st = state(e['name'])
        out.append(f'<g class="ent {st}">')
        out.append(f'<rect class="bg" x="{ex}" y="{ey}" width="{box_w}" height="{h}" rx="6"/>')
        out.append(f'<path class="hd" d="M{ex} {ey + HEAD}V{ey + 6}a6 6 0 0 1 6 -6H{ex + box_w - 6}a6 6 0 0 1 6 6V{ey + HEAD}Z"/>')
        out.append(f'<text class="nm" x="{ex + 12}" y="{ey + 20}">{html.escape(e["name"])}</text>')
        if st:
            label = ('+ ' + t['new']) if st == 'add' else ('− ' + t['gone'])
            out.append(f'<text class="st" x="{ex + box_w - 10}" y="{ey + 20}" text-anchor="end">{label}</text>')
        for i, f in enumerate(e.get('fields', [])):
            fy = ey + HEAD + ROW * i
            fs = '' if st else state(e['name'], f['name'])
            if fs:
                out.append(f'<rect class="row {fs}" x="{ex + 1}" y="{fy}" width="{box_w - 2}" height="{ROW}"/>')
                sym = {'add': '+', 'del': '−', 'mod': '~'}[fs]
                out.append(f'<text class="sym {fs}" x="{ex + 10}" y="{fy + 15}" text-anchor="middle">{sym}</text>')
            if keys(f):
                out.append(f'<text class="key" x="{ex + 20}" y="{fy + 15}">{html.escape(" ".join(keys(f)))}</text>')
            out.append(f'<text class="fn{" gone" if fs == "del" else ""}" x="{ex + name_x}" y="{fy + 15}">{html.escape(f["name"])}</text>')
            ty = f.get('type', '') + ('?' if f.get('null') else '')
            out.append(f'<text class="ty" x="{ex + box_w - 10}" y="{fy + 15}" text-anchor="end">{html.escape(ty)}</text>')
        out.append(f'<rect class="box" x="{ex}" y="{ey}" width="{box_w}" height="{h}" rx="6"/>')
        out.append('</g>')

    # a lone side is as wide as its own last column
    last = max(depth[e['name']] for e in ents)
    w = (col_x[last] + box_w + 12 + (28 if last in g['selfcols'] else 0)) if last != cols[-1] else g['right']
    if has_other:
        w = g['right']                                 # both sides get the same canvas, so they are drawn at the same scale
    if narrow:
        w = 12 + box_w + 16 + 12 * len(plans) + 12
    if under:
        w = max(w, max(p['px'] + 14 + 10 * p['level'] + 40 for p in under))
    h = bottom + PAD
    label = 'AS-IS' if side_key == 'asis' else 'TO-BE'
    title = html.escape(t['title'].format(side=label))
    desc = html.escape(t['desc'].format(n=len(ents), r=len(rels)))
    wrap = 'erd-wrap erd-n' if narrow else 'erd-wrap erd-w'
    return w, (f'<div class="{wrap}"><svg class="erd" role="img" aria-labelledby="{uid}-title {uid}-desc" viewBox="0 0 {w:.0f} {h:.0f}" '
               f'width="{w:.0f}" height="{h:.0f}" style="min-width: {min(w, 300 if narrow else max(340, w * 0.75)):.0f}px">'
               f'<title id="{uid}-title">{title}</title><desc id="{uid}-desc">{desc}</desc>\n'
               + '\n'.join(out) + '\n</svg></div>')


def main(argv):
    lang = 'en' if '--lang' in argv and argv[argv.index('--lang') + 1:][:1] == ['en'] else 'ko'
    args = [a for a in argv[1:] if not a.startswith('--') and a not in ('ko', 'en')]
    if len(args) != 1:
        die('usage: erd.py spec.json [--lang ko|en]')
    with open(args[0], encoding='utf-8') as f:
        spec = json.load(f)
    if not spec.get('asis') and not spec.get('tobe'):
        die('both sides are empty')
    g = grid(spec)
    t = STR[lang]
    solo = not (spec.get('asis') and spec.get('tobe'))
    sides, widest = [], 0
    for key, cls, label in (('asis', 'a', 'AS-IS'), ('tobe', 'b', 'TO-BE')):
        if spec.get(key):
            w, svg = draw(key, spec, g, lang, 'erd-' + key)
            widest = max(widest, w)
            # a second drawing for narrow screens: one column of entities, no empty columns, shown instead of the wide one below 760px
            _, slim = draw(key, spec, g, lang, 'erd-n-' + key, narrow=True)
            sides.append(f'<div class="side {cls}"><i class="lt {cls}">{label}</i>{svg}{slim}</div>')
    # a side of the pair is about 540px wide at 1280px; a wider diagram would hide behind a scrollbar, so the pair stacks instead
    kind = ' solo' if solo else (' wide' if widest > 540 else '')
    parts = [f'<div class="split erd-pair{kind}">'] + sides + ['</div>']
    for key, label in (('asis', 'AS-IS'), ('tobe', 'TO-BE')):
        if not spec.get(key):
            note = html.escape(spec.get(key + '_note') or '')
            parts.insert(0, f'<p class="missing">{t["none"]}({label}): {note}</p>')
    parts.append(f'<p class="erd-key">{t["key"]}</p>')
    print('\n'.join(parts))


if __name__ == '__main__':
    main(sys.argv)
