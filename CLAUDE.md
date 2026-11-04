# Campaign Studio

Campaign agent for paid-social and display advertising. One brief in, one campaign out: angle,
copy, master visual, every ad format in every language, short video versions, an HTML board,
and the same board in Figma. Revisions come back as Figma comments. Every campaign is a new task
with its own folder under `campaigns/`.

Reply in the user's language. Campaign copy is written in English first, then localized.

Machine-specific and client-specific instructions live in `CLAUDE.local.md` (not in git):
@CLAUDE.local.md

## Commands

| User says | Do |
|---|---|
| new campaign, a brief, a spec link | `campaign-build` from step 1 |
| "check comments" | `figma-comments-loop` |
| "push to Figma" | `campaign-build` step 6 |
| "rebuild the board" | `campaign-build` steps 4-5 |
| "make the videos" | `campaign-build` steps 7-8 |

If the client has a brand skill (`<client>-brand`), load it before any of them. Its rules win
over the craft skills.

## Skills (`.claude/skills/`)

In this repo: `campaign-build`, `localize`, `figma-comments-loop`.
Expected next to them (installed separately, see README): a copywriting skill (`copy`), design
skills (`design-taste-frontend`, `high-end-visual-design`, `brandkit-images`), motion skills
(`animate`, `review-animations`, `animation-vocabulary`) and `figma-build`. If one is missing,
say so and continue with the closest one available.

## Layout

| Path | What |
|---|---|
| `formats.json` | Formats (size, platform, layout family, content slots), languages, naming, video spec |
| `templates/banner.html` | The banner template: three layout families, one seekable motion timeline |
| `campaigns/<CODE>/` | `campaign.json`, `brief.md`, `facts.md`, `copy-deck.md`, `i18n/<lang>.json`, `assets/` |
| `campaigns/<CODE>/dist/` | Built output: `banners/`, `png/`, `mp4/`, `layers/`, `board.html`, `<CODE>-board.html` |
| `brand/<client>/` | Brand tokens and voice per client |
| `tools/` | `render.py`, `export.py`, `board_standalone.py`, `figma_board.py`, `figma_comments.py`, `patch_server.py`, `duotone.py` |
| `plugin/` | Figma development plugin that applies patches; `plugin/test/` runs it against a strict API stub |
| `state/figma.json` | Target Figma file, page and frame ids per campaign (not in git) |
| `secrets/figma-token.txt` | Figma personal access token (not in git) |

Python: `.venv\Scripts\python` (Playwright + Chromium, Pillow). Set `PYTHONIOENCODING=utf-8`
when output has non-ASCII text. ffmpeg must be on PATH for video export.

## Figma

- Writes go through the plugin (`plugin/`), not the Figma MCP: plugins have no monthly call cap.
  Use MCP only for what the plugin cannot do, and say so before spending a call.
- `tools/figma_board.py <CODE>` writes the patch: three pages per campaign,
  `{CODE} — Master visuals`, `{CODE} — Formats`, `{CODE} — video layers`. Every patch names its
  target file; the plugin refuses to run it in any other file.
- Comments are read and answered through the REST API (`tools/figma_comments.py`), because neither
  the plugin API nor the MCP can read them. Map them through `state/figma.json` (`bySection`).

## Hard rules

- No number in copy that is not in `campaigns/<CODE>/facts.md`; otherwise `[VERIFY: ...]`.
- No em dashes in copy.
- Translations are machine translations until a native speaker reviews them; say so.
- Never print, log or put the Figma token in a URL.
- Do not publish, post or commit anywhere new without the user asking.
