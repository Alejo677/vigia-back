# Figma → Angular mapping rules

How design concepts become Angular concepts, so the mapping stays consistent across a whole
file instead of drifting component by component.

Read the section the current phase needs rather than the whole file — most of it doesn't apply
until Phase 4, and loading it early just spends context.

| Section | Read during |
|---|---|
| [Structural mapping](#structural-mapping) | Phase 1 |
| [Variants: the core problem](#variants-the-core-problem) | Phase 1 |
| [Tokens](#tokens) | Phase 2 |
| [Typography](#typography) | Phase 2 |
| [Auto Layout → CSS](#auto-layout--css) | Phase 4 |
| [Responsive](#responsive) | Phase 4 |
| [Interaction states](#interaction-states) | Phase 4 |
| [Assets](#assets) | Phase 4 |
| [Accessibility](#accessibility) | Phase 4 |

## Structural mapping

| Figma | Angular |
|---|---|
| `COMPONENT_SET` | One component with typed inputs, one per variant property |
| `COMPONENT` | Standalone component |
| `INSTANCE` | Usage of the component with bound inputs |
| Frame with Auto Layout | Container element with flex/grid |
| Frame without Auto Layout | Container with explicit positioning — flag it, it usually means the design isn't responsive-ready |
| Text layer | Text node, styled via a typography token class |
| Boolean/instance swap property | Content projection (`<ng-content select="...">`) |
| Text property | String input |
| Nested component instance | Child component usage, not duplicated markup |

Prefer content projection over string inputs when the slot could contain markup. A `label`
input that turns out to need an icon inside it becomes a breaking change; a projected slot
doesn't.

## Variants: the core problem

A Figma component set with three variant properties is not three inputs with independent
behaviour — it is a matrix, and the design may treat specific *combinations* specially.
Check for combination-specific styling before assuming the properties are orthogonal.

Map each variant property to a typed input with a literal union type, never a bare string:

```ts
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';
export type ButtonIcon = 'none' | 'left' | 'right' | 'only';

@Component({
  selector: 'app-button',
  changeDetection: ChangeDetectionStrategy.OnPush,
  // ...
})
export class ButtonComponent {
  readonly variant = input<ButtonVariant>('primary');
  readonly size = input<ButtonSize>('md');
  readonly icon = input<ButtonIcon>('none');
  readonly disabled = input(false, { transform: booleanAttribute });
}
```

Literal unions matter here beyond type safety: they make the completeness check possible.
A `string` input cannot be verified against the manifest; a union can.

Drive styling through host bindings rather than `ngClass` on a wrapper, so the component's
own element carries the state and consumers can style around it:

```ts
host: {
  '[attr.data-variant]': 'variant()',
  '[attr.data-size]': 'size()',
  '[attr.data-icon]': 'icon()',
  '[attr.aria-disabled]': 'disabled() || null',
}
```

```scss
:host([data-variant='primary']) { /* ... */ }
:host([data-variant='primary'][data-size='sm']) { /* combination-specific */ }
```

Every variant value from the manifest must appear in both the union type and the stylesheet.
A value present in the type but with no matching style rule is a silent omission — it compiles,
it renders, and it looks wrong.

## Auto Layout → CSS

| Figma | CSS |
|---|---|
| Auto Layout horizontal | `display: flex; flex-direction: row` |
| Auto Layout vertical | `display: flex; flex-direction: column` |
| Gap | `gap` |
| Padding | `padding` |
| `Fill container` | `flex: 1` or `width: 100%` |
| `Hug contents` | `width: fit-content` |
| `Fixed` | explicit `width`/`height` — flag it, fixed sizing usually breaks responsive |
| Alignment | `justify-content` / `align-items` |
| Absolute position inside Auto Layout | `position: absolute` on child, `position: relative` on parent |
| Wrap enabled | `flex-wrap: wrap` |

A frame without Auto Layout gives no information about responsive intent. Implement it with
the geometry given, and put it in the open-questions list rather than inventing breakpoint
behaviour.

## Tokens

Emit tokens as CSS custom properties on `:root` (or the existing theme scope), then reference
them everywhere. Never inline a value that has a token.

```scss
:root {
  --color-surface-raised: #1a1a1a;
  --space-4: 16px;
  --radius-md: 8px;
}
```

If the repo already has a token layer, extend it and match its naming convention even where
Figma's naming differs — consistency inside the codebase beats fidelity to Figma's names, and
a second parallel token system is worse than an imperfect mapping.

## Typography

Figma text styles become a single class per style, not per-element declarations:

```scss
.type-heading-lg {
  font-family: var(--font-sans);
  font-size: var(--font-size-heading-lg);
  line-height: var(--line-height-heading-lg);
  font-weight: 600;
  letter-spacing: -0.02em;
}
```

Figma line height is often a percentage; convert to a unitless ratio. Letter spacing in Figma
is in px or %; `em` travels better across font sizes. These two are the most common source of
"it looks almost right but the text block is the wrong height".

## Responsive

Figma variables can be mode-scoped (desktop/tablet/mobile). If they are, `get_variable_defs`
returns the modes and the breakpoints follow directly.

If they are not — which is the common case — the design specifies one width and nothing else.
Do not invent breakpoints. Implement the specified width faithfully, use fluid units where the
layout obviously allows it, and list the undefined responsive behaviour as an open question.
Inventing breakpoints produces code that looks finished and is wrong at every size but one.

## Interaction states

Figma variants describe appearance, not behaviour. A `hover` variant tells you what hover looks
like, not whether it applies on touch, or whether it should be suppressed while disabled.

Implement the appearance exactly as drawn. Wire the state to the natural CSS mechanism
(`:hover`, `:focus-visible`, `:active`, `[aria-disabled]`) rather than to component state,
unless the design requires JS-driven transitions.

Transitions are almost never specified in Figma. Unless the file uses Figma Motion — whose
timing values, easing curves and keyframes do come through MCP — do not invent durations.
Ask, or use the repo's existing transition token.

## Assets

### Icons

Check whether the repo already has an icon system — `lucide-angular`, `@ng-icons`, a local
`IconComponent`, an SVG sprite. If it does, map Figma icon names onto it and stop there. Adding
a second icon mechanism next to an existing one is worse than an imperfect name match.

With no icon system, **write each icon to its own file** under the repo's asset directory
(`src/assets/icons/<name>.svg` unless the repo says otherwise), one file per distinct icon,
named after the Figma component. Never paste the same `<svg>` markup into several templates:
a duplicated icon has to be fixed in every copy, and reviewers cannot tell whether two copies
were meant to be identical.

Consume the file in whichever way the repo already handles static SVGs. Two that work:

```html
<!-- Sprite: one HTTP request for all icons, styleable via currentColor -->
<svg class="icon" aria-hidden="true"><use href="assets/icons/sprite.svg#search"></use></svg>
```

```ts
// A small component, if the repo has no sprite pipeline
@Component({
  selector: 'app-icon',
  template: `<svg [attr.aria-hidden]="true"><use [attr.href]="'assets/icons/sprite.svg#' + name()"></use></svg>`,
})
```

Inline `<svg>` markup directly in a component template only when the icon appears exactly once
in the whole design and carries no reuse. Inline is a defensible default only for a one-off.

Whatever the mechanism, the icon must inherit colour from CSS — `fill="currentColor"` or
`stroke="currentColor"`, never a hard-coded hex. An icon with a baked-in colour breaks the
moment it appears on another surface, and that break is invisible until someone looks.

### Images

Decide the format from what the image *is*, never from what Figma happens to hand back. Figma
returns whatever the source layer was, so accepting its default is how a codebase ends up with
a logo as a 400 KB PNG next to the same logo as an SVG.

| Content | Format | Why |
|---|---|---|
| Logos, illustrations, anything vector in Figma | `.svg` | Scales to any density, smaller, styleable |
| Photographs, raster textures | `.webp`, with `.jpg` fallback only if the repo already does that | Far smaller than PNG at the same quality |
| Raster that needs real transparency | `.png` | The only raster case where PNG is the right answer |

Export raster at **2x** for a 1x layout slot, and record the intended display size — a 2x export
consumed without width/height attributes is a layout shift waiting to happen.

Write images under the repo's existing asset directory (`src/assets/images/` unless the repo
says otherwise), named after the Figma layer in `kebab-case`. Never keep Figma's exported
filename: hashes and names like `Group 47.png` tell a reviewer nothing about what the file is.

Every `<img>` needs explicit `width` and `height` attributes and a meaningful `alt`. Decorative
images take `alt=""` — an empty alt is a deliberate statement to a screen reader, a missing one
is a bug.

**Report what you exported, grouped by destination component, not by file type.** A list sorted
by extension tells the reader nothing about whether anything is missing; a list under the
component that uses each file is checkable against the manifest.

If an image already exists in the repo, reuse it rather than exporting a second copy under a
different name.

## Accessibility

Figma rarely specifies this, so it comes from the implementation:

- Semantic elements: `<button>` for buttons, `<nav>` for navigation. A styled `<div>` with a
  click handler is a defect regardless of how closely it matches the design.
- `aria-label` on icon-only variants — an icon-only button with no accessible name is unusable
  with a screen reader, and it's the variant most likely to ship without one.
- Focus states: if the design has no focus variant, implement `:focus-visible` anyway and flag
  it. Never remove a focus ring to match a design that omitted it.
- Colour contrast: check text tokens against their surfaces. Report failures rather than
  silently adjusting the designer's colours.
