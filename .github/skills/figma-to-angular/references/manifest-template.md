# Manifest template

Write this to `figma-manifest.md` at the repo root during Phase 1, filled from `get_metadata`.
It is the contract for what "done" means, and the completeness script parses it, so the
structure below is load-bearing — keep the headings and the `variants:` line format.

---

```markdown
# Figma → Angular coverage

Source: <figma file URL>
Root node: <node-id>
Generated: <date>
Angular: <version from package.json>
Styling: <SCSS | Tailwind | ...>

## Summary

- Nodes: 0 / 47
- Component sets: 0 / 6
- Variant combinations: 0 / 84

## Tokens

- [ ] Colours (12)
- [ ] Spacing (8)
- [ ] Typography (6)
- [ ] Radii (4)
- [ ] Shadows (3)

## Components

### app-button `1:2043`
variants: variant[primary,secondary,ghost,danger] size[sm,md,lg] icon[none,left,right,only]
combinations: 48
- [ ] primary / sm / none
- [ ] primary / sm / left
- [ ] primary / sm / right
- [ ] primary / sm / only
- [ ] primary / md / none
...

### app-card `1:2110`
variants: elevation[flat,raised] media[none,top,side]
combinations: 6
- [ ] flat / none
- [ ] flat / top
...

## Screens

### checkout-page `1:3001`
- [ ] Header `1:3002`
- [ ] Order summary `1:3010`
- [ ] Payment form `1:3025`
- [ ] Footer `1:3080`

## Reused via Code Connect

- `1:2043` → existing `ButtonComponent` (src/app/ui/button)

## Open questions

- Node `1:3025` uses colour #2B2B2B with no matching variable
- No mobile breakpoint defined for `1:3010`
- Hover transition duration unspecified

## Known fidelity gaps

- (filled during Phase 5)
```

---

## Rules

Enumerate the full cartesian product of variant properties, one line each. Writing
`- [ ] all 48 combinations` defeats the entire mechanism — the point is that a human can scan
the file and see what's missing.

Check a box only after the code for that combination exists and compiles. Never check boxes
in advance, and never delete an unchecked line to make the check pass. If a combination turns
out to be genuinely impossible, mark it `- [x] ~~primary / sm / only~~ (N/A: reason)` so the
decision is visible and reviewable rather than erased.
