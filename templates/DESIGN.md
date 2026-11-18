# DESIGN — <project>

Single source of truth for visual and interaction rules. Only the coordinator edits this file; user decisions
are written here with their date.

## 1. Character
<One paragraph: what the product feels like, what it refuses (e.g. default Material look, decorative
gradients/illustrations, colour that means two things).>

## 2. Colour
- Neutral surfaces + one accent. Status colours only with text or an icon.
- Contrast: 4.5:1 body text, 3:1 icons and large text, in every theme.

## 3. Type, spacing, shape
- Type scale: <sizes>. Spacing: 4 / 8 / 12 / 16 / 24. Touch targets ≥ 44×44.
- Corner radii: <values>. Lines: <hairline width>.

## 4. Motion
- <Duration, curve>. Reduce Motion → 0. No loops except <the one allowed indeterminate indicator>.

## 5. Components
- Own component layer: <list>. New UI uses it, not raw framework widgets.

## 6. Screens
<Per screen: hierarchy, primary action, empty state, errors.>

## 7. Exceptions (dated)
- <YYYY-MM-DD: decision, why, limits.>
