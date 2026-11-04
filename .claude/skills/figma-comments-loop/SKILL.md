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

| Page | Node is | Scope of the change |
|---|---|---|
| `Formats` | one banner (`<CODE>_<W>x<H>_Static_<LANG>_v<N>`) | that language and format only |
| `Master visuals` | an EN master banner | template or EN copy, rebuilt into every banner |
| `video layers` | one layer of one format | motion or that layer's asset |

A node that is not in the map belongs to something else in the file: leave it alone.

## 3. Classify and decide

Copy, visual, layout, motion, or a question. A question gets an answer in the thread and no edit.
Check the request against the client's brand rules and `facts.md`. If it collides with them, do
not apply it: reply with the conflict and a compliant alternative.

## 4. Edit

- Copy: `campaigns/<CODE>/i18n/<lang>.json`. A one-banner change that must not spread gets a
  per-format override instead of a new key for everyone.
- Visual or layout: `templates/banner.html` or the campaign's `assets/`.
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
