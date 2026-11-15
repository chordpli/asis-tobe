#!/usr/bin/env python3
"""Prints the before/after of two code or payload snippets as the template's line diff (.dv), with both views:
side by side and unified. The reader switches with the buttons in the head.

    python3 -I code_diff.py ASIS.txt TOBE.txt --label "Todo (src/domain/todo.rs)" [--start-a 84] [--start-b 50]
            [--context 3] [--mask id,time] [--note "12=배포 순서: 서버가 먼저 나가면 이 필드를 버린다"] [--view unified] [--lang ko|en] > diff.html

- ASIS.txt and TOBE.txt hold the snippet as it is at each commit (`git show <sha>:<path>`, cut to the part that matters).
  Use /dev/null for a side that does not exist (a new or a removed model, a new endpoint).
- One call per model or payload (one struct, one class, one response). Do not join several files into one snippet with path comments:
  the lines would be paired across files.
- The changed lines are computed (difflib), not marked by hand. Do not add <mark> yourself; the text is escaped.
- Inside a changed block, lines are paired by their key (the text before the first ":" or "="), so `"due_at": …` is never shown
  as a change of `"created_at": …`. A pair gets the differing part of each line marked.
- --label is the text in the head: the name and where it lives (「Todo (src/domain/todo.rs)」, 「GET /api/todos 응답」).
- --start-a and --start-b are the line numbers the snippets start at in their files, so the numbers shown are the real ones (default 1).
- --context N folds runs of unchanged lines longer than 2N+1 down to N lines on each side (default: keep every line).
- --mask id,time replaces values that differ on every run before comparing: UUIDs become <id>, RFC 3339 timestamps become <시각>
  (<time> with --lang en). Use it for payloads recorded from two running servers, and say so in the .src line under the diff.
  Do not mask when the id or time format itself is what changed.
- --note "<TO-BE line number>=<risk type>: <text>" attaches a line memo under that line (repeatable). Use the line number as shown
  (after --start-b). For the request cell of a scenario; only for what can break because of that line.
- --view unified opens unified first (the scenario panels are narrow). Default: side by side, unified on a narrow screen.
- --verb POST puts the HTTP method in its own box before the label; then --label holds the path and what it is (「/api/todos 요청 본문」).
- Paste the output where the template says. Standard library only.
"""
import difflib
import html
import re
import sys

STR = {
    'ko': {'uni': '합쳐서', 'split': '나란히', 'seg': '차이 보기 방식', 'stat': '{a}줄 추가, {d}줄 삭제', 'fold': '같은 줄 {n}개',
           'al_uni': '{label} 차이, 합쳐서 보기', 'al_split': '{label} 차이, 나란히 보기', 'add': '추가', 'del': '삭제',
           'line': '{n}번 줄', 'time': '<시각>'},
    'en': {'uni': 'Unified', 'split': 'Split', 'seg': 'Diff view', 'stat': '{a} lines added, {d} removed', 'fold': '{n} unchanged lines',
           'al_uni': '{label} diff, unified view', 'al_split': '{label} diff, split view', 'add': 'added', 'del': 'removed',
           'line': 'Line {n}', 'time': '<time>'},
}
UUID = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
TIME = re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?')


def die(msg):
    sys.stderr.write(f'code_diff.py: {msg}\n')
    raise SystemExit(2)


def read(path):
    if path == '/dev/null':
        return []
    with open(path, encoding='utf-8') as f:
        return f.read().rstrip('\n').split('\n')


def key_of(line):
    """What a line is about: the text before the first ':' or '=' (a JSON key, a field name), else the whole line."""
    s = line.strip()
    m = re.match(r'^[^:=]*[:=]', s)
    return m.group(0)[:-1].strip() if m else s


def inline(a, b):
    """Marks the part of each line that differs, after the common prefix and suffix. Returns escaped HTML for both."""
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    s = 0
    while s < min(len(a), len(b)) - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]:
        s += 1

    def word(ch):
        return ch.isalnum() or ch == '_'
    # do not cut identifiers in half: widen to word boundaries
    while p > 0 and word(a[p - 1]) and ((p < len(a) and word(a[p])) or (p < len(b) and word(b[p]))):
        p -= 1
    while s > 0 and word(a[len(a) - s]) and ((len(a) - s - 1 >= p and word(a[len(a) - s - 1])) or (len(b) - s - 1 >= p and word(b[len(b) - s - 1]))):
        s -= 1

    def wrap(t):
        mid = t[p:len(t) - s] if s else t[p:]
        if not mid.strip():
            return html.escape(t)
        return html.escape(t[:p]) + '<mark>' + html.escape(mid) + '</mark>' + (html.escape(t[len(t) - s:]) if s else '')
    return wrap(a), wrap(b)


def block(a, i1, i2, b, j1, j2):
    """Rows for one changed block. Lines with the same key on both sides become one changed line; the rest are removals and additions."""
    out = []
    ka, kb = [key_of(x) for x in a[i1:i2]], [key_of(x) for x in b[j1:j2]]
    i = j = 0
    for tag, x1, x2, y1, y2 in difflib.SequenceMatcher(None, ka, kb, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(x2 - x1):
                ha, hb = inline(a[i1 + x1 + k], b[j1 + y1 + k])
                out.append(('chg', i1 + x1 + k + 1, j1 + y1 + k + 1, ha, hb))
        else:
            for k in range(x1, x2):
                out.append(('del', i1 + k + 1, None, html.escape(a[i1 + k]), ''))
            for k in range(y1, y2):
                out.append(('add', None, j1 + k + 1, '', html.escape(b[j1 + k])))
    return out


def rows(a, b):
    """List of ('eq'|'del'|'add'|'chg', a_no, b_no, a_html, b_html)."""
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                e = html.escape(a[i1 + k])
                out.append(('eq', i1 + k + 1, j1 + k + 1, e, e))
        else:
            out += block(a, i1, i2, b, j1, j2)
    return out


def fold(rs, ctx):
    """Replaces long runs of 'eq' rows with ('fold', n)."""
    if ctx is None:
        return rs
    out, i = [], 0
    while i < len(rs):
        if rs[i][0] != 'eq':
            out.append(rs[i])
            i += 1
            continue
        j = i
        while j < len(rs) and rs[j][0] == 'eq':
            j += 1
        run = rs[i:j]
        head = 0 if i == 0 else ctx            # nothing above the first run needs context
        tail = 0 if j == len(rs) else ctx
        if len(run) > head + tail + 1:
            out += run[:head] + [('fold', len(run) - head - tail)] + (run[len(run) - tail:] if tail else [])
        else:
            out += run
        i = j
    return out


def main(argv):
    opts = {'--lang': 'ko', '--label': '', '--context': None, '--start-a': '1', '--start-b': '1', '--mask': '', '--view': 'split', '--verb': ''}
    notes, args, i = {}, [], 1
    while i < len(argv):
        if argv[i] in opts or argv[i] == '--note':
            if i + 1 >= len(argv):
                die(f'{argv[i]} needs a value')
            if argv[i] == '--note':
                m = re.match(r'^(\d+)=([^:]+):\s*(.+)$', argv[i + 1])
                if not m:
                    die('--note takes "<TO-BE line number>=<risk type>: <text>"')
                notes[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
            else:
                opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 2 or not opts['--label']:
        die('usage: code_diff.py ASIS.txt TOBE.txt --label "<what this is>" [--start-a N] [--start-b N] [--context N] '
            '[--mask id,time] [--note "N=type: text"] [--view unified] [--lang ko|en]')
    if opts['--view'] not in ('split', 'unified'):
        die('--view is split or unified')
    t = STR['en' if opts['--lang'] == 'en' else 'ko']
    ctx = int(opts['--context']) if opts['--context'] is not None else None
    a, b = read(args[0]), read(args[1])
    if not a and not b:
        die('both sides are empty')
    masks = {m.strip() for m in opts['--mask'].split(',') if m.strip()}
    if masks - {'id', 'time'}:
        die('--mask takes id, time, or both')
    for side in (a, b):
        for k, line in enumerate(side):
            if 'id' in masks:
                line = UUID.sub('<id>', line)
            if 'time' in masks:
                line = TIME.sub(t['time'], line)
            side[k] = line
    oa, ob = int(opts['--start-a']) - 1, int(opts['--start-b']) - 1
    rs = [(k, na + oa if na else na, nb + ob if nb else nb, ha, hb) for k, na, nb, ha, hb in rows(a, b)]
    changed = [r for r in rs if r[0] == 'chg' and r[3] != r[4]]
    rs = [('eq',) + r[1:] if r[0] == 'chg' and r[3] == r[4] else r for r in rs]       # same key, same text: not a change
    added = sum(1 for r in rs if r[0] == 'add') + len(changed)
    removed = sum(1 for r in rs if r[0] == 'del') + len(changed)
    known = {r[2] for r in rs if r[2]}
    for n in notes:
        if n not in known:
            die(f'--note {n}: the TO-BE side has no line {n}')
    rs = fold(rs, ctx)
    label = html.escape(opts['--label'])
    vh_add, vh_del = f'<span class="vh">{t["add"]}</span>+', f'<span class="vh">{t["del"]}</span>−'

    def memo(nb, span):
        if nb not in notes:
            return []
        kind, text = notes[nb]
        return [f'<tr class="cm"><td colspan="{span}"><div class="cm-in"><div class="cm-box"><b>{html.escape(kind)}</b>{html.escape(text)}</div></div></td></tr>']

    uni, sp, dels, adds = [], [], [], []

    def flush():                                       # unified view: every removed line of a block, then its additions
        nonlocal dels, adds
        uni.extend(dels + adds)
        dels, adds = [], []

    for r in rs:
        if r[0] == 'fold':
            flush()
            text = t['fold'].format(n=r[1])
            uni.append(f'<tr class="fold"><td colspan="4">{text}</td></tr>')
            sp.append(f'<tr class="fold"><td colspan="6">{text}</td></tr>')
            continue
        kind, na, nb, ha, hb = r
        if kind == 'eq':
            flush()
            uni.append(f'<tr><td class="ln">{na}</td><td class="ln">{nb}</td><td class="sg"></td><td class="cd">{ha}</td></tr>')
            uni.extend(memo(nb, 4))
            sp.append(f'<tr><td class="ln">{na}</td><td class="sg"></td><td class="cd">{ha}</td><td class="ln mid">{nb}</td><td class="sg"></td><td class="cd">{hb}</td></tr>')
            continue
        if kind in ('del', 'chg'):
            dels.append(f'<tr class="del"><td class="ln">{na}</td><td class="ln"></td><td class="sg">{vh_del}</td><td class="cd">{ha}</td></tr>')
        if kind in ('add', 'chg'):
            adds.append(f'<tr class="add"><td class="ln"></td><td class="ln">{nb}</td><td class="sg">{vh_add}</td><td class="cd">{hb}</td></tr>')
            adds.extend(memo(nb, 4))
        left = (f'<td class="ln del">{na}</td><td class="sg del">−</td><td class="cd del">{ha}</td>' if kind != 'add'
                else '<td class="ln gap"></td><td class="sg gap"></td><td class="cd gap"></td>')
        right = (f'<td class="ln mid add">{nb}</td><td class="sg add">+</td><td class="cd add">{hb}</td>' if kind != 'del'
                 else '<td class="ln mid gap"></td><td class="sg gap"></td><td class="cd gap"></td>')
        sp.append(f'<tr>{left}{right}</tr>')
    flush()

    view = opts['--view']
    pressed = lambda v: 'true' if v == view else 'false'
    narrow = ' data-narrow="unified"' if view == 'split' else ''
    lines = [
        f'<div class="dv" data-view="{view}"{narrow}>',
        '  <div class="dv-head">',
        *([f'    <span class="verb">{html.escape(opts["--verb"])}</span>'] if opts['--verb'] else []),
        f'    <span class="path">{label}</span>',
        f'    <span class="stat" aria-label="{t["stat"].format(a=added, d=removed)}"><span class="p">+{added}</span><span class="m">−{removed}</span></span>',
        f'    <span class="seg nojs-hide" role="group" aria-label="{t["seg"]}"><button type="button" data-view="split" aria-pressed="{pressed("split")}">{t["split"]}</button>'
        f'<button type="button" data-view="unified" aria-pressed="{pressed("unified")}">{t["uni"]}</button></span>',
        '  </div>',
        '  <div class="dv-body">',
        f'    <table class="dl v-uni" aria-label="{t["al_uni"].format(label=label)}">',
        *['      ' + x for x in uni],
        '    </table>',
        f'    <table class="dl sp v-split" aria-label="{t["al_split"].format(label=label)}">',
        *['      ' + x for x in sp],
        '    </table>',
        '  </div>',
    ]
    if notes:                                          # the split view cannot hold a memo between two columns: they gather below it
        items = ''.join(f'<li>{t["line"].format(n=n)}: <b>{html.escape(k)}</b> {html.escape(x)}</li>' for n, (k, x) in sorted(notes.items()))
        lines.append(f'  <ul class="dv-notes">{items}</ul>')
    lines.append('</div>')
    print('\n'.join(lines))


if __name__ == '__main__':
    main(sys.argv)
