---
name: figma-comments-loop
description: Apply the user's Figma comments to a campaign and reply in each thread. Use when the user says "check comments", "apply comments", or anything that means reading feedback left on the campaign's Figma pages.
---

# Figma comments loop

Read → map → classify → edit → rebuild → patch Figma → reply → report.
Load the client's brand skill first, if there is one.

## 1. Read

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python tools/figma_comments.py fetch
```

Returns unresolved root threads that are not yet in `state/applied.jsonl`, with replies in
order. The instruction is often in a reply, not the root. Act only on threads by the user (their
handle is in `CLAUDE.local.md`). An empty list means nothing to do: say so and stop.

Token: `secrets/figma-token.txt` or `%USERPROFILE%\.figma-token`. Never print it, never pass it on
a command line, never put it in a URL. A `401 Token has expired` means the user needs a new token
with the scope "File comments: read and write".

## 2. Map

Each thread carries `node_id` and `node_offset`. Look the node up in `state/figma.json`
(`campaigns.<CODE>.bySection`):

| Page | Node is | Tells you |
|---|---|---|
| `Formats` | one banner (`<CODE>_<W>x<H>_Static_<LANG>_v<N>`) | which language and size the user was looking at |
| `Master visuals` | an EN master banner | a change meant for the whole campaign |
| `video layers` | one layer of one format | motion or that layer's asset |

The scope of the edit follows where its source lives (step 4), not the frame:

| Kind of request | Source | Reaches |
|---|---|---|
| Copy ("change this word") | `i18n/<lang>.json` | every format of that language |
| Layout of one size (type size, spacing, chart position) | that size in `formats.json` (`vars`) | that size in every language |
| Design (colour, asset, motion, structure) | `templates/banner.html`, `campaign.json` theme, `assets/` | every banner |
| Anything on `Master visuals` | template or `en.json` | every banner (EN copy flows into other languages only through their own files) |

There is no single-banner override. Say in the reply which banners changed.

A node that is not in the map belongs to something else in the file: leave it alone.

## 3. Classify and decide

Copy, visual, layout, motion, or a question. A question gets an answer in the thread and no edit.
Check the request against the client's brand rules and `facts.md`. If it collides with them, do
not apply it: reply with the conflict and a compliant alternative.

## 4. Edit

- Copy: `campaigns/<CODE>/i18n/<lang>.json` (every format of that language). A copy change on an
  EN master that should reach other languages needs the matching edit in each language file.
- Layout of one size: that format's `vars` in `formats.json` (that size in every language). After
  the change, `--check` must stay clean in every language: a bigger headline is fine for EN and
  may overflow in DE.
- Design: `templates/banner.html`, the campaign's `theme` in `campaign.json`, or `assets/`.
- Motion: the timeline in `templates/banner.html` (`seek()`); the last frame must still equal the
  static banner.

## 5. Rebuild and check

```
.venv/Scripts/python tools/render.py <CODE> --check
.venv/Scripts/python tools/export.py <CODE> --match <what changed>
```

Look at the changed banners. Re-export videos only for what changed (`--video --match`).

## 6. Patch Figma

`tools/figma_board.py <CODE>` rewrites the patch, start `tools/patch_server.py` in the
background, ask the user to run *Campaign Studio Patch → Apply patch from agent* in the target
file, then `figma_board.py <CODE> --record`. Every `failed` entry in `state/patch-result.json`
needs a fix and another run. Stop the server when done.

## 7. Reply

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python tools/figma_comments.py reply <comment_id> "<what changed, where>"
```

One or two sentences in the user's language: what changed and in which banners. The script
records the thread in `state/applied.jsonl`.

## 8. Report

List what was applied, what was declined and why, and anything still pending.
