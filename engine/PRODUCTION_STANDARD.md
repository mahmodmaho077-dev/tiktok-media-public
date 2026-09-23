# INVISIBLE RULES (TikTok @invisiblerulesmedia) — production standard

Written 2026-09-23. Metricool brand id 7029303, timezone Europe/Athens.
This file is about TikTok only. Never touch the YouTube pipeline, its repo, its queue,
its cp-* assets or its renders.

===============================================================================
## 1. NICHE — LOCKED, never drift

Forensic company/business case studies. Every post reveals one hidden business
mechanism behind a specific, verified decision: pricing move, margin, contract,
cash-flow structure, distribution advantage, unit economics, customer economics,
incentive, or capital allocation.
Not psychology. Not self-development. Not generic motivation or "make money" content.
Every claim traceable to a named source; if a number cannot be verified, it does not
go in the video — write "Not verified." rather than guessing.

===============================================================================
## 2. COVER IMAGE — what is actually possible

Metricool's createScheduledPost has two cover fields:
- `videoThumbnailUrl` — a custom jpg/jpeg/png cover at a public URL.
  Works on TikTok ONLY for Business-connected accounts.
  On a personal TikTok account it is silently ignored.
- `videoCoverMilliseconds` — an offset into the video used as the cover frame.
  Works regardless of account type.

So do BOTH, every time:
a) Design the cover as a real frame inside the video: hold it for the first 400 ms,
   1080x1920, then cut into the hook. Set videoCoverMilliseconds to 200.
b) Also export that same frame as a PNG, host it in tiktok-media-public, and pass its
   raw URL as videoThumbnailUrl. If the account is Business it is used; if not, it is
   ignored and the baked frame from (a) still gives the right cover.
c) Check once whether the TikTok account in Metricool is connected as Business. Report
   which it is; do not assume.
   Status (checked 2026-09-23): not determinable from any available Metricool MCP tool —
   `getBrandSettings` returns only the connected username (`invisiblerulesmedia`), no
   account-tier field. Needs a direct check in the Metricool web UI (Brand settings →
   TikTok connection). Treat as Personal (do (a) unconditionally, don't rely on (b))
   until confirmed otherwise.

Cover design: 3-5 words maximum, the company name or the number as the largest element,
one accent colour, everything else neutral. It must be readable in a 150px-wide grid
cell. No full sentences, no logos of real companies, no faces.

===============================================================================
## 3. VISUAL HOOK — first 1.5 seconds

- The specific claim is on screen before the voice says it: a company + a number,
  or a company + a contradiction. Never a generic question, never "here's why".
- One element moves from frame 0 — the number counting, the line breaking, the two
  columns diverging. Static text alone is a scroll.
- No channel name, no logo, no intro animation in the first 1.5s.
- One accent colour on one element; the rest neutral.
- Safe zones: keep all text out of the bottom 480px and the right 200px of the
  1080x1920 frame — TikTok's caption, buttons and username sit there.
- Burned-in captions for the whole video, high contrast, max 4 words per line.

===============================================================================
## 4. TITLE AND CAPTION

- tiktokData.title: the on-screen-style hook, under 60 characters, concrete.
  Good: "Hertz bought 100,000 EVs. Then sold them at a loss."
  Bad:  "The shocking truth about Hertz"
- Caption (post text): one sentence that adds information the video does not repeat,
  then the hashtags. No "follow for more", no emoji strings, no engagement bait.
- Name the company and the year in the first line. Specificity is the hook.

===============================================================================
## 5. HASHTAGS

- Exactly 3-5, at the end of the caption.
- First = the specific mechanism or industry, not the generic one:
     #UnitEconomics #CarRental #BusinessBreakdown
     #PricingStrategy #Airlines #BusinessCaseStudy
- Keep one broad tag at the end (#BusinessCaseStudy or #BusinessBreakdown), never more.
- No #fyp, #viral, #foryou — they attract the wrong audience for this niche.
- Never repeat the same first two hashtags on consecutive posts.

===============================================================================
## 6. POSTING TIME — from the account's real Metricool data (pulled 2026-09-23)

Europe/Athens local time, higher = better:
  Wed 10:00 (1432) · Wed 18:00 (1386) · Thu 10:00 (1471) · Thu 18:00 (1378)
  Fri 10:00 (1379) · Fri 18:00 (1222) · Mon/Tue 18:00 (~1100) · weekends clearly weaker
Rule: one post per day at 18:00 Europe/Athens. If a second post is added, put it at
10:00. Wednesday and Thursday are the strongest days — put the best case study there.
Treat these numbers as indicative only: the account has almost no history yet.
Re-pull getBestTimeToPostByNetwork after ~30 posts and update this section.

===============================================================================
## 7. RUN FLOW (unchanged — manual, one cycle per "Run next TikTok")

next unused IR-* id -> research -> script -> render -> QA -> cover frame + hosted PNG
-> title/caption/hashtags -> duplicate check against the ledger -> host media
-> exactly ONE Metricool scheduled post -> update the ledger.
No approval questions during the cycle. If any step fails, stop BEFORE publishing and
report the exact error. Never schedule two posts for the same item. Never reuse an
IR id. Never publish without the cover frame in place.
