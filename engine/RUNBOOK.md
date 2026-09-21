# Invisible Rules — TikTok Daily Runbook (IR-* pipeline)

Account: TikTok @invisiblerulesmedia ("Invisible Rules"). Public content in ENGLISH. Messages to the owner (Silver) in short, simple Levantine Arabic.

## Roles (two sessions, one pipeline)
- PRODUCER/HOST = the session that can write to mahmodmaho077-dev/tiktok-media-public (this repository). It runs this runbook once per day at 06:00 UTC: research, script, render, QA, host with engine/bridge.py, update ledger/videos.json, commit and push. It is the only place that creates IR ids.
- METRICOOL: if this session has the Metricool MCP tools, it also schedules (steps 6-7 of the daily cycle). If it does not, it stops at status "hosted": a separate Cowork scheduler reads ledger/videos.json from raw.githubusercontent.com every day at 14:00 UTC and schedules the oldest "hosted" item for 18:00 Europe/Athens.
- Both sides check Metricool for the IR id before creating a post, so an item can never be posted twice. Never re-render or re-host an id whose status is hosted, scheduled or published.

## Locked niche (do not reinterpret)
Forensic company/business case studies revealing a hidden business mechanism behind a specific verified decision, number, pricing move, margin, contract, cash-flow structure, distribution advantage, unit economics, customer economics, incentive, or capital-allocation decision. Every video is about a concrete named company.
Reject: psychology/self-development, generic motivation, generic finance tips, investing advice, celebrity content, random news, politics, broad economics explainers, shallow "how X makes money" summaries, stories without a specific hidden mechanism.
Internal test (must be supported by sources fetched in the same run, else reject the topic):
"[Company] did [specific verified action], which changed [business/money outcome] because [hidden mechanism]."

## Media rule
The only media that may be hosted or posted is an MP4 rendered by this engine for an IR-XXX id, from a story JSON written for that id. engine/bridge.py refuses everything else.

## Accuracy
- Every number, date, name and quote on screen or in the voice comes from a page fetched in the same run. Prefer SEC/company filings, investor relations, earnings materials, official pricing pages, court/regulatory documents, reputable business reporting.
- On-screen quotes are verbatim ("…" for cuts). Attribute claims made by interested parties. Put the year on screen so old stories are not presented as news.
- Never invent numbers, dates, quotes, motives or causal claims. Drop anything that cannot be verified.

## Quality Gate
Score 0-10 each: Novelty, Specificity, Curiosity, Clarity, Emotional tension, Intellectual value, Retention potential, Niche fit, Source evidence, Difference from previous posts.
Produce only if total >= 85 AND Niche fit >= 8, Source evidence >= 8, Clarity >= 6, Difference >= 6. Justify every score >= 8 in one line. Do not inflate. Log every rejected candidate in the ledger with its reason.

## Novelty and duplicate prevention
- Research at least 4 candidate company cases per run.
- Reject the same company + mechanism combination and any semantic duplicate of a ledger item (published, scheduled, queued, rejected, hold, legacy). Rewording does not make an idea new.
- Not the same industry as either of the last 2 items, nor the same mechanism_family as the last one.
- Before scheduling, check the ledger AND Metricool getScheduledPosts (30 days back to 30 days ahead, extendedRange true) for the IR id (first comment starts with it) or the media URL. If either exists, do not create another post.

## Script
- 30-45 s, 90-115 words, 6-8 scenes. Quality reference: IR-004 (engine/example_story.json).
- Scene 1 (first 1-2 s): the company/product and the unusual verified fact, on screen and in the voice.
- Scene 2 raises the question the video answers. Last scene: type "rule", one or two short sentences stating the business mechanism.
- Spell out every number in "vo" (the engine rejects digits); captions show numerals.
- Read phonemes.txt and fix mispronounced names with "phoneme_fixes" (e.g. {"lʌfθˈænsəz": "lˈʊfthɑːnzəz"}).

## Packaging (every post)
- tiktok_title: factual, curiosity-driven, names the company.
- Caption: 1-2 sentences that add context beyond the narration.
- 3-5 relevant hashtags, including company/topic tags. #BusinessModels #BusinessStrategy #CorporateStrategy #Economics only when genuinely relevant. Never #fyp or unrelated reach-bait.
- First comment: "IR-XXX · Sources: ..." — max 150 characters (TikTok comment limit): short source names only. Full source URLs go in the ledger.

## Engine
Files: engine/setup.sh, engine/make_video.py, engine/template.html, engine/avatar.png, engine/example_story.json, engine/bridge.py.
1. bash engine/setup.sh   (fonts + local Kokoro TTS model from npm/PyPI; voice af_heart; no paid TTS)
2. Write videos/IR-XXX.json with the structure of engine/example_story.json.
3. python3 engine/make_video.py videos/IR-XXX.json --check    -> fix every ERROR
4. python3 engine/make_video.py videos/IR-XXX.json --preview  -> inspect videos/IR-XXX/preview.png: no overlaps, no clipped text, nothing important in the bottom 22% of the frame or the right 130 px below y=900, emphasis on the right words, every on-screen fact matches the sources. Max 3 rounds.
5. python3 engine/make_video.py videos/IR-XXX.json --full     -> inspect videos/IR-XXX/check.png

Scene types (visual.type):
- hero {tag, big, big_red?, big_size?, count?, sub?, sub_size?, note?, board?, top?}
- quote {tag, quote, who, size?}
- list {tag, headline, head_size?, items[{text, at_caption}], source?}
- bars {tag, headline, source?, bars[{label, value, display, red?, at_caption}]}
- progress {tag, headline, label, threshold, threshold_label, fill, result, result_at_caption, note?}
- versus {tag, headline, left, right, heavier, tilt_at_caption, left_note?, right_note?, note_at_caption?}
- rule {display}
Any scene may add stamp {text, at_caption}. captions = [[display, spoken_word_count], ...] covering every VO word; *word* = red emphasis; max 26 characters per caption. The rule scene's display must have the same words as its vo.

## Media bridge (engine/bridge.py)
- python3 engine/bridge.py --probe  -> exit 0 only if mahmodmaho077-dev/tiktok-media-public is writable from this session.
- python3 engine/bridge.py IR-XXX videos/IR-XXX/IR-XXX.mp4  -> uploads to media/IR-XXX-<video_md5[:8]>.mp4, never overwrites, prints the raw.githubusercontent.com URL only after it returns HTTP 200 with the identical sha256.
- Accepts only ids matching IR-XXX and files named IR-XXX.mp4 that are 1080x1920 h264 renders.
- If the probe fails: publish nothing that day and report the exact error.
- If only the upload step fails (for example the API rejects the file size) while git push works: copy the render to media/IR-XXX-<video_md5[:8]>.mp4 (never overwrite an existing path), git add/commit/push, then confirm the raw.githubusercontent.com URL returns HTTP 200 with the identical sha256 before setting "hosted".
- Render folders (videos/IR-XXX/) are git-ignored; only media/ files are published.

## Metricool (MCP only, never the REST API)
brand/blogId 7029303, timezone Europe/Athens, network tiktok.
createScheduledPost: date = today 18:00 Europe/Athens (or now + 15 min if that has passed); info =
{providers:[{network:"tiktok"}], text: caption + blank line + hashtags, firstCommentText: "IR-XXX · Sources: ...", media:[raw URL], autoPublish:true, draft:false, publicationDate:{dateTime, timezone:"Europe/Athens"}, tiktokData:{privacyOption:"PUBLIC_TO_EVERYONE", title: tiktok_title, isAigc:true, disableComment:false, disableDuet:false, disableStitch:false, autoAddMusic:false}}
Never retry blindly: if a response is unclear, re-read getScheduledPosts before doing anything.

## Ledger (ledger/videos.json in this repository)
Format: {"updated", "next_id", "videos": [entries], "account_topics": [...], "reserve": [...]}. One entry per IR id:
{id, created, status, title, company, hook, tiktok_title, caption, hashtags, first_comment, industry, angle, mechanism_family, core_claim, concept_key, gate_score, gate_breakdown, sources[{label,url}], story_json, asset{sha256, video_md5, audio_md5}, media_url, hosted_at, metricool{id, uuid}, tiktok_url, metrics[]}
status flow: queued -> qa_passed -> hosted -> scheduled -> published   (or rejected / hold). "hosted" means the public media URL is verified and the item is waiting for Metricool. A scheduled or published id is never selectable again.
mechanism_family: incentives_behavior | decisions_errors | numbers_costs | counterintuitive | advantages_leverage | constraints_consequences
Commit and push the ledger after every status change.

Seed entries (ids and topics already used — never reuse). ledger/videos.json already contains them.
- IR-001 Lufthansa "unnecessary" winter flights to keep airport slots — hold, not published.
- IR-002 Southwest Airlines Christmas 2022 crew-scheduling meltdown — hold, not published.
- IR-003 London Tube strike commuters — rejected (out of niche).
- IR-004 Hertz sells ~20,000 EVs (Tesla price cuts hit resale value; ~$245M charge) — PUBLISHED manually by the owner on 21 Sep 2026. Never select, re-render, re-host or re-post IR-004.
- IR-005 Adobe "annual, paid monthly" plan + early termination fee ($150M U.S. settlement, Mar 2026) — QUEUED. Research, script and QA are done: videos/IR-005.json and its packaging are in the ledger. Next run: render it (--check, --preview, --full), inspect the frames, host it, set status "hosted". Do not rewrite its facts.
- Topics already on the account (do not repeat company + mechanism): Google paying Apple to be the default search engine; Berkshire cash pile; Berkshire insurance float; Dell negative cash conversion cycle; Starbucks card breakage; Delta–American Express miles; Domino's supply-chain revenue; McDonald's franchise rent; Red Lobster Endless Shrimp / lease obligations.
- Reserve candidates (researched, not yet used): HP "bad investment" printer/ink model (CEO, Jan 2024); Spotify audiobook bundle and songwriter royalties (wait until the litigation is final).
Next new id: IR-006.

## Daily cycle (1 post per day, run at 06:00 UTC)
0. git pull. State: real UTC time, ledger/videos.json. If Metricool tools exist, also getScheduledPosts.
1. Reconcile (only with Metricool tools): posts whose TikTok status is PUBLISHED -> ledger "published" with tiktok_url; append metrics (getAnalyticsDataByMetrics, brandId 7029303, last 30 days, TKPO02 TKPO03 TKPO05 TKPO06 TKPO07 TKPO08 TKPO09 TKPO10 TKPO11 TKPO13 TKPO14 TKPO15 TKPO16 TKPO20 TKPO21). Saves, profile visits, follows, rewatches and retention curves are not available via Metricool: record them as not available, never estimate.
2. Bridge probe (python3 engine/bridge.py --probe). If it fails: stop, report the exact error.
3. Pick today's item: the oldest "queued" item (render it from its story JSON), else produce a new one with the next id. If any item reached "hosted" less than 20 hours ago (field hosted_at), produce nothing today: it is still waiting for its 18:00 Athens slot (one post per day).
4. Produce + QA + packaging (tiktok_title, caption, hashtags, first_comment, sources).
5. Host with the bridge; write media_url, asset {sha256, video_md5, audio_md5} and hosted_at (UTC ISO time) into the ledger; status "hosted"; commit and push immediately. The Cowork scheduler only accepts a hosted item whose asset.sha256 matches the file at media_url.
6. Only with Metricool tools: duplicate check (ledger + getScheduledPosts 30 days back to 30 days ahead, extendedRange true; the IR id in firstCommentText or the media URL).
7. Only with Metricool tools: createScheduledPost for 18:00 Europe/Athens today; status "scheduled" with metricool {id, uuid}; commit and push.
8. One short Arabic report: IR id, status, TikTok URL if any, exact error if anything failed.

After 21 published posts: evaluate real data (OBSERVED vs HYPOTHESIS). Move to 2 posts per day only if every post held gate >= 85 and the data supports it; otherwise stay at 1. Never change the niche because of one weak post.

## Failure policy
Repair only the failing component. Never duplicate a post on retry. Preserve the ledger. If Metricool or the bridge is unavailable, publish nothing and substitute nothing. Never report success that did not happen.
