"""Shared checks for the tools: clear messages instead of tracebacks when something is missing."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg):
    sys.exit("error: " + msg)


def campaigns():
    d = ROOT / "campaigns"
    return sorted(p.name for p in d.iterdir() if (p / "campaign.json").exists()) if d.exists() else []


def campaign_dir(code):
    """campaigns/<code>/, or exit with the list of campaigns that do exist."""
    if not code:
        fail("give a campaign code, e.g. DEMO. Campaigns here: " + (", ".join(campaigns()) or "none"))
    d = ROOT / "campaigns" / code
    if not (d / "campaign.json").exists():
        have = ", ".join(campaigns()) or "none"
        fail(f"no campaign '{code}' (missing campaigns/{code}/campaign.json). Campaigns here: {have}. "
             "The folder format is in campaigns/README.md; campaigns/DEMO is a working example.")
    if not (d / "i18n" / "en.json").exists():
        fail(f"campaigns/{code}/i18n/en.json is missing: English copy is the source for every language.")
    return d


def figma_state():
    """state/figma.json, or exit with what to put in it."""
    p = ROOT / "state" / "figma.json"
    if not p.exists():
        fail("state/figma.json is missing. Create it with the target Figma file:\n"
             '  { "file": "<exact Figma file name>", "fileKey": "<key from the file URL>", "campaigns": {} }')
    s = json.loads(p.read_text(encoding="utf-8"))
    for k in ("file", "fileKey"):
        if not s.get(k):
            fail(f'state/figma.json has no "{k}". See README, "Requirements and setup".')
    s.setdefault("campaigns", {})
    return s
