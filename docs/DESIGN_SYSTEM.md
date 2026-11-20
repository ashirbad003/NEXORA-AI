# NEXORA AI - UI/UX Design System Specification

**Design Direction:** Cybernetic Obsidian — Futuristic, Technically Sophisticated, Minimalist, Accessible.

---

## 1. Visual Identity & Color Palette

### Core Tokens:
- **Obsidian Dark (Base Background):** `#060913`
- **Surface Elevation 1 (Card Background):** `#0c1222`
- **Surface Elevation 2 (Elevated Modals & Drawers):** `#131b31`
- **Obsidian Border (Subtle Dividers):** `#1e293b`
- **Cyber Lime (Primary Action & Accent):** `#a3e635`
  - Hover: `#84cc16`
  - Subtle Glow: `rgba(163, 230, 53, 0.15)`
- **Tech Violet (Intelligence & Secondary Accent):** `#8b5cf6`
  - Hover: `#7c3aed`
  - Subtle Glow: `rgba(139, 92, 246, 0.15)`
- **Typography Colors:**
  - Primary Headings & High Contrast Text: `#f8fafc` (Slate 50)
  - Secondary Body & Subtitles: `#94a3b8` (Slate 400)
  - Muted Captions & Placeholders: `#64748b` (Slate 500)

---

## 2. Typography Hierarchy

- **Font Family Sans:** Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Font Family Mono:** JetBrains Mono, Fira Code, Consolas, monospace (used in Monaco Editor, Code Review, and Terminal views)
- **Scale:**
  - Hero Header: 48px - 72px / Bold 800
  - Section Header: 30px - 36px / SemiBold 600
  - Card Title: 18px - 20px / Medium 500
  - Body Regular: 14px - 16px / Normal 400 (Line height 1.6)
  - Caption / Metadata: 12px / Normal 400

---

## 3. UI Component Primitives

1. **Button:**
   - `primary`: Cyber Lime background with Obsidian text and subtle glow (`shadow-cyber-glow`).
   - `secondary`: Tech Violet background with white text and violet glow (`shadow-tech-glow`).
   - `outline`: Obsidian Card background with subtle slate border; highlights Cyber Lime on hover.
   - `ghost`: Transparent background with subtle hover background highlight.
   - All buttons feature accessible focus rings (`focus:ring-2`) and loading spinner state indicators.

2. **Card:**
   - Rounded border (`rounded-xl`), Obsidian Card surface (`#0c1222`), 1px border.
   - Optional glow states: `glow="cyber"`, `glow="violet"`, or `glow="none"`.

3. **Badge:**
   - Pill-shaped (`rounded-full`) tags for status indicators, difficulty badges (Easy, Medium, Hard), and track indicators.

---

## 4. Usability & Accessibility Rules

- **Contrast Ratio:** All primary text on Obsidian background exceeds WCAG AAA (contrast ratio > 7:1).
- **Reduced Motion:** Interactive transitions use subtle 200ms easing (`transition-all duration-200`) without disorienting layout shifts.
- **State Feedback:** Every interactive element has explicit `:hover`, `:focus-visible`, and `:disabled` styling.
