# brand/

One folder per client, not committed. Suggested contents:

```
brand/<client>/
  tokens.json      colours, fonts (with script fallbacks for ar / zh / ja), radii
  voice.md         vocabulary lane, tone, words to avoid, legal lines
  competitors.md   who else is in the category and how they position
```

Pair it with a client skill in `.claude/skills/<client>-brand/` that states the rule priority
(legal, facts, brand, the user's comment, then craft skills). `CLAUDE.local.md` tells the agent
to load it.
