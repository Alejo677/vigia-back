#!/usr/bin/env python3
"""Verify a Figma → Angular implementation actually covers the manifest.

Three checks, all mechanical:
  1. Every manifest checkbox is ticked (or explicitly marked N/A).
  2. No placeholder / abbreviation phrases survive in generated source.
  3. Every variant value declared in the manifest appears in the source.

Exit code 0 = pass, 1 = fail. Designed to be run by the agent before it reports
completion, and by a human who doesn't trust the agent's self-assessment.
"""

import argparse
import re
import sys
from pathlib import Path

# Phrases that mean "I stopped writing code here". Case-insensitive substring match.
PLACEHOLDER_PATTERNS = [
    r"\.\.\.\s*(rest|remaining|other|more)\b",
    r"\b(and so on|etc\.)",
    r"\bfor brevity\b",
    r"\bsame (as above|pattern|structure)\b",
    r"\bsimilar(ly)? (to|for) (the )?(above|other)",
    r"\b(remaining|other) (variants?|states?|combinations?|cases?)\b",
    r"\bomitted\b",
    r"\btruncated\b",
    r"\bfollows? the same\b",
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bimplement (the )?rest\b",
    r"<!--\s*\.\.\.",
    r"/\*\s*\.\.\.\s*\*/",
]

SOURCE_SUFFIXES = {".ts", ".html", ".scss", ".css"}
SKIP_DIRS = {"node_modules", "dist", ".git", ".angular", "coverage"}


def read_manifest(path: Path) -> str:
    if not path.exists():
        sys.exit(f"FAIL: manifest not found at {path}. Phase 1 was skipped.")
    return path.read_text(encoding="utf-8")


def check_boxes(manifest: str) -> list[str]:
    """Unticked checkboxes are uncovered work."""
    failures = []
    for i, line in enumerate(manifest.splitlines(), 1):
        if re.match(r"\s*-\s*\[\s\]", line):
            failures.append(f"  line {i}: {line.strip()}")
    return failures


def parse_variants(manifest: str) -> dict[str, list[str]]:
    """Pull `variants: name[a,b,c] other[x,y]` lines into {property: [values]}."""
    variants: dict[str, list[str]] = {}
    for line in manifest.splitlines():
        if not line.strip().lower().startswith("variants:"):
            continue
        for prop, values in re.findall(r"(\w+)\[([^\]]+)\]", line):
            vals = [v.strip() for v in values.split(",") if v.strip()]
            variants.setdefault(prop, [])
            for v in vals:
                if v not in variants[prop]:
                    variants[prop].append(v)
    return variants


def iter_sources(root: Path):
    for p in root.rglob("*"):
        if p.is_dir() or p.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def check_placeholders(root: Path) -> list[str]:
    failures = []
    compiled = [(p, re.compile(p, re.IGNORECASE)) for p in PLACEHOLDER_PATTERNS]
    for path in iter_sources(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pattern, rx in compiled:
                if rx.search(line):
                    failures.append(f"  {path}:{i}  [{pattern}]  {line.strip()[:90]}")
                    break
    return failures


def check_variant_coverage(root: Path, variants: dict[str, list[str]]) -> list[str]:
    """A declared variant value that appears nowhere in source was never implemented."""
    blob = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in iter_sources(root)
    )
    failures = []
    for prop, values in sorted(variants.items()):
        for value in values:
            # Look for the value as a quoted literal or an attribute selector value.
            if not re.search(rf"['\"\[=]{re.escape(value)}['\"\]]", blob):
                failures.append(f"  {prop}: '{value}' declared in manifest, absent from source")
    return failures


def report(title: str, failures: list[str]) -> bool:
    if failures:
        print(f"\nFAIL — {title} ({len(failures)})")
        for f in failures[:40]:
            print(f)
        if len(failures) > 40:
            print(f"  ... and {len(failures) - 40} more")
        return False
    print(f"PASS — {title}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="figma-manifest.md")
    ap.add_argument("--src", default="src/app")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    src_root = Path(args.src)
    if not src_root.exists():
        sys.exit(f"FAIL: source root not found at {src_root}")

    manifest = read_manifest(manifest_path)
    variants = parse_variants(manifest)

    print(f"Manifest: {manifest_path}")
    print(f"Source:   {src_root}")
    print(f"Variant properties declared: {len(variants)}")

    ok = True
    ok &= report("manifest coverage", check_boxes(manifest))
    ok &= report("no placeholder code", check_placeholders(src_root))
    ok &= report("variant values present in source", check_variant_coverage(src_root, variants))

    if ok:
        print("\nAll checks passed.")
        print("Note: this proves nothing was omitted. It does not prove visual fidelity —")
        print("that still needs the Phase 5 screenshot comparison.")
        return 0

    print("\nDo not report this work as complete. Fix the failures above and re-run.")
    print("Editing the manifest to make this pass defeats the purpose.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
