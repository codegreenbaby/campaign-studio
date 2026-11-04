---
name: localize
description: Produce a campaign's language versions from its English copy, in the vocabulary the client's category actually uses. Use when the user asks for translations or language versions of a campaign, or when campaign-build reaches step 4 for languages other than English.
---

# Localize

Languages come from `formats.json` (`langs`). English (`campaigns/<CODE>/i18n/en.json`) is the
source; every other language is `i18n/<lang>.json` with exactly the same keys.

## Before translating: the glossary

Ad copy fails in translation on category vocabulary, not on grammar. Build or extend a glossary
first (`campaign-build` step 3): the 15-25 terms the campaign uses, the term chosen per language,
and the URL it was taken from. Sources in order:

1. The client's own localized site.
2. Category leaders that publish that language.
3. A plain translation, marked `unsourced`.

Record per language: formal or informal address, how prices, percents and currency are written
(`32 $` vs `$32` vs `US$ 32`, `20 %` vs `%20`), digits (Western or native), and whether product
names stay in Latin script.

## Writing the files

- Same keys as `en.json`. `<key>.short` variants exist for tight layouts; keep them short.
- `{…}` marks the bold part of a line, and the last number inside it counts up in the animation.
  Keep the braces around the same value.
- Do not translate: numbers, codes, product names, platform names, `[VERIFY]` markers.
- Use a no-break space where a number and its unit must stay together (`20 %`).
- The brand's vocabulary rules hold in every language. If the client's own localized site
  breaks them, follow the brand rule and say so.
- No em dashes.

## After writing

1. `tools/render.py <CODE> --check`. Long languages (de, and often vi, ms, tr) trigger the
   headline auto-fit and the short variants; an `overflow` line is a failure to fix.
2. Look at the longest language and every RTL language (`rtl` in `formats.json`) in the board.
3. Tell the user these are machine translations pending native review, and list the terms you
   were least sure of.
