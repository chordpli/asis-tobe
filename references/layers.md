# Per-layer checklist

## Data

- Check separately: field addition, removal, rename, type change, nullable change, default value, enum values, unique, FK, index.
- If the migration is not in this PR and has already shipped, write 「이미 반영(<커밋·PR>)」 ("already applied (<commit/PR>)") and take AS-IS as the state after it. If this PR is its cleanup, that fact is the first link of the impact path.
- If there is a data backfill or handling of existing rows, add a 「기존 행」 ("existing rows") row to the Behavior layer.
- The entity diagram (`scripts/erd.py`) covers the changed entities plus directly attached entities, 6 or fewer per side. Past that, keep the changed ones and their nearest neighbours, and say in the `.src` line which were left out.
- The diagram takes names, types, keys, and nullability from the migration or schema at each commit, not from memory. A rename shows as a removal and an addition; say it is a rename in the field table.
- If AS-IS kept the data in memory or in a file, there is no AS-IS schema: put the in-memory model (`file:line`) on the AS-IS side and say what is lost on restart. A first migration that only writes down that model is still TO-BE.

## API spec

- The 「시맨틱 변경」 ("semantic change") column of the field table is the core. Even if name and type are the same, if what the value means changes (e.g. a value the server computed and sent becomes a directly stored value), record it here.
- If an enum narrows, point out in the call site table the side that sent old values; if it widens, the side that receives unknown values.
- If request validation (.strict, required fields) changes, add a 「옛 요청을 보내면」 ("if an old request is sent") row to the Behavior layer.
- Codegen is generated code, regenerated from the server spec. Do not count it as a call site; note separately 「다시 뽑으면 무엇이 바뀌나」 ("what changes if regenerated").
- Events, webhooks, and queue messages are API specs too. Do not look only at HTTP.

## Behavior

- Lines in the test diff where assertions changed are the behavior changes. Use test names as row names.
- Record only 「같은 입력, 다른 결과」 ("same input, different result"). If a refactor yields the same result, 「변경 없음」 ("no change").

## Screen

- Before capturing, check whether the changed branch is reached with current data. If a removed branch only ran on a value the server already no longer sends, the current screen is the same. Then one representative scenario showing sameness is enough to capture.
- Capture with the same screen scenario, same data, same language, same size. If they differ, it is not a comparison.
- If several states changed (normal, error, empty), one row per state.
- Note that web-captured screens do not reflect font scaling.
- Point out the changed spot in the screenshot in one line of text (「카드 제목 끝의 「품절」 배지가 사라졌다」, "the sold-out badge at the end of the card title is gone"). Never leave just the picture.

## User impact

- Do not copy the issue AC verbatim. Rewrite in terms of what the user sees, taps, and learns.
- If numbers change, such as operational metrics or billing, state in which direction and by how much (if known).

## Common pitfalls

- If you take main as the base of a stacked PR, other people's changes mix into AS-IS and TO-BE. Get the diff by PR number.
- Do not judge "no change" from stale dist or codegen. Look at the source and schema diff, not build output.
- Do not leave old clients out of the call sites. Whenever you change a public response, include a row for the code already in users' hands and run `git grep` on its sha: 「스토어 배포 빌드」 ("store release build") for an installed app, 「열려 있던 AS-IS 화면」 ("an AS-IS page still open") for a web page. A working-tree grep cannot see the released version. If nothing was ever released, the row says so with what you checked.
- Do not assume the screen changed because the code changed. Check reachability before capturing, and if captured, confirm sameness with md5.
- Also record the intermediate state when the server PR and the app PR merge in reverse order. Add one line 「A 만 배포된 상태」 ("state with only A deployed") to the rollout order section.
