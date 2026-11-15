# Scenario skeleton and domain mapping table

Scenario cells are defined by questions, not by artifact names. Six questions are the skeleton, and two more questions go in the scenario head. Cell names and where to find real artifacts differ by domain, so they are split out into a mapping table. Keep one skeleton and one set of rules; a new domain adds one column to the mapping table.

Skeleton names and cell names below are the Korean labels that appear in the output document; English glosses are in parentheses.

## Skeleton

| Skeleton | Question | Industry term | Source |
|---|---|---|---|
| 전제 조건 | Who starts, in what state? | Precondition, Given | Preconditions of use cases, Given in BDD (Gherkin) |
| 트리거 | What is done or what event happens, and what is passed? | Trigger, When | Triggers of use cases, When in BDD. Gherkin's When also accepts events from other systems |
| 처리 | By what rule does the receiver return what? | Process | Process and Outputs in SIPOC |
| 접점 | What does the acting person see? | Touchpoint | Above the line of visibility in a service blueprint, the customer touchpoint in CX |
| 감사 추적 | What traces will others see later? | Audit trail | Below the line of visibility and physical evidence in a service blueprint, audit trails in information security and financial audit |
| 사후 조건 | What is different after it ends? | Postcondition, Then | Postconditions of use cases (success guarantee), Then in BDD |
| (head) 전환 계획 | From when? Who is still on the old way? Is there an order to keep? | Cutover | Cutover plans in system migration, version skew in Kubernetes KEPs, effective dates and transitional provisions in statute addenda |
| (head) 변경 요청 | What document produced the change? | Change Request | RFC in ITIL change management, change requests and notices in manufacturing engineering change management |

- Never reorder or drop any of the six cells. If one does not apply, leave it as 「해당 없음. <이유>」 ("not applicable. <reason>").
- The two heads are not placed in the rail and are not counted as changed cells.
- For changes with no human action (metric definitions, pricing plans, batches), write the event in the trigger cell. Things like 「월말 청구가 돈다」 ("month-end billing runs") or 「주간 보고서가 생성된다」 ("the weekly report is generated").
- Separate Process from Touchpoint like this. If the returned value or rule changes, Process changed. If only what the receiver reads grew, Process is 「같음」 ("same") and Touchpoint changed.
- Postcondition does not restate Touchpoint. Write only what persists afterward.

## Domain mapping table

In the output, use the cell names from this table; the skeleton name stays in the markup (`.sk`) but is not shown. For a domain not in the table, pick the words that industry actually uses and add a column.

| Skeleton | Web and app development | Business and policy | Infrastructure and operations | Data and analytics | Manufacturing |
|---|---|---|---|---|---|
| 전제 조건 | 준비 (Setup) | 적용 대상과 요건 (scope and requirements) | 현재 구성과 상태 (current configuration and state) | 대상 데이터와 기간 (target data and period) | 4M 조건 (4M conditions) |
| 트리거 | 요청 (Request) | 신청 (application) | 실행(명령, 트리거) (execution (command, trigger)) | 조회(쿼리, 필터) (lookup (query, filter)) | 자재 투입과 작업 (material input and work) |
| 처리 | 응답 (Response) | 심사와 회신 (review and reply) | 게이트와 판정(승인, 검사, 권한) (gates and verdicts (approval, check, permission)) | 지표 산식과 집계값 (metric formula and aggregates) | 공정 조건과 합부 판정 (process conditions and pass/fail verdict) |
| 접점 | 화면 (Screen) | 안내문과 서식 (notices and forms) | 콘솔과 알림 (console and alerts) | 대시보드와 보고서 (dashboards and reports) | 작업 표준서와 설비 표시 (work standards and equipment displays) |
| 감사 추적 | 로그 (Logs) | 처리 이력과 증빙 (processing history and proof) | 감사 로그와 지표 (audit logs and metrics) | 데이터 리니지와 지표 정의서 (data lineage and metric definitions) | 검사 기록과 로트 추적 이력 (inspection records and lot traceability) |
| 사후 조건 | 결과 (Outcome) | 처리 결과 (processing outcome) | 최종 상태(배포된 것, 청구액) (final state (what is deployed, billed amount)) | 내려지는 의사결정 (decisions made) | 완성품과 수율 (finished goods and yield) |
| 전환 계획 | 머지와 배포 순서 (merge and rollout order) | 시행일과 경과조치 (effective date and transitional measures) | 롤아웃과 롤백 (rollout and rollback) | 소급 재집계(백필)와 병행 표기 기간 (retroactive re-aggregation (backfill) and parallel reporting period) | 재공품 처리와 초도품 검사 (work-in-process handling and first article inspection) |
| 변경 요청 | PR 과 커밋 (PRs and commits) | 개정문과 결재 (amendment text and approval) | 변경 요청서(RFC) (change request (RFC)) | 지표 정의 변경 이력 (metric definition change history) | 설계 변경 통지(ECN)와 4M 변경 신고 (engineering change notice (ECN) and 4M change report) |

| Skeleton | Logistics | Medical and financial regulation | Education | Marketing |
|---|---|---|---|---|
| 전제 조건 | 화물 정보와 출하 조건 (cargo info and shipping conditions) | 대상자와 적용 요건 (eligible persons and requirements) | 수강 대상과 선수 과목 (target students and prerequisites) | 타깃 세그먼트와 예산 (target segment and budget) |
| 트리거 | 출고 지시 (shipping order) | 처방, 신청, 거래 (prescription, application, transaction) | 수업 활동과 과제 (class activities and assignments) | 집행(노출, 발송) (execution (impressions, sends)) |
| 처리 | 배차와 운임 산정 (dispatch and freight calculation) | 심사 기준과 승인 (review criteria and approval) | 평가 기준과 채점 (assessment criteria and grading) | 타기팅 규칙과 입찰 (targeting rules and bidding) |
| 접점 | 운송장과 배송 조회 화면 (waybill and tracking screen) | 설명서와 고지문 (explanatory documents and notices) | 강의 계획서와 교재 (syllabus and materials) | 소재와 랜딩 페이지 (creatives and landing page) |
| 감사 추적 | 배송 이력과 인수 증빙 (delivery history and proof of receipt) | 의무기록, 거래 기록, 당국 보고 (medical records, transaction records, regulatory reports) | 성적과 출결 기록 (grades and attendance records) | 성과 지표와 트래킹 (performance metrics and tracking) |
| 사후 조건 | 도착 시각과 물류비 (arrival time and logistics cost) | 급여, 지급, 승인 결과 (benefits, payment, approval outcome) | 이수와 학점 (completion and credits) | 전환 수와 획득 비용 (conversions and acquisition cost) |
| 전환 계획 | 운송 중인 화물 (cargo in transit) | 시행일, 경과조치, 기존 계약 (effective date, transitional measures, existing contracts) | 적용 학번과 시행 학기 (applicable cohorts and effective semester) | 진행 중인 캠페인 (running campaigns) |
| 변경 요청 | 운송 계약과 운영 지침 개정 (transport contract and operating guideline revisions) | 신구조문 대비표 (old/new provision comparison table) | 교육과정 개정안 (curriculum revision proposal) | 캠페인 브리프 (campaign brief) |

In marketing, 「전환 수」 means outcomes such as purchases or sign-ups (conversion), a different word from the head's 전환 계획 (cutover).

## Where the real artifacts are

Only web and app development is filled in. The other eight domains are still empty. The first time you use one of those domains, fill in where to find the real artifact for each cell.

| Skeleton | Real artifact for web and app development |
|---|---|
| 전제 조건 | Test account rules, screen scenario definitions, seeds |
| 트리거 | Fixtures in the API spec section (in order: server test fixture, OpenAPI example, recorded real call, client mock response) |
| 처리 | Fixtures in the API spec section, test expected values in the behavior section |
| 접점 | Captures in the screen section (the screenshot tool in "Project adapters" (「프로젝트 어댑터」)) |
| 감사 추적 | `git grep` diff of logger, `captureException`, and analytics event calls |
| 사후 조건 | Behavior section, data section (migrations, ORM schema) |
| 전환 계획 | Step 6 compatibility table, sha of the released version, merge and rollout order |
| 변경 요청 | `git log <base>..HEAD -- <file>`, PR list |

How to find the evidence for 「같음」 also follows from the question. Evidence that what is passed is the same is a `git grep` result in web and app development, and the version number of the application form in business and policy.

## Filled documents

Of the nine domains in the mapping table, only web and app development has been filled in with a real document. The cell names for the other domains have not yet been validated by a document.
