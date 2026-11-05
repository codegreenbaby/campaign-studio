---
name: campaign-build
description: Build a full ad campaign from a brief, in the order that keeps facts, copy and 66 banners consistent. Use when the user starts a new campaign («сделай кампанию», a brief, a Confluence or Jira link), asks to rebuild the board, push to Figma, make the videos, or apply comments to a campaign.
---

# Campaign build

Brief → facts → copy → glossary → master → formats → board → Figma → motion → video → comments.
The user approves at four points, marked **[stop]**. Do not run past a stop.

## 1. Brief and facts

Create `campaigns/<CODE>/` with `brief.md` and `facts.md`. `CODE` is short, upper case, used in
every frame name (example `SPRING25`).

`facts.md` is a table: fact, value, source (Jira key, Confluence page, Slack permalink, xlsx,
live site), status (`confirmed`, `site`, `doc`, `assumption`). Read the sources yourself:
the product spec, the tickets and release that ship the feature, any existing marketing brief,
and the team chat about it. Write down every conflict between sources and which one won. Anything the
campaign needs and nobody stated gets `[VERIFY: what is needed]`.

## 2. Copy deck **[stop]**

Load `copy` and the client's brand skill, if there is one. Angle first, then three headline options, then payoff, slots and
CTA. Every slot in `formats.json` gets a long and a short version; the `wide` layout uses the
short ones. Run the six final-pass checks one at a time and record the result. Ask the user to
pick a headline.

## 3. Glossary

`glossary/<lang>.json`: the 15-25 terms the campaign uses, with the term chosen per language
and the URL it was taken from. Sources in order: the client's own language versions, category
leaders that publish the language, then a plain translation marked `unsourced`. Reuse an
existing glossary and extend it. Details in `localize`.

## 4. Master and formats **[stop after the EN master]**

Load `design-taste-frontend`, `high-end-visual-design`, `brandkit-images`. One template per
layout family in `templates/` (`vertical`, `block`, `wide`); a format is a template plus a size
from `formats.json`. Text lives only in `i18n/<lang>.json`, keyed by slot. Images from
`campaigns/<CODE>/assets/` only; user references from `refs/` steer style, never get copied.

`tools/render.py` builds every format x language into `dist/` and fails loudly when a text box
overflows its slot. Fix overflow by switching to the short version, then by type scale within
the template's limits, never by cutting words. Arabic sets `dir="rtl"`; ar, zh-hans, ja switch to
the Noto fallbacks in `tokens.json`.

Show the EN row first. Build the other ten only after the user accepts it.

## 5. Board

`dist/board.html`: rows are languages, columns are formats in `formats.json` order, frame names
above each banner, motion live. Export PNGs with `tools/export.py`. Look at `de` and `ar` in the
browser pane before reporting.

## 6. Figma

Through the plugin only (`plugin/README.md`): write `state/patch.json`, start
`tools/patch_server.py` in the background, ask the user to run the plugin, read
`state/patch-result.json`, stop the server. `tools/figma_board.py <CODE>` writes the patch: three
pages in the file "Marketing campaigns", `{CODE} — Master visuals`, `{CODE} — Formats`,
`{CODE} — video layers`, frames named per `formats.json` with a `label - <name>` text above each.
The patch names its file, so the plugin will not draw into another file. Then
`figma_board.py <CODE> --record` writes page and frame ids to `state/figma.json`.

## 7. Motion **[stop after the EN master animation]**

Load `animate`, `review-animations`, `animation-vocabulary`. 6 seconds, the last frame equals the
static banner. Motion is CSS or GSAP in the template, driven by one timeline that the exporter
can seek. Respect `prefers-reduced-motion` in the board.

## 8. Video export

`tools/export.py --video`: Playwright seeks the timeline frame by frame at 30 fps, ffmpeg encodes
H.264 yuv420p. Run in the background; 66 files. Video layers (background, chart, text groups)
go to the `video layers` page as separate frames.

## 9. Comments

`figma-comments-loop`. The scope of a change follows where its source lives, not which frame
carries the comment: a copy edit on a `Formats` frame goes to `i18n/<lang>.json` and reaches every
format of that language; a layout edit goes to that size's entry in `formats.json` and reaches that
size in every language; a design change goes to the template and reaches all banners, as does
any comment on the `Master visuals` page. There is no single-banner override. Rebuild, re-export,
patch Figma, reply in the thread with what changed and in which banners.

## Report

What was built, what is `[VERIFY]`, which translations are unreviewed, which Figma edits are
pending, and what the user needs to click.
