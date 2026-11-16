# Scenario rail (step 4b)

Read this before filling the template's 「시나리오별 전후」 ("before/after by scenario") section. Layer sections are evidence; readers see the scenarios first. Reviewers and QA read "if I do it in this order, what changes?" from a one-line rail and click chips to expand one step at a time (patterns from step rails and screen stages, GitHub Files changed, GitHub image diff, Chromatic, the Stripe changelog, and oasdiff).

In an English edition, use the en strings from the fixed-strings comment in [template.html](template.html) for every cell, skeleton, layer, head and table name (e.g. 결과 → Outcome, API 스펙 → API contract). The English names here describe the concepts; the template comment is the source for output labels.

## Choosing scenarios

- One thing one person goes through once, or one event, is one scenario (e.g. 「데스크톱 웹에서 /settings 를 연다」 "open /settings on desktop web", 「월말 청구 배치가 돈다」 "the month-end billing batch runs").
- Write the actor before the scenario title: a user, an operator, or a system such as a batch job.
- Default: one per issue AC, about 3 in total. If the same action splits by width or platform, keep them separate.
- One `.scn` per scenario, ids `s1`, `s2`. Panel ids are `s<number>-p<step>`.

## Six cells and two heads

Cells are defined by questions, not by artifact names. Cell names follow the domain mapping table in [domains.md](domains.md); for web and app development they are 준비 (Setup), 요청 (Request), 응답 (Response), 화면 (Screen), 로그 (Logs), 결과 (Outcome). Never reorder or drop any of the six; with no empty cells, "not checked here" and "same here" stay distinguishable. The two heads (변경 요청 "change request", 전환 계획 "cutover") go in the scenario head, outside the rail.

The skeleton name stays in the markup next to the cell name (`.sk`) so documents from different domains align, but the template does not show it: readers met two names per step and had to decode the second.

| Skeleton | Question | Cell name for web and app | Where the real artifact comes from | Device |
|---|---|---|---|---|
| 전제 조건 (Precondition) | Who starts, in what state? | 준비. State needed to reproduce: account, device and width, data that must already exist, settings | Test account rules, screen scenario definitions, seeds | Side-by-side text (`.split`). A list if there are several conditions |
| 트리거 (Trigger) | What is done or what event happens, and what is passed? | 요청. The payload sent. Changed cells only | Fixtures in the API spec section | Line diff (`.dv`) printed by `scripts/code_diff.py --view unified`: both views, changed words marked; a line memo (`--note`) under a line that carries risk |
| 처리 (Process) | By what rule does the receiver return what? | 응답. The payload received and the status code. Changed fields only | Fixtures in the API spec section | Field table (`필드, 변경, 리소스` — field, change, resource). Only one representative branch |
| 접점 (Touchpoint) | What does the acting person see? | 화면. One line of text per changed spot | Captures in the screen section | Side-by-side text. Captures go in the screen stage at the end of the scenario (`.stage`, step 7) |
| 감사 추적 (Audit trail) | What traces will others see later? | 로그. Server logs, app errors (Sentry etc.), analytics events. What newly appears or disappears | Diff of log and event calls via `git grep` | Event rows (`.logrow`): branch and name, whether it is emitted (●) or not (○) in AS-IS and TO-BE |
| 사후 조건 (Postcondition) | What is different after it ends? | 결과. Do not restate the screen cell. Only what persists afterward: DB rows, what the user holds, the state seen on next open | Behavior section, data section | Side-by-side text. Bars (`.cost`, ratio with the larger side as 100%) only when there are comparable numbers (cost, count, time) |
| (head) 변경 요청 (Change Request) | What document produced the change? | PRs and commits | `git log <base>..HEAD -- <file>`, PR list | Evidence row: PR list (`.prs`) and commit row (`.commits`) |
| (head) 전환 계획 (Cutover) | From when? Who is still on the old way? Is there an order to keep? | Merge and rollout order, partial rollout state | Step 6 compatibility table, merge and rollout order | Cutover row. With two or more repos, repo lanes (`.tl`) and the required order (bold line) |

## Cell rules

- **Process vs. Touchpoint.** If the returned value or rule changes, Process changed. If only what the receiver reads grew, Process is 「같음」 ("same") and Touchpoint changed. Example: the server response is unchanged but the app newly reads a field that was already arriving to draw a badge: response cell 「같음」, screen cell changes.
- **A trigger can be an event with no person.** For batches, settlements, or scheduled jobs, write the event in the trigger cell (「월말 청구 배치가 돈다」). The actor is then that system.
- **Branch tables go to the Behavior layer section.** If a Process cell needs a table by input branch, put it in the Behavior layer section, keep one representative branch in the panel, and link that section from the evidence line at the end of the panel.
- **Same is one cell.** The panel of a cell with equal values is `<div class="side same"><b>같음.</b> <근거 한 줄></div>` (same. <one line of evidence>).
- **Calls, not payload.** If the body is the same and only which calls are made changes (two more GETs when the list opens), the request cell's line diff lists the calls, one per line. A new scenario's diff has added lines only.
- **Not applicable.** 「해당 없음. <이유>」 ("not applicable. <reason>"). Examples: the screen cell of a server job with no screen, the touchpoint cell of a nightly batch where the acting party sees nothing.
- **Never write 「같음」 without evidence.** For request and response: a `git grep` result showing no API call code in the changed files. For logs: a result showing no log or event calls in the diff. If the same evidence appears in another cell, you may point to it (「요청과 같은 근거다」 "same evidence as request"). If you found none, do not invent it: 「같음. 근거 미확인」 ("same. evidence unverified").
- **Request logging in one middleware** (every request logged by the same layer): the log cell is 「같음」 with that layer's `file:line` as evidence. A log line whose wording changed outside any scenario goes in the Behavior table, not here.
- **Logs: check all three branches.** Server logs, app error reports, analytics events (GA4 etc.). A branch the project does not have at all (no error reporting, no analytics) is one line 「해당 없음. <0건인 grep>」 in the first scenario's log panel; later scenarios point to it (「시나리오 1 의 로그와 같은 근거다」). Look in the diff for logger, `captureException`, and event function calls. For a new screen, also check whether a screen view event is sent automatically (router integration, etc.); if so, 「자동 수집으로 새 화면 이름이 쌓인다」 ("the new screen name accumulates via automatic collection") is the TO-BE value. If the event name stays and only the value changes (screen name from `/+not-found` to `/settings`), put `.kd mod` on one row and place each value in the AS-IS and TO-BE cells. Write unverified values as 「추정:」 text instead of a dot.
- **Line memos (`.cm`) only for risks.** Only for what could break because of that line: rollout order, idempotency keys, validation (`.strict()` 400). The memo head `<b>` names the risk type briefly (「배포 순서」, "rollout order"). In split view the same text gathers in `.dv-notes`.
- **Panels stay short.** Send full text to the layer section. Panels show only changed cells and fold the rest (`.fold`). A panel that repeats the layer section has no purpose.

## Rail chips

- A changed cell carries short values in two chips (`.pill a`, `.pill b`), about ten characters (e.g. 「+ imageQuality」, 「정렬 3종」). The one-line rail must read as a summary.
- An unchanged cell gets a single spanning chip (`.pill m`, 「같음」).
- The marker next to the cell name is `.kd add` (+ added), `.kd del` (− removed), `.kd mod` (~ changed).
- At 420px the rail folds to three steps per row and the chips keep their text, so the text must fit about ten characters.

## Scenario head: evidence row and cutover row

The scenario head block (`.scn-meta`, id `s<number>-p7`) holds two rows. They are not in the rail and are not counted as changed cells.

- **Evidence row (change request).** The PRs and commits that changed this scenario. With a PR: PR list and commit row. Before a PR: the commit row. Before a commit: 「커밋 전」 ("not yet committed"). If all scenarios share the same evidence, or there is no PR, delete the row in every scenario; do not write a row that only points back to the summary. The same holds for the cutover row: it appears only when this scenario has an order or a breakage of its own, and the breakage in the summary's warning is not repeated. PRs and shas are written once, in that table ([document.md](document.md)); the document header does not list them.
- **Cutover row (cutover).** If there is an order to keep or a side still on the old way, add the warning marker (`.cutover.warned`) and write in one line what this scenario goes through. With two or more repos, repo lanes (`.tl`) are this row's device. Three cases: this scenario has an order or a breakage of its own, so the row says it; this scenario's only breakage is the one in the summary's warning, so the row is deleted (writing 「전환 없음」 there would be false); this scenario is not touched by any breakage, so one line 「전환 없음. <근거>」 ("no cutover. <evidence>") with the evidence that the old consumer does not send or read what changed. The step 6 compatibility table covers everything; the cutover row is this scenario's share. Deployment conditions like 「서버 PR 이 prod 에 나간 뒤」 ("after the server PR reaches prod") go in the cutover row, not the setup cell. The 「기존 데이터」 warning is not a breakage for these three cases: a scenario it touches says so in its 준비 or 결과 cell, and its cutover row is chosen as if that warning were absent.

## New feature: 「신설」

When the action is impossible in AS-IS, do not repeat 「없음」 ("none") in every cell. Every cell of a new scenario is marked added (`.kd add`, and `class="d"` on each step of the selection card's mini rail) except a cell that really is the same on both sides, such as a setup that already existed. Put one line in the scenario head: 「AS-IS: 이 행동을 할 수 없다. <근거>」 ("AS-IS: this action is not possible. <evidence>"). Write 「신설」 ("new") instead of the changed-cell count (scenario head and selection card). The rail has only TO-BE chips (`.pill b`); panels fill only the TO-BE side: `<div class="split solo">` with the `.side b` child alone. A cell that really is unchanged in a new scenario (often 로그) keeps `.pill m` 「같음」 with its evidence. If the AS-IS server already did something with the same request (e.g. accepted it and dropped the field), that is the breaking link: say it in the head line and the Behavior section, not in an AS-IS panel.

## Changed-cell count

`n/6 바뀜` ("n/6 changed") in the scenario head and the selection card. The two heads are not counted, so the max is 6. If two or fewer cells changed, add their names in parentheses (`2/6 바뀜 (준비, 응답)`). For new, 「신설」 instead of a number. `data-default` is the most important changed cell.

## Card to the right of the summary

The card is 「사용자에게 달라지는 것」, a table of user actions before and after ([document.md](document.md), "Right summary card"). The old per-step change list is gone: its lines were developer terms on the first screen, and the scenario cards and rails already show which steps change. When you refer to a scenario anywhere in running text, write 「시나리오 2」, never 「s2」.

## Old seven-cell documents

A document where the change record was the seventh cell is the previous edition of the web and app mapping. Do not migrate them all at once; migrate a document the next time you edit it. The change record was never counted, so `3/7 바뀜` becomes `3/6 바뀜` and the numerator stays. Links to `#s<n>-p7` are received by the head block with the same id.
