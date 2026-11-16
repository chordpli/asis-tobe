# Project adapters (프로젝트 어댑터)

Read this before capturing screens (step 4), looking up the released version (step 4), deciding the badge (step 6), and attaching PR images (step 9).

The skill carries no project's commands. Each project's commands come from an adapter note the project keeps, or you find them in the repo.

## Adapter note

A project that uses this skill often keeps a note with its own commands. Look for it in this order and read the first one found:

1. `<repo>/.claude/asis-tobe.md`
2. `.claude/asis-tobe.md` in the folder that holds the repos (a multi-repo workspace)
3. `~/.claude/asis-tobe-adapters/*.md` whose first line `repos:` names this repo

The note answers, per repo, the five questions below. Where it is silent or missing, find the answer in the repo (next section). In the report, list the commands you had to find yourself so the user can save them in a note.

| Question | Used in |
|---|---|
| How is a screen captured (command, scenario ids; mock responses or a real server)? | step 4, step 7 |
| Where are the API spec, response types, and fixtures? Which paths are generated code? | step 3, step 4 |
| How is the released version found (build list command, deploy workflow, or by hand)? | step 4, step 6 |
| Where is `puppeteer-core` installed (`NODE_PATH` for `render_check.mjs`)? | step 7 |
| Where do PR images go (branch or upload), and where is the document saved? | step 9, Output |

Note format, one block per repo:

```
repos: <repo-a>, <repo-b>

## <repo-a>
- Screen: <command>
- API spec: <paths>; generated: <paths>
- Released version: <command or "main deploys on merge" or "deployed by hand: <how to find the time>">
- NODE_PATH: <path>
- PR images: <branch or "none">
- Save location: <path pattern>
```

## Finding the answers without a note

- **Screen.** Look for a screenshot or visual-test script in `package.json` scripts, a Storybook, Playwright or Maestro scenarios, or an existing screenshot skill in the project. Prefer one that runs on mock responses; if the project has none, run the real server ([screens.md](screens.md), "No mock capture tool"). Failed scenarios often leave no image, so capture an AS-IS that has no entry point with a scenario that stops at the preceding state. For the base commit use a separate worktree (`git worktree add <path> <sha>`), then install dependencies there. No way to capture: 「실물 없음: <이유>」.
- **API spec.** OpenAPI or GraphQL schema files, response DTOs, and test fixtures. Generated clients (a `codegen` or `generated` folder, a header saying "do not edit") are not call sites.
- **`NODE_PATH`.** Any `node_modules` that contains `puppeteer-core` (`find . ~/.npm/_npx -path '*/node_modules/puppeteer-core' -maxdepth 6`). The script also needs Google Chrome installed.
- **PR images.** Ask the project's convention; if none, do not push images anywhere without the user's confirmation.

## Finding the released version (all projects)

`git grep -n <field> <sha>` on the released sha checks whether the code currently in users' hands reads the field. Its result decides merge and rollout order. Do it in order.

1. Find the sha. Look at the build list (recipes below), the shas written in the issue body and release notes, and the lower bound in item 3, in that order. Only a sha found in the build list is confirmed; mark the rest 「추정:」. If you do not know which build went to the store, or the sources disagree on the sha, do not pick one: `git grep` every sha you found, and if any of them reads the field, count it as 「배포된 앱이 읽는다」 ("the released app reads it"). Do not choose by tag name alone: a repo's tags may belong to another deployable (a landing site, an admin) in the same repo.
2. For call sites that deploy main automatically on merge, main is the released version: `git grep -n <field> origin/main`. Check that this is true first (a deploy workflow that runs on push to main). A web app deployed by hand is not main: the merge time is only the earliest possible release, so find the deploy time (recipe below) or write 「확인하지 못함」.
3. If you cannot find any, use a lower bound. Example: the last main commit before the store submission date.
4. If there is OTA (a deploy that changes only JS without store review), record the binary sha and the JS sha separately.
5. If nothing was ever released (no remote, no tag, no deploy workflow, no build list), there is no sha to grep. Write 「배포된 버전: 없음」 with what you checked, and decide the badge from the call sites inside the repo (SKILL.md step 6).
6. If a release exists but you do not know the sha, ask the user in an interactive session. If you cannot ask (e.g. as a subagent), leave an estimate with evidence and proceed.

### Recipe: Expo app built with EAS

Run from the app folder (the one with `eas.json`):

```
eas build:list --platform ios --status finished --limit 10 --json --non-interactive | jq -r '.[] | select(.buildProfile=="production") | .appVersion + " " + .gitCommitHash'
```

- Keep only the store profile. Debug or preview profiles are not store builds.
- A finished build is not necessarily in the store, so match which build passed review against the issue or release notes.
- `eas` is the command of the `eas-cli` package, installed in the project or globally. If it is not installed, say so and move on to the fallback below; do not download it on the fly.
- It requires an EAS login. If it fails, move on to the issue or release notes (lightweight fallback), then to a 「추정:」 lower bound.
- The `--json` output includes long log URLs and runs to tens of thousands of characters, so always filter with `jq`.
- macOS has no `timeout`, so do not use it.
- OTA updates are the commits from `eas update:list --branch <production branch> --json --non-interactive`.

Other mobile pipelines (fastlane, Xcode Cloud, Play Console): the store build's commit is in the pipeline's build list or the release tag; the same rules about confirmed and 「추정:」 apply.

### Recipe: web app deployed by hand

No deploy workflow on push to main, and a deploy command in a Makefile or README, means the web is deployed by hand. Then main is not the released web.

- The deploy time is the `last-modified` header of the served bundle (`curl -sI` on the bundle URL taken from the page source).
- Compare it with the server's production deploy time to say whether the web was live before the server.
- Look for a commit sha in the bundle (an error-reporting release id, a version file). If there is none, write 「배포된 웹의 커밋: 확인하지 못함」 and give the `last-modified` time.

### Recipe: server deployed on merge

Confirm a workflow deploys on push to main, then take the deploy run's finish time (`gh run list --workflow <deploy workflow> --branch main`), not the merge time, when the order against a client matters.

## Minimum version example (step 6, installed apps only)

A forced-update mechanism that compares the app display version as semver cannot separate two builds that share a display version. If every released build is `1.0.1`, raising the minimum version does nothing. Only by shipping the new build as `1.0.2` and raising the minimum version to `1.0.2` does the badge become `ord`. Put both into the order.
