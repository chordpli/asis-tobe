# Terms and per-language editing

Developers, QA, and planners read the document together. Write in words the industry uses. Product-specific names (feature, plan, and menu names) follow the product's spelling, and on-screen text is quoted verbatim (「」 in the Korean edition, “ ” in the English edition).

## Glossary

| Do not use (쓰지 않는 말) | Use in ko (쓰는 말 (ko)) | en | Plain explanation, added in parentheses on first use (쉬운 풀이) |
|---|---|---|---|
| 층 | 레이어 | layer | The unit for splitting a change into views. In order: data (DB), API spec, behavior, screen, user |
| 칸 | 필드 | field | One value inside a response or table. E.g. `status` |
| 계약 | API 스펙 | API contract | The promise the server makes about what shape it will answer in |
| 의미 변화 | 시맨틱 변경 | semantic change | Name and type stay the same but the meaning of the value changes |
| 소비자, 읽는 곳 | 호출처 | consumer | Code that actually reads and uses that field |
| 옛 앱 판, 스토어 판 | 구버전 앱(스토어 배포 빌드) | legacy app build (store release) | The app already installed on users' phones. It runs old code until updated |
| 판, 버전 행 | 버전, 리비전 | version, revision |  |
| 호환 칸, 폐기 예정 칸 | deprecated 필드 | deprecated field | A field still sent but scheduled for removal |
| 깨진다 | breaking change, 장애 | breaking change, outage | When this change ships, existing call sites error out |
| 고정 응답, 가짜 응답 | mock 응답 | mock response | A hand-made fake response to render a screen without a server |
| 픽스처 | 테스트 fixture | test fixture | Fixed input and response data used by tests |
| 사본(코드젠) | 생성 코드(codegen) | generated client (codegen) | Type files auto-generated from the server spec. Never edited by hand; regenerated |
| 장면 | 화면 시나리오 | screen scenario | One predefined screen state for taking screenshots |
| 단정 | assertion | assertion | One 「이 값이어야 한다」 ("it must be this value") check line inside a test |
| 사슬, 인과 | 영향 경로 | impact chain | The path along which a change spreads to the next layer |
| 머지 순서 | 머지·배포 순서 | merge and rollout order | Which PR to merge and ship first so nothing breaks |
| 한쪽만 나간 상태 | 부분 배포 상태 | partial rollout state | The state in between, when only the server or only the app has the new version |
| 걷는다 | 제거한다 | remove |  |
| 머리, 머리말 | 헤더 | header |  |
| 지금 머지 가능 | 즉시 머지 가능 | ready to merge |  |
| 조건, 시작 상태 | 전제 조건 | precondition | The state that must already be true when the scenario starts. The Given of use cases and BDD. The web and app cell name is 「준비」 |
| 행동, 입력 | 트리거 | trigger | The action or event that starts the scenario. Can be an event with no person, such as a batch or settlement. The When of BDD. The web and app cell name is 「요청」 |
| 판정, 계산 | 처리 | process | The receiver applying rules and returning a value. Process and Output in SIPOC. The web and app cell name is 「응답」 |
| 표시, 보이는 것 | 접점 | touchpoint | What the acting person directly sees and touches. The customer touchpoint of a service blueprint. The web and app cell name is 「화면」 |
| 기록, 흔적 | 감사 추적 | audit trail | Traces left so others can see them later. The web and app cell name is 「로그」 |
| 끝 상태 | 사후 조건 | postcondition | The state that persists after it ends. The Then of use cases and BDD. The web and app cell name is 「결과」 |
| 전환, 배포 순서 칸 | 전환 계획 | cutover | From when it changes, who is still on the old way, what order must be kept |
| 근거, 변경 기록 칸 | 변경 요청 | change request | The document that produced the change. RFC in ITIL, engineering change notice in manufacturing. In web and app, PRs and commits |
| — | OTA | over-the-air update | A deploy that changes only the app's JS without store review |
| — | typecheck | typecheck | The check that types match. When codegen changes, it breaks in this check |

Choose words not in the table by the same criteria. Add the explanation in parentheses only once, on first use in the document. From the second use on in the same document, use the term alone. For words that only work in-house (「AC」, screen nicknames the team made up), state what they are on first use (e.g. AC(이슈의 완료 조건) — "the issue's completion criteria").

## One concept, one term (한 개념에 한 용어)

Readers take a new word for a new thing. If one paragraph says 버전 and the next says 판, a planner or QA reader asks whether these are two different things, and searching the document for one word misses the other (Plain Language Guide, "Consistency counts"; Toss technical writing guide, 「용어를 일관되게 사용하세요」).

- Pick one term per concept on first use and keep it to the end: in body text, table headers, captions, the impact path, and the summary. Do not swap in a synonym for variety.
- Pairs that drift most often in this document: 버전/판/리비전, 필드/칸/항목, 호출처/소비자/쓰는 곳, 배포/출시/릴리스, 스토어 배포 빌드/구버전 앱/옛 앱, 요청/호출, 저장/반영. Use the glossary word; if two words in a pair really mean different things here (리비전 as a stored row vs 버전 as a release), say so once on first use.
- The same applies to product objects and screen names: once 「배송 메모」, never 「요청 사항」 or 「메모란」 for the same field later. Quote the on-screen label once; then use the same noun.
- Before finishing, search the document for each pair. `text_lint.py` reports `term-mix` when both words of a pair appear.
- Quoted originals (test names, on-screen text, commit titles) stay verbatim even if they use the other word; `term-mix` ignores text inside 「」 and “ ”. Never drop or reword a quoted test name to avoid the mix: the test name is the evidence.

## Korean editing

1. Replace words using the glossary above.
2. **Remove translationese (번역투).** These instructions are in English, so Korean output drifts toward English sentence shapes. Rewrite them as Korean (새국어생활 22-1, 「영한 번역에 나타난 번역투 문장」; 『문장기술』):
   - 「~에 의해 ~되다」 → active with the real actor: 「서버에 의해 버려진다」 → 「서버가 버린다」.
   - 「~에 대한」, 「~에 관한」 → a plain particle: 「문구에 대한 저장」 → 「문구 저장」, 「배지에 대한 판정」 → 「배지 판정」.
   - 「~을 통해」 → 「~로」: 「PATCH 를 통해 저장한다」 → 「PATCH 로 저장한다」. 「~로부터」 → 「~에서」.
   - Inanimate subject causing something (「이 변경은 사용자로 하여금 ~하게 한다」) → the person or system as subject (「사용자가 ~한다」).
   - 「-들」 on every plural (「필드들」, 「호출처들」) → drop it unless the count matters.
   - 「~하는 것이 필요하다」, 「~할 수 있게 된다」 → 「~해야 한다」, 「~할 수 있다」.
   `text_lint.py` reports `transl` for these shapes. Some are needed in context; a person decides.
3. If the project or user has a writing-style guide or skill, proofread with it. Otherwise keep these: one sentence says one thing; reduce middle-dot (·) lists and arrow overuse; do not chain the same sentence ending more than three times; delete closing remarks and restatements.
4. The template's structural symbols (AS-IS/TO-BE in badges, table headers, the ↓ in the impact path) are not subject to editing.

## English editing

Rewrite in English, do not translate. Facts, numbers, paths, and order must match the Korean edition.

1. Use the en column of the glossary.
2. Short declarative sentences, active voice. One thing per sentence.
3. US technical writing conventions: sentence-case headings, dates as `2026-11-10`, backticks for code, paths, and fields.
4. Leave no Hangul. Quoted on-screen text uses the actual text from screenshots taken in that language (do not translate ko text into it). The exception is identifiers whose original is Hangul: test names, fixture values, commit titles, branch names. Translating them makes them unsearchable, so keep the original in backticks and add the meaning in parentheses on first use (e.g. `승인 전문을 보낸다` (sends the full approval text)).
5. Use “ ” for quotation marks. 「」 is only for the Korean edition (both on-screen text and test name quotes).
6. Delete filler adverbs (simply, just, basically) and closing remarks (Hope this helps).

## Line breaks and modifiers (줄바꿈과 꾸밈말)

These apply to all languages. `scripts/text_lint.py <doc.html>` finds the following. A person makes the judgment.

- **Delete modifiers.** 「매우」, 「정말」, 「크게」, 「단순히」, 「사실상」, very, simply, just, seamlessly add no facts. If degree matters, use numbers (instead of 「크게 줄었다」 "greatly reduced", 「1,748px 에서 1,300px 로」 "from 1,748px to 1,300px").
- **Turn evaluative words into facts.** Replace 「깔끔한」, 「강력한」, 「효과적인」, 「개선된」, robust, clean, improved with one phrase on what improved and how.
- **One sentence is around 70 characters (en 160).** If longer, split it. If evidence paths or long identifiers lengthen a sentence, move them to a `.src` evidence line.
- **Keep parentheticals short.** If over 40 characters, unwrap the parentheses into the next sentence. No parentheses inside parentheses.
- **Short paragraphs; lists as tables.** A paragraph is within 280 characters (en 500), and even when shorter, do not chain five long sentences or five identifiers (`<code>`). Do not chain three or more items of the same shape (runs and commits, base and target, cases and results) as sentences; put them in a `.ft` table. Notes recording base commits, capture sources, and E2E runs are the typical case. In the `.note` under the table, leave only one or two sentences of exceptions that cannot go in a table.
- **CSS does the line breaking.** Do not put `<br>` inside sentences. The template breaks Korean at word (eojeol) boundaries (`word-break: keep-all`) and avoids leaving only one or two characters on the last line (`text-wrap: pretty`). After fixing, eyeball the 420px render for breaks mid-word and orphan lines.
- **Emphasis only through devices.** Bold only for the summary conclusion and warning blocks; in-sentence `<strong>` at most one per paragraph. Color emphasis only for badges, change markers, and boxes. Quotation marks only for on-screen text, at most two per sentence.

## Aligning language editions

After writing both language editions, cross-check: the number of summary items, number of rollout order steps, number of table rows, and box numbers are the same. If any differ, fix the side that is missing something.
