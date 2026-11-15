---
name: asis-tobe
description: Explains, in a single HTML page, how one change (a PR, a branch, an uncommitted working tree, a bundle of PRs across several repos, or an issue) changes each layer — data, API payload, server behavior, screen, user outcome — by placing AS-IS and TO-BE side by side and linking the layers with a causal chain. Follow this skill even when not invoked by name for Korean requests like "AS-IS TO-BE 정리해줘", "이 PR 이 화면에 뭘 바꾸는지", "서버 바꾸면 앱에 어떤 영향", "payload 가 어떻게 바뀌고 그래서 뭐가 달라지는지", "ERD 전후 비교", "변경 전후 비교 문서", "PR 본문에 전후 비교 넣어줘", or whenever a PR that changes both server and screen needs a before/after comparison for reviewers and planners before it goes up. Unlike an exhaustive risk hunt, a narrative walk through the code, or a single structure diagram, this skill produces a per-layer before/after comparison, the causality between layers, and the rollout order.
user-invocable: true
---

# AS-IS / TO-BE

Find the layers a change touches, put AS-IS and TO-BE side by side for each, and link the layers with evidence-backed arrows: "this field is dropped, so this response changes, so this disappears from (or appears on) this screen." If code changes but what the user sees stays the same, saying so is the conclusion. Do not invent changes.

## Principles

1. **Side by side.** AS-IS left, TO-BE right. Never stacked vertically.
2. **Compare real artifacts.** Payloads per 「실물 고르는 순서」 below, screens from real screenshots, schemas from real migration and model diffs. Without the real thing: 「실물 없음: <이유>」 ("no real artifact: <reason>"). Hand-made examples: 「예시(손으로 만듦)」 ("example (hand-made)").
3. **Draw only changed layers.** An unchanged layer gets 「변경 없음」 ("no change") plus one line of evidence. No empty tables.
4. **Every arrow has evidence.** A `file:line` or a commit per link of the impact path. Without evidence, mark it 「추정:」 ("estimate:").
5. **Say who still uses the old spec.** Whatever keeps running old code after this ships: app builds already in the store, browser tabs still open on the old page, other services, other call sites such as an admin tool or a bot. This decides merge and rollout order.
6. **Summary first.** The summary box at the top alone must support the decision: a one-sentence conclusion in the user's words (no field names or status codes), what changes for the user, how it ships, whether it can be rolled back; 3 items or fewer per group. Right under it, three cards answer what any reader asks next, named by the question and not by a role: 「정해야 할 것」 (what the change decided on someone's behalf), 「먼저 볼 곳」 (size, the files to open first, premises the code states), 「직접 확인하는 법」 (check items, then how to run it) — rules in [references/document.md](references/document.md) ("Question cards"). The two things a decision turns on, the badge and the rollback, are the most visible things on the first screen. Say each fact once: a sentence already in the conclusion or the warning is not repeated in the lead, the question cards, or a scenario. Everything below is evidence. Fold long payloads and exhaustive tables into `<details>`; do not delete them. No introduction, progress narrative, or closing remarks.
7. **Layout is content.** At 420px width the page must not scroll horizontally (only tables may). Body width capped at 880px; only tables and side-by-side comparisons use full width. `code` inside tables only for identifiers; only file paths and identifiers are monospace, Korean descriptions never. Sentences around 70 characters, modifiers cut. Two color schemes switched by a toggle above the title: default Dusk, beige (AS-IS) and slate blue (TO-BE); Bloom, pink (AS-IS) and mint (TO-BE). Do not follow the system dark-mode setting. Dashed and solid lines always accompany color. In-line code highlights use the light `--a-mark`, `--b-mark`, not the dark chip colors. Render once in each scheme and once at 420px.
8. **Industry terms, explained once.** Use words developers, QA, and planners understand immediately. In the Korean document use 레이어, 필드, API 스펙, 호출처, deprecated, breaking change, mock 응답, with a plain explanation in parentheses on first use only (e.g. codegen(서버 스펙으로 자동 생성한 타입 파일) — "type files auto-generated from the server spec"). For internal jargon (「AC」, made-up screen nicknames), state what it is on first use. Glossary: [references/terms.md](references/terms.md). If a term blocks you, read it there; do not skip the step.

## Layers

| Layer | What to compare | Where the real artifact comes from |
|---|---|---|
| Data (데이터) | Tables, fields, types, enums, constraints, indexes. An entity diagram of only the changed entities, and the model code | Migrations, ORM schema (prisma etc.), DDL diff |
| API spec (API 스펙) | Request and response payloads, events, codegen types. Per-field additions, removals, type changes, semantic changes | OpenAPI diff, response DTOs, test fixtures |
| Behavior (동작) | The result the server and client produce for the same input | Test assertion diff, state transition code |
| Screen (화면) | Two captures of the screen in the same state | The project's screenshot tool ([references/adapters.md](references/adapters.md), 「프로젝트 어댑터」) |
| User impact (사용자 영향) | What users can now do or no longer do, numbers that change. Includes intermediate states caused by rollout order | Issue AC, the sum of the layers above, compatibility table |

Per-layer checklists and common pitfalls: [references/layers.md](references/layers.md).

### Choosing the real artifact (실물 고르는 순서, API spec)

Server test fixture > OpenAPI example > recorded real call > client mock response. Take the first that exists in full. If a higher source is only partial (a fixture built from variables, or tests that build the request inline and assert field by field) and you recorded a real call, show the higher source in the panel and the recorded call as the full text, each labelled with its source. A recorded call carries values that differ on every run (ids, timestamps); compare such payloads with `code_diff.py --mask id,time` and say so in the source line, so a new id is not counted as a changed field. A client mock (e.g. a fake response for screenshots) is not the server's real artifact. Write the chosen source's path under the payload. If the fixture is built from variables with no full JSON, transcribe it from the test's expected values, label it 「예시(테스트 기대값에서 옮김)」 ("example (transcribed from test expectations)"), and use `…` where shortened. Do not fill in fields absent from the expected values; leave them `…`. If you borrowed a value from elsewhere (a mock response, etc.), note the source next to that field.

## Procedure

### 1. Set the scope

- PR input: get the diff **by PR number** (`gh pr diff <n> -R <repo>`). A path or branch alone gives a stacked PR main as its base and mixes in other people's changes.
- Issue input: find the PRs in each repo (`gh pr list -R <repo> --search <key> --state all`). Two or more repos go in one document.
- No PR: `git diff <base>...HEAD` in the worktree, with `<base>` the fork point, computed from the repo root (local `main` is stale and mixes in hundreds of files):
  ```
  git fetch origin main
  git merge-base origin/main HEAD
  ```
  If the diff includes files unrelated to the issue, the base is wrong. Recompute before splitting into layers.
- No remote: skip the fetch and take the base the user names, else the commit the work started from (`git merge-base main HEAD`, or `HEAD` itself for uncommitted work).
- Uncommitted working tree: AS-IS is `HEAD`, TO-BE is the working tree. `git diff HEAD` misses new files, so also read `git ls-files --others --exclude-standard`. Wherever a head sha is asked for, write 「커밋 전」 ("not committed"). Do not commit, stash, or check out to make the comparison.
- No PR or issue: the target is named by what it is (「<repo> 작업 트리 변경」, 「<branch> 브랜치」). The rollout table gets one row per unit that ships (a branch, 「작업 트리 커밋」) with the PR cell naming it; the issue key is dropped, not invented.
- Per repo, write one line `<repo> <short base sha> → <short branch sha>`. Use it verbatim in the report. In the document, PRs and shas go once in the summary card's rollout order table and the base table ([references/document.md](references/document.md)), not in the header.

### 2. Assign changed files to layers

Each file goes to one or more layers; if unclear, open it. Test files are not assigned; they are evidence for the Behavior (동작) layer. This table decides which layer sections the document gets; it is working material and is not printed in the document.

### 3. First decide whether the screen actually changes

Even if screen code changed, ask before capturing: **is the changed branch reachable with current data?** Pick one value the branch depends on and find whether the server actually produces it.

```
# Example: removed the branch where the app showed a 「품절」 (“sold out”) badge when stockState === 'SOLD_OUT'
git -C <server repo> grep -n "SOLD_OUT" -- <source files>      # does the server put this value in a response anywhere?
git -C <app repo> grep -n "stockState" -- <generated types>   # values the generated type allows
```

No server code setting the value (only type or enum definitions) means unreachable, even if the generated type allows it. Record the `file:line` as the evidence for 「변경 없음」.

If only the place that computes a value moves (e.g. the server's `ERROR` is now computed by the app as `lastError`), put both formulas side by side with their `file:line`. Same value for the same input: same screen. Different: find one input that yields a different value and capture that state.

- Reachable: capture in step 4.
- Unreachable: the Screen layer gets 「현재 데이터로는 변경 없음: <이유와 근거>」 ("no change with current data: <reason and evidence>"). Record the vanished state under 「실물 없음」 and show its old appearance via the test strings whose assertions checked that state. If confirmation is needed, capture one representative scenario and show sameness with md5.
- Unsure: capture.

### 4. Collect real artifacts per layer

- **Data**: three parts, in this order.
  1. **Entity diagram**, open. Only the changed entities and the ones directly attached, 6 or fewer per side. Write them as JSON and let the script draw both sides as inline SVG: `python3 -I ~/.claude/skills/asis-tobe/scripts/erd.py <spec.json>` (the spec format is in the script's header). Never draw the SVG by hand and never load a diagram library; the page is self-contained. The script marks added, removed, and changed fields and entities itself by comparing the two sides, so write each side as it really is at that commit.
  2. **Model code**, folded (`<details>`): the model as the code holds it (struct, class, ORM schema) at the base and now. One line diff per model from `python3 -I ~/.claude/skills/asis-tobe/scripts/code_diff.py <ASIS.txt> <TOBE.txt> --label "<name (path)>" --start-a <line> --start-b <line>`; a new or removed model uses `/dev/null` for the missing side. The script computes the changed lines and prints both views (나란히 side by side, 합쳐서 unified) for the reader to switch; never mark lines by hand.
  3. **Field table**, folded: what the diagram leaves out (defaults, constraints, indexes, handling of existing rows).
  A single changed field with no relation involved needs no diagram: one row in the field table, shown open. If AS-IS had no stored schema (in memory, a file), give only `tobe` to the script with `asis_note` saying where the data lived (`file:line`); the model code is then the AS-IS evidence, so leave that `<details>` open. The migration that creates the first tables is TO-BE. If this cleans up after an already-shipped migration, 「이미 반영(<PR>)」 ("already applied (<PR>)") is the first link of the impact path.
- **API spec**: the payload before and after as a line diff from `scripts/code_diff.py` (same script as the model code; one call per payload, `--context 3` for long ones, `--mask id,time` for recorded calls). Below it, `필드 | AS-IS | TO-BE | 시맨틱 변경` (field | AS-IS | TO-BE | semantic change). A name- or type-only change merges both cells into one line: `<code class="old">start_time</code> → <code class="new">starts_at</code>`. Call sites:
  - `git grep <field>` in each repo, **from the repo root** (a subdirectory makes paths relative and returns 0 hits).
  - **Also on the released version**: `git grep -n <field> <sha>`. Its result decides merge and rollout order and the badge. **Read [references/adapters.md](references/adapters.md) ("Finding the released version") before doing this.** Musts: only a sha from the build list is confirmed, others are 「추정:」; if sources disagree, grep every sha and count any hit as 「배포된 앱이 읽는다」 ("the released app reads it"); never choose by tag name alone (tags may belong to another deployable in the same repo). Lightweight fallback when the build list fails (e.g. no login to the build service): shas from the issue or release notes, else a 「추정:」 lower bound.
  - Codegen output is not a call site; it is regenerated from the server spec. Note separately 「다시 뽑으면 무엇이 바뀌나」 ("what changes if regenerated").
  - Also `git grep` the removed field in the client's mock responses and test fixtures. If it remains, typecheck may break once codegen is regenerated after the server ships. List those files as the last rollout step (「codegen 재생성과 fixture 정리」, "regenerate codegen and clean up fixtures").
- **Behavior**: `입력·상태 | AS-IS | TO-BE | 근거(테스트 이름)` (input/state | AS-IS | TO-BE | evidence (test name)).
- **Screen**: **read [references/screens.md](references/screens.md) ("Capture") before capturing.** Same scenario, data, one language, and size on both sides, in one temporary worktree (base for AS-IS, branch for TO-BE) or, for uncommitted work or a repo you must not touch, in two copies outside the repo; installs and captures in the background, md5 compared, then, once step 10 has re-measured what it needs, stop the servers and remove the temporary worktree or copies (keep them if the user wants the run reproducible); never commit them. With no mock capture tool, run each version's real server on its own port and capture that. Capture commands per project: [references/adapters.md](references/adapters.md). Skip capturing only when the platform cannot be captured (e.g. native) or step 3 found the branch unreachable; then 「실물 없음: <이유>」 plus test assertion strings. If unsure, capture.

### 4b. Fill the scenario rail

**Read [references/scenario-rail.md](references/scenario-rail.md) before filling 「시나리오별 전후」.** Cell names for other domains: [references/domains.md](references/domains.md).

| Skeleton | Web/app cell | Device |
|---|---|---|
| 전제 조건 (Precondition) | 준비 (Setup) | `.split` |
| 트리거 (Trigger) | 요청 (Request) | `.dv` line diff, `.cm` memos |
| 처리 (Process) | 응답 (Response) | field table, one branch |
| 접점 (Touchpoint) | 화면 (Screen) | `.split`; captures in `.stage` |
| 감사 추적 (Audit trail) | 로그 (Logs) | `.logrow` ●/○ |
| 사후 조건 (Postcondition) | 결과 (Outcome) | `.split`; `.cost` bars for numbers |
| (head) 변경 요청 (Change Request) | PRs and commits | `.prs`, `.commits` |
| (head) 전환 계획 (Cutover) | Merge and rollout order | cutover row, `.tl` lanes |

Must-follow:
- Scenario = one thing one actor (user, operator, or system) goes through once, or one event; about 3, one per issue AC by default (no issue: one per thing a user can newly do or does differently, taken from the diff; with more candidates than three, take first the ones that break an old consumer, then the ones that change stored data, and list the rest only in the user impact table); split a scenario when the same action differs by width or platform. Ids `s1`, `s2`; panels `s<number>-p<step>`; head `s<number>-p7`.
- Never reorder or drop any of the six cells. The two heads sit in the scenario head (`.scn-meta`), outside the rail, and are not counted.
- 「같음」 always has evidence; if none was found, 「같음. 근거 미확인」. Not applicable: 「해당 없음. <이유>」.
- Changed-cell count `n/6 바뀜`; new feature: 「신설」 with TO-BE-only chips and one head line 「AS-IS: 이 행동을 할 수 없다. <근거>」 instead of repeating 「없음」 in every cell.
- Chip text is about ten characters; at 420px the rail folds to three steps per row and the chips keep their text.
- English edition: output labels come from the fixed-strings comment in [references/template.html](references/template.html).

### 5. Link the impact path

One line at a time, in layer-table order. Each line starts with what the previous line ended on (the field, call, or screen the reader just met) and ends with the new fact; the reader reads the end of a line as its point (Gopen and Swan, "The Science of Scientific Writing", topic and stress positions). The same holds for scenario cells and `.lead` lines: put the consequence at the end of the sentence, not in a trailing clause after it. A hypothetical example of the format:

```
[데이터] orders.status enum 에 PARTIALLY_REFUNDED 추가 (migrations/20261101_x.sql)
  → [API 스펙] GET /orders/{id} 의 status 가 새 값을 낼 수 있다 (openapi.yaml +1줄)
  → [화면] 주문 상세 배지에 「부분 환불」 (order-badge.tsx:40)
  → [사용자] 부분 환불 주문이 「환불 완료」로 잘못 보이지 않는다
```

English gloss (the Korean document keeps the Korean form):

```
[Data] add PARTIALLY_REFUNDED to the orders.status enum (migrations/20261101_x.sql)
  → [API spec] status of GET /orders/{id} can return the new value (openapi.yaml +1 line)
  → [Screen] order detail badge shows “partially refunded” (order-badge.tsx:40)
  → [User] partially refunded orders no longer wrongly appear as “refund complete”
```

Branches get separate lines. If the screen does not change, the path ends at API spec or Behavior, and user impact comes from the compatibility table.

In HTML, use the template's `.chain` nodes: a layer tag (`<b>`), a one-sentence claim (`.claim`, preceded by a change marker, followed by repo and module `.where`), and evidence rows (`.ev`).
- **Subtract first.** Consecutive nodes in the same repo and layer merge into one node with multiple evidence rows. 7 nodes or fewer; if more, split by repo.
- **1–2 focal points.** `.focal` (filled tag) only on the breaking link or the result the user sees.
- **Boundaries by line style.** `.cross` (dashed) when the next node crosses a repo or network boundary.
- **Changes by symbol.** `.kd add` (+ added), `.kd del` (− removed), `.kd mod` (~ changed); never color alone. Pass-through nodes get no marker.

### 6. Compatibility and merge/rollout order

`호출처 | 깨질 수 있나(예/순서를 어기면/새로고침 전까지/아니오) | 구 스펙 사용(근거) | breaking 조건 | 안전해지는 시점` (call site | can it break (yes / if order is violated / until refreshed / no) | uses old spec (evidence) | breaking condition | when it becomes safe). Cover only call sites already found; exhaustive risk hunting is a separate review, not this document.

One summary badge, the worst case: `.brk yes` (breaking change: an old call site stays broken whatever order you ship in, and nothing short of replacing that call site fixes it) > `.brk ord` (「배포 순서를 어기면 깨짐」, "breaks if rollout order is violated": there is an order of merges and deploys that avoids the breakage) > `.brk upd` (「새로고침 전까지 깨짐」, "broken until refreshed": no order avoids it and none is needed; an old consumer already running is broken only until it is refreshed by itself or by its user, such as a browser tab reloaded after the deploy; the badge names what refreshes it, 「재시작 전까지 깨짐」 for a client process, 「업데이트 전까지 깨짐」 for an installed app) > `.brk no` (「호환」, "compatible": breaks in no order). Keep it consistent with the 「깨질 수 있나」 ("can it break") column values (예, 순서를 어기면, 새로고침 전까지, 아니오). Two more values do not count toward the badge: 「해당 없음」 for the row 「배포된 버전: 없음」, and 「확인하지 못함」 for call sites you could not look at. The template badge is a `{{yes|ord|upd|no}}` placeholder with no default; it remains if you do not choose.

- A released consumer (step 4) reads a field being removed or changed: `ord` or worse (server first breaks that consumer).
- The request side counts as much as the response side. A request the old consumer sends that the new server rejects (a field became required, validation got stricter, an endpoint was removed) or answers with a different meaning (the same body now does something else) breaks that consumer: `upd` or worse. List the requests the old consumer sends (`git grep` the calls on the AS-IS sha) next to what the new server requires.
- The next three lines are for installed apps (mobile, desktop); skip them for a web page the server itself serves. There the old consumer is a browser tab opened before the deploy: always add a row 「열려 있던 AS-IS 화면」 with what that page reads and sends (`git grep` on the AS-IS sha) and whether each still works. If something breaks only until the tab is reloaded, the row says 「새로고침 전까지」 with 「새로고침하면 풀린다」 as the safe point, the badge is `upd` (unless another row is worse), and the warning block, labelled 「새로고침 전까지」, says who sees what until they reload.
- If keeping the order still cannot prevent it, `yes` (legacy builds stay on phones until users update):
  - Forced update can raise the minimum version: `ord`, and add 「최소 버전 올리기」 ("raise the minimum version") to the order.
  - No forced update: `yes`.
  - Mechanism exists but blocking is unknown: `yes`, marked 「추정:」, stating what confirmation would make it `ord`.

  Check blocking two ways: (1) `git grep` the mechanism's files at the released sha from step 4; (2) see in code what the mechanism compares versions by, and put that value for legacy and new builds side by side; equal values cannot be separated. Example: [references/adapters.md](references/adapters.md) ("Minimum version example").
- `no` only when no released version reads the field, with the step 4 `git grep` result (0 hits) as evidence.
- Nothing was ever released (no remote, tag, deploy workflow, or build list; state which you checked): write the row 「배포된 버전: 없음. <확인한 것>」. The badge then rests on the call sites inside the repo: `no` only if no existing response field is removed or retyped and no request the old page sends is rejected or changes meaning. A consumer that ships in the same unit as the server (e.g. a page embedded in the server binary) rules out a half-deployed state, not a tab that was already open. Callers outside the repo are 「확인하지 못함」.
- Shipping itself loses or hides data users already have, with no spec change behind it (AS-IS kept its data in memory and the deploy restarts it, a cache or queue is emptied, existing rows are not carried over): this is not a compatibility break when restarting AS-IS by itself ends the same way, so the badge stays where the spec puts it and an old page's request that fails only because its record is gone is a 「아니오」 row that says so. It is still the first thing the reader must know: write it in a `.warn` block labelled 「기존 데이터」, whatever the badge.

`yes`, `ord`, or `upd`: write that one breakage in a `.warn` block directly under the summary conclusion (rules in [references/document.md](references/document.md)). State whether it can be undone: after this ships and its migration has run, can the previous version run again on the same data? 「가능」 means the previous version starts on the data as it is after shipping and shows what users wrote since. A previous version that starts but cannot see that data (it never opens the new store) is 「불가」, and the body says the data stays intact and returns when this version is put back. Read the migration (a rebuilt table, a dropped column, converted values, and no down migration mean no) and, when you ran both versions, open a copy of the migrated data with the AS-IS binary and see whether it starts and reads. Write the result in the summary's rollback block, labelled 「되돌리기 가능」, 「되돌리기 불가」, or 「되돌리기 확인하지 못함」, in plain words: what going back means and what the way back is (a backup taken before the deploy), with the error text after it.

Then number the merge and rollout order: per PR 「즉시 머지 가능」 ("ready to merge") or 「<조건> 뒤」 ("after <condition>"), plus one line on the partial rollout state.

### 7. Mark the changed spots on screens

**Read [references/screens.md](references/screens.md) ("Stage layout", "Boxes") before this step.** Every screenshot pair gets boxes on the changed spots; never leave just the picture. Coordinates: `python3 -I ~/.claude/skills/asis-tobe/scripts/diff_boxes.py <ASIS.png> <TOBE.png>` (same scenario, same viewport width). One side only or no capture: `.stage.solo` or `<p class="missing">`, no script.

Gate, run for every document, with or without screen pairs:

```
NODE_PATH=<node_modules containing puppeteer-core> node ~/.claude/skills/asis-tobe/scripts/render_check.mjs <doc.html> <out-dir>
```

`NODE_PATH` is a `node_modules` that contains `puppeteer-core` (the script drives the system Chrome); the project's adapter note names it ([references/adapters.md](references/adapters.md)). The output also reports `foldedHeight`, the page height at 1280px before anything is opened: past about 3,000px times the number of scenarios plus one (the summary and the layer sections count as one more), fold more or drop a stage that repeats another. If everything still open is something a rule keeps open, leave it and say so in the report. Finish only when `outside` (boxes or their numbers outside the image in that `.shot`), `overflowX` (horizontal scroll at that width), and `consoleErrors` (script error or broken image path) are all empty arrays. Then open `render.pair<N>.png`: if a box border touches text, widen it; if a number covers text, hang it outside with `out` ([references/screens.md](references/screens.md)).

### 8. Produce per language

- Output language follows the request; unspecified means a single Korean document. Two or more languages: one file each (`asis-tobe.ko.html`, `asis-tobe.en.html`).
- Capture screenshots in that edition's locale; no en screens in the ko edition. On-screen text quoted in callouts is that language's actual screen text.
- Follow that language's editing procedure in [references/terms.md](references/terms.md). The English edition is rewritten as English technical writing, not translated.
- Gate per edition: `python3 -I ~/.claude/skills/asis-tobe/scripts/text_lint.py <doc.html>`; fix modifiers, long sentences, long parentheticals, overused emphasis, mixed terms for one concept (`term-mix`), translationese (`transl`, ko only), and Hangul left in the English edition. Criteria: 「줄바꿈과 꾸밈말」 ("Line breaks and modifiers") in [references/terms.md](references/terms.md). `cell` and `dense` findings map to rules in [references/document.md](references/document.md).
- Cross-check editions: number of summary items, order steps, table rows, box numbers.

### 9. Produce the document

- **Read [references/document.md](references/document.md) before filling [references/template.html](references/template.html).** Replace every `{{…}}` placeholder; keep Korean fixed labels in a Korean edition and swap them for en strings in an English one.
- Save location: the project's documentation rules or its adapter note if any (e.g. `docs/<repo>/<YYYYMMDD>_<slug>/asis-tobe.html` plus an index update). Otherwise `~/Downloads/asis-tobe-<slug>.html`. Report the absolute path.
- **One file.** The document is shared as a single HTML file, so its screenshots live inside it. Write `<img>` with the capture's file path while you work, then run `python3 -I ~/.claude/skills/asis-tobe/scripts/inline_images.py <doc.html>` once the screenshots are final and before the gates of steps 7 and 8; it turns every local image into a data URI and reports the size. Keep the PNG files only in your working folder (the markdown edition needs them); do not leave an image folder next to the document.
- On request, a markdown edition for the PR body (see document.md).

### 10. Verify the facts before reporting

A document that passes `text_lint` and `render_check` can still state a wrong sha, count, or boundary; those gates do not read facts. Check your own draft the way Chain-of-Verification does (Dhuliawala et al., arXiv 2309.11495): list the checkable claims, answer each one again from the source without looking at the draft, then fix the draft where the two differ.

1. **List the claims.** From the summary cards, the warning block, the rollout table, and the compatibility table, collect every claim that is one of: a sha or PR number, a count (「+13줄」, 「6개 빌드 중 3개」), a time, a boundary (「<sha> 이후 빌드부터」, 「1.0.1 부터」), a 「0건」 / 「같음」 / 「읽지 않는다」, a quoted test name or on-screen text. Usually 10 to 20 claims.
2. **Re-run, do not recall.** For each claim run the command that produces it again (`gh pr view`, `gh pr diff --stat`, `git show <sha>:<path>`, `git grep -n <field> <sha>`; with no PR, `git diff --stat <base>`, `git ls-files --others`) and read the output. A claim you measured by running the software (a response, a row count, a restart) is measured again, after confirming what you measured is what you name: the process listening on the port (its PID: `lsof -nP -iTCP:<port> -sTCP:LISTEN`), that binary's checksum, and the data store it has open (`lsof -p <PID>`). A server you thought you stopped answers with old data and looks like a finding. Requests that write change what you measure: re-measure against a fresh copy of the data taken before the first measurement, not the store the first run already wrote to. Notes and memory from earlier steps are not evidence here: the wrong value is usually already in them. A 「0건」 needs a search that ran: check the command's exit status and quote its pattern, because a search that failed (a shell glob error, a wrong path) prints nothing too.
3. **Boundaries need both sides.** 「<sha> 부터 그린다」 is confirmed only by two outputs: the first sha that does it and the build just before it that does not. With N released builds, record the result per build (a row each), not a summary sentence written from memory. An unverified boundary is 「추정:」.
4. **Follow each newly written value to its other readers.** For every value this change starts writing or stops writing, find the flows that copy, restore, revert, duplicate, export, or delete the owning record, starting from the entry points (routes, commands, jobs) since the words alone match unrelated code (a `restore` constructor, a `Duplicate` error), and state in one line whether each carries the value (e.g. 「버전 되돌리기는 이 필드를 되돌리지 않는다. <file:line>」). A project with no such flow at all gets one line saying so with the 0-hit grep. These lines go in a short list (`<ul>`) at the end of the Data section, one flow per item. Not found in the time available: 「확인하지 못함」, not silence.
5. **Stacked PRs.** If a PR's base is another PR's branch, the rollout table says which PR must merge first and into what, even when it is already merged.
6. **Fix and re-gate.** Correct the document, then rerun step 8's `text_lint` and step 7's `render_check`. Fast path: a change with no released consumer, no counts, and one repo usually has under five claims; check them and move on.

## Report (보고)

```
AS-IS/TO-BE: <대상>
  <repo> <기준> → <브랜치>
  <repo> <기준> → <브랜치>
바뀐 레이어: … / 변경 없음: <레이어>(<근거>)
문서: <절대 경로>
실물 없는 항목: <있으면 무엇과 이유>
배포 순서: 1. … 2. …
검증: 다시 돌린 주장 <n>건, 고친 것 <n>건(<무엇>)
```

Field names are literal and stay in Korean: `AS-IS/TO-BE:` (target), `바뀐 레이어:` (changed layers), `변경 없음:` (unchanged), `문서:` (document), `실물 없는 항목:` (items without a real artifact), `배포 순서:` (rollout order), `검증:` (step 10: how many claims you re-ran and what you corrected; if you did not re-run, write 「검증: 다시 돌리지 않음」 and why). Placeholders: <대상> target, <기준> base, <브랜치> branch, <레이어> layer, <근거> evidence, <절대 경로> absolute path, <있으면 무엇과 이유> what and why, if any. Values follow the conversation language.

## What not to do

- Do not fabricate a plausible payload or screen without a real artifact and present it as TO-BE.
- Do not hunt risk beyond the compatibility table. The 「먼저 볼 곳」 card points at where the change is heavy and quotes premises the code states; it does not audit them. Note an unintended change you notice in the 「의도 밖 변경」 ("unintended changes") section and stop there.
- Do not modify code.
- No confidential data (e.g. customer records, real users' personal information) in examples. Use fixture values.

## Project adapters

Where a project's screenshot commands, generated-code paths, released-version lookups, and PR image branches come from (the project's adapter note, else found in the repo), with recipes for EAS apps and hand-deployed web: [references/adapters.md](references/adapters.md).
