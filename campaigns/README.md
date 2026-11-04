# campaigns/

One folder per campaign, named by its short code (used in every frame and file name). Campaign
folders are not committed, since they hold client copy, facts and assets, except `DEMO`, a
working example with a fictional product. Copy it to start a new campaign.

```
campaigns/<CODE>/
  campaign.json        code, version, title, brandName, theme, assets, count-up keys, short-copy order
  brief.md             what the campaign is, scope, deliverables, art direction
  facts.md             every number allowed in copy, with source and status
  copy-deck.md         angle, headline options, copy per slot (long and short), final-pass notes
  i18n/<lang>.json     copy per language, same keys as en.json
  assets/              images and SVGs the template uses
  refs/                style references (never copied into the work)
  dist/                build output (banners, png, mp4, layers, board.html, <CODE>-board.html)
```

## campaign.json

```json
{
  "code": "SPRING25",
  "version": 1,
  "title": "SPRING25 · Spring launch",
  "brandName": "Example Co",
  "template": "templates/banner.html",
  "langs": ["en", "de", "ar"],
  "theme": { "accent": "#3B82F6", "accent-2": "#22C55E", "accent-soft": "#BFDBFE" },
  "assets": {
    "logo": "assets/logo.svg",
    "bg": "assets/background.jpg",
    "rocket": "assets/sprite.svg",
    "candles": "assets/chart.svg"
  },
  "counts": ["price.value", "price2", "price2.short", "code.off"],
  "shortOrder": ["sub", "chip", "price2", "badge"],
  "seconds": 6
}
```

- `theme` overrides any colour token of the template (`--accent`, `--accent-2`, `--accent-soft`,
  `--accent-deep`, `--bg`, `--ink`, `--soft`, `--muted`).
- `rocket` is the sprite that flies across the banner; `candles` is an inline SVG whose
  `<g class="c">` groups rise in sequence and whose `<g class="line">` draws in.
- `langs` (optional): languages this campaign is built in; defaults to all in `formats.json`.
- `counts`: copy keys whose last number counts up from zero when the banner starts.
- `shortOrder`: which slots switch to their `.short` copy, in this order, when a layout overflows.

## i18n/en.json keys

`badge`, `headline.1`, `headline.2`, `sub`, `price.from`, `price.value`, `price2`, `code.label`,
`code.value`, `code.off`, `cta`, `chip`, `disclaimer`, `disclaimerShort`, plus `.short` variants
of `badge`, `sub`, `price2`, `chip`. In `price2`, `{…}` marks the bold, counting part.
