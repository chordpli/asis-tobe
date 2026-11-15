#!/usr/bin/env python3
"""Run one mechanical pass over a finished document's text. Finds line-break, modifier, and emphasis-overuse problems and reports them line by line.

    python3 -I text_lint.py <doc.html> [--max-ko 70] [--max-en 160]

What it finds:
- modifier: modifiers (매우, 정말, 크게, 단순히, very, simply, seamlessly ...). They add no facts, so delete them
- vague: empty evaluative words (깔끔한, 강력한, 효과적인, robust, clean ...). Replace with what improved and how
- long: a sentence is too long (over 70 chars for ko, 160 for en). Split it or move evidence to a .src line. Not counted: the scenario rail (.rail, chips are not a sentence), quoted PR titles (.prs), line diffs (.dv-body), text inside 「」 or “ ”, and the .where tag of an impact path node
- br: <br> inside a sentence. CSS does the line breaking. A forced break lands in an awkward spot when the width changes
- paren: a parenthetical is over 40 chars. Unwrap it into a sentence or move it to an evidence line
- strong: two or more <strong> in one paragraph. Emphasis stops being emphasis
- quote: three or more quotation pairs (「」 or “”) in one sentence. Quote only on-screen text
- verdict: the summary conclusion is too long (over 100 chars for ko, 160 for en)
- verdict-code: the summary conclusion contains an identifier (<code>); it is written in the user's words
- cell: a cell of a summary card (.card) table is over 25 chars (45 for en) or has two or more clauses split by sentence punctuation. Each cell of the rollout order table is one phrase
- dense: a paragraph is too dense. Over 280 chars for ko (500 for en), or over 70% of that with more than four sentences, or over half of that with five or more identifiers (<code>). If the paragraph lists runs, commits, or items as sentences, turn it into a table
- term-mix: two words for one concept in the same document (버전 and 판, 필드 and 칸, ...). Pick one and keep it (terms.md, "One concept, one term")
- transl: Korean translationese shapes (~에 의해, ~에 대한, ~을 통해, ~로부터, ~로 하여금, -들 on common nouns, ~할 수 있게 된다). Rewrite as Korean (terms.md, "Korean editing")
- hangul-en: Hangul left in the English edition (lang="en"). Identifiers whose original is Hangul, such as test names and fixture values, are skipped when placed inside <code>

Output: one line per finding, `kind | start of sentence`. The last line is a JSON of counts per kind. A person makes the judgment (some 「크게」 are needed in context).
Dependencies: standard library only.
"""
import html
import json
import re
import sys
from html.parser import HTMLParser

KO_MODIFIERS = ['매우', '정말', '아주', '굉장히', '상당히', '크게', '완전히', '단순히', '그저', '사실상', '기본적으로',
                '확실히', '분명히', '훨씬', '다소', '꽤', '무척', '너무', '엄청', '전혀 문제없이', '자연스럽게', '깔끔하게']
KO_VAGUE = ['깔끔한', '강력한', '효과적인', '효율적인', '획기적인', '직관적인', '원활한', '최적의', '다양한', '유연한', '개선된']
EN_MODIFIERS = ['very', 'really', 'simply', 'just', 'basically', 'actually', 'quite', 'extremely', 'easily',
                'seamlessly', 'significantly', 'greatly', 'clearly', 'obviously', 'completely']
EN_VAGUE = ['robust', 'clean', 'powerful', 'effective', 'efficient', 'intuitive', 'seamless', 'optimal', 'various', 'improved']

P = r'(?=[이가은는을를의에와과도로만,.)」\s]|$)'
NB = r'(?<![가-힣])'
# Pairs of words for one concept. The first is the glossary word. Particles after the noun are allowed; longer words (판정, 칸막이) are not matches
TERM_PAIRS = [
    ('버전', NB + r'버전' + P, NB + r'판' + P),
    # 칸 is also the template's rail cell (「여섯 칸」) and an on-screen input box (「입력 칸」); those are not the API field
    ('필드', NB + r'필드' + P, r'(?<!입력 )(?<!여섯 )(?<!걸친 )(?<![가-힣])칸' + P),
    ('호출처', NB + r'호출처' + P, r'소비자' + P + r'|읽는 곳|쓰는 곳'),
    ('스토어 배포 빌드', r'스토어 배포|구버전 앱', r'옛 앱|스토어 판'),
    ('영향 경로', r'영향 경로', NB + r'사슬' + P),
]
KO_TRANSL = [
    ('에 의해', r'에 의해|에 의한'),
    ('에 대한', r'에 대한|에 대해|에 관한|에 관해'),
    ('을 통해', r'[을를] 통해|[을를] 통한'),
    ('로부터', r'로부터'),
    ('로 하여금', r'로 하여금'),
    ('-들', r'(필드|호출처|파일|화면|요청|커밋|테스트|값|변경|항목|시나리오|문구)들(?=[이은을의에도과,\s]|$)'),
    ('수 있게 된다', r'수 있게 되|것이 필요하'),
]

SKIP_TAGS = {'script', 'style', 'pre', 'code', 'kbd', 'title'}
VOID_TAGS = {'br', 'img', 'input', 'meta', 'link', 'hr', 'col', 'source', 'wbr', 'area', 'base', 'embed', 'track'}
NOLONG_CLASSES = {'rail', 'prs'}   # chips and quoted PR titles are not sentences
MUTE_CLASSES = {'where', 'erd-wrap', 'dv-body'}   # a location tag glued to the end of an impact path claim; the entity diagram's SVG labels; code and payload lines of a line diff
BLOCK_TAGS = {'p', 'li', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'summary', 'div', 'section'}


class Blocks(HTMLParser):
    """Collects, per block element, the text (excluding code), the emphasis count, and the <br> count."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = 'ko'
        self.blocks = []
        self.cur = None
        self.skip = 0
        self.stack = []
        self.divs = 0
        self.card_at = None
        self.open = []      # (tag, kind) for every open non-void element; kind is 'nolong', 'mute' or ''
        self.nolong = 0
        self.mute = 0

    def flush(self):
        if self.cur and self.cur['text'].strip():
            self.cur['text'] = re.sub(r'\s+', ' ', self.cur['text']).strip()
            self.blocks.append(self.cur)
        self.cur = None

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            cls = set((dict(attrs).get('class') or '').split())
            kind = 'nolong' if cls & NOLONG_CLASSES else 'mute' if cls & MUTE_CLASSES else ''
            self.open.append((tag, kind))
            if kind == 'nolong':
                self.nolong += 1
            if kind == 'mute':
                self.mute += 1
        if tag == 'html':
            self.lang = dict(attrs).get('lang', 'ko')[:2]
        if tag in SKIP_TAGS:
            self.skip += 1
            if self.cur is not None and tag in ('code', 'kbd'):
                self.cur['text'] += ' ⟨code⟩ '
            return
        if tag == 'div':
            self.divs += 1
            if self.card_at is None and 'card' in (dict(attrs).get('class') or '').split():
                self.card_at = self.divs
        if tag in BLOCK_TAGS:
            self.flush()
            self.cur = {'tag': tag, 'text': '', 'strong': 0, 'br': 0, 'verdict': 'verdict' in (dict(attrs).get('class') or ''),
                        'card': self.card_at is not None, 'nolong': self.nolong > 0}
        elif self.cur is not None:
            # <b> is not counted: it is a structural marker of the template (step numbers, layer tags, 「같음.」). In-sentence emphasis uses only <strong>
            if tag == 'strong':
                self.cur['strong'] += 1
            if tag == 'br':
                self.cur['br'] += 1

    def handle_endtag(self, tag):
        while self.open:
            otag, kind = self.open.pop()
            if kind == 'nolong':
                self.nolong -= 1
            if kind == 'mute':
                self.mute -= 1
            if otag == tag:
                break
        if tag == 'div':
            if self.card_at == self.divs:
                self.card_at = None
            self.divs = max(0, self.divs - 1)
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
            return
        if tag in BLOCK_TAGS:
            self.flush()

    def handle_data(self, data):
        if self.skip or self.mute or self.cur is None:
            return
        self.cur['text'] += data


def sentences(text, lang):
    parts = re.split(r'(?<=[.!?。])\s+' if lang == 'en' else r'(?<=[다요음함됨임.!?])\.?\s+', text)
    return [p.strip() for p in parts if p.strip()]


def word_hits(sentence, words, lang):
    hits = []
    for w in words:
        if lang == 'en':
            if re.search(rf'\b{re.escape(w)}\b', sentence, re.I):
                hits.append(w)
        elif re.search(rf'(^|[\s(「“]){re.escape(w)}', sentence):
            hits.append(w)
    return hits


def main(argv):
    args, opts = [], {'--max-ko': 70, '--max-en': 160}
    it = iter(argv)
    for a in it:
        if a in opts:
            opts[a] = int(next(it))
        else:
            args.append(a)
    if len(args) != 1:
        raise SystemExit(__doc__)
    parser = Blocks()
    parser.feed(open(args[0], encoding='utf-8').read())
    parser.flush()
    lang = parser.lang
    mods, vague = (EN_MODIFIERS, EN_VAGUE) if lang == 'en' else (KO_MODIFIERS, KO_VAGUE)
    limit = opts['--max-en'] if lang == 'en' else opts['--max-ko']
    found, counts = [], {}

    def hit(kind, text, extra=''):
        counts[kind] = counts.get(kind, 0) + 1
        found.append(f'{kind} | {text[:60]}{"…" if len(text) > 60 else ""}{(" | " + extra) if extra else ""}')

    vlimit = 160 if lang == 'en' else 100
    for b in parser.blocks:
        text = html.unescape(b['text'])
        if b.get('verdict') and len(text.replace('⟨code⟩', 'x')) > vlimit:
            hit('verdict', text, f'{len(text)} chars, limit {vlimit}')
        if b.get('verdict') and '⟨code⟩' in text:
            hit('verdict-code', text, 'the conclusion names an identifier; say it in the user\'s words')
        if b['br']:
            hit('br', text)
        if b['strong'] >= 2:
            hit('strong', text, f'{b["strong"]} found')
        if b['tag'] in ('th',):
            continue
        if b['tag'] == 'td' and b.get('card'):
            # PR numbers and identifier lists are lists, not phrases, so they are excluded from the length
            n = len(re.sub(r'\s+', ' ', re.sub(r'#\d+|⟨code⟩|,', '', text)).strip())
            if n > (45 if lang == 'en' else 25) or len(re.findall(r'[.。]\s', text + ' ')) >= 2:
                hit('cell', text, f'{n} chars')
        if b['tag'] in ('p', 'li', 'td', 'div', 'summary'):
            ss = sentences(text, lang)
            plain_all = text.replace('⟨code⟩', 'x')
            codes = text.count('⟨code⟩')
            cap = 500 if lang == 'en' else 280
            n = len(plain_all)
            # A cell of several short sentences or only identifiers is not hard to read. Flag it only when the length is also exceeded
            if n > cap or (len(ss) > 4 and n > cap * 0.7) or (codes >= 5 and len(ss) >= 3 and n > cap * 0.5):
                hit('dense', text, f'{len(ss)} sentences, {n} chars, {codes} identifiers')
        for s in sentences(text, lang):
            for w in word_hits(s, mods, lang):
                hit('modifier', s, w)
            for w in word_hits(s, vague, lang):
                hit('vague', s, w)
            plain = s.replace('⟨code⟩', 'x')
            # screen text quoted verbatim is not the author's sentence: a quotation counts as one character
            own = re.sub(r'「[^」]*」|“[^”]*”', 'x', plain)
            if len(own) > limit and not b.get('nolong'):
                hit('long', s, f'{len(plain)} chars')
            for m in re.findall(r'\(([^()]*)\)', plain):
                if len(m) > 40:
                    hit('paren', s, f'parenthetical {len(m)} chars')
            if len(re.findall(r'「[^」]*」|“[^”]*”', s)) >= 3:
                hit('quote', s)
            if lang != 'en':
                for name, rx in KO_TRANSL:
                    if re.search(rx, s):
                        hit('transl', s, name)
            if lang == 'en' and re.search(r'[가-힣]', s):
                hit('hangul-en', s)
    if lang != 'en':
        alltext = ' '.join(html.unescape(b['text']) for b in parser.blocks)
        # Quoted originals (test names, on-screen text, commit titles) stay verbatim, so they are not counted
        alltext = re.sub(r'「[^」]*」|“[^”]*”', ' ', alltext)
        for name, a, b2 in TERM_PAIRS:
            na, nb = len(re.findall(a, alltext)), len(re.findall(b2, alltext))
            if na and nb:
                m = re.search(b2, alltext)
                hit('term-mix', alltext[max(0, m.start() - 20):m.end() + 20], f'{name}: {na} vs other {nb}')
    print('\n'.join(found))
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1:])
