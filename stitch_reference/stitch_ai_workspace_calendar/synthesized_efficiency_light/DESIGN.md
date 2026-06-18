---
name: Synthesized Efficiency (Light)
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434655'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#712ae2'
  on-secondary: '#ffffff'
  secondary-container: '#8a4cfc'
  on-secondary-container: '#fffbff'
  tertiary: '#4d556b'
  on-tertiary: '#ffffff'
  tertiary-container: '#656d84'
  on-tertiary-container: '#eef0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bbff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5a00c6'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  max-width: 1440px
---

## Brand & Style
The design system focuses on high-clarity information architecture and professional rigor. The transition to a light-mode foundation emphasizes daylight readability and an "editor-first" environment. The brand personality is precise, systematic, and reliable, catering to power users who require long-duration focus without visual fatigue.

The design style is **Corporate / Modern** with a lean towards **Minimalism**. It utilizes expansive white space, subtle tonal shifts to define hierarchy, and crisp typography to create a sense of organized efficiency. The emotional response is one of calm control and technical proficiency.

## Colors
The palette is anchored by a high-contrast base of Pure White (`#ffffff`) for primary canvases and Slate Gray scales for UI scaffolding. 

- **Primary Blue (#2563eb):** Reserved for primary actions, active states, and key progress indicators.
- **Accent Purple (#7c3aed):** Used for secondary features, data visualization highlights, and innovative toolsets.
- **Neutrals:** We use a "Slate" scale. `Slate-900` is used for primary text to ensure WCAG AAA compliance against white backgrounds. `Slate-100` and `Slate-200` are utilized for non-interactive borders and secondary surface backgrounds.
- **Semantic Colors:** Success (Emerald), Warning (Amber), and Error (Rose) are applied with high saturation to remain distinct against the light interface.

## Typography
Typography is the primary driver of hierarchy in this system. 

**Hanken Grotesk** provides a sharp, contemporary feel for headings. It should be set with tighter letter-spacing in larger sizes to maintain visual density. **Inter** is the workhorse for all body copy and UI strings, chosen for its exceptional legibility and neutral tone. **JetBrains Mono** is used sparingly for labels, metadata, and technical values to reinforce the "synthesized" and precise nature of the product. 

For light mode, font weights are slightly heavier for small body text than they would be in dark mode to compensate for the "thinning" effect of dark text on light backgrounds.

## Layout & Spacing
The system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. 

A strict 4px baseline grid governs all vertical rhythm. Layouts should prioritize "Top-Down, Left-to-Right" reading flows. Padding within containers is generous to prevent information density from feeling overwhelming. Use `lg` (24px) spacing for primary grouping of elements and `md` (16px) for internal component spacing.

On desktop, content should be capped at a `max-width` of 1440px to ensure line lengths remain readable for text-heavy views.

## Elevation & Depth
In light mode, depth is conveyed through **Tonal Layers** and **Low-contrast Outlines** rather than heavy shadows.

- **Level 0 (Background):** `#ffffff` - The main canvas.
- **Level 1 (Surface):** `#f8fafc` - Used for sidebars, cards, and secondary panels.
- **Level 2 (Overlay):** `#ffffff` with a very soft, high-diffusion shadow (`0 4px 12px rgba(15, 23, 42, 0.05)`). Used for menus and modals.

Borders are the primary tool for separation. Use a 1px border of `#e2e8f0` for almost all container divisions. This creates a "blueprint" feel that is clean and structured.

## Shapes
The shape language is **Soft**. A base radius of `0.25rem` (4px) is applied to buttons and input fields to maintain a professional, slightly architectural edge. Larger components like cards or modals use `0.5rem` (8px). 

Avoid fully rounded "pill" shapes unless used for status tags (Chips), where the distinct shape helps differentiate the element from interactive buttons.

## Components
- **Buttons:** Primary buttons use `#2563eb` with white text. Secondary buttons use a white fill with a `#e2e8f0` border and `#0f172a` text. Ghost buttons use no background but show a `#f1f5f9` fill on hover.
- **Input Fields:** Use a `#ffffff` background with a 1px border of `#cbd5e1`. On focus, the border transitions to `#2563eb` with a subtle 2px outer glow of the same color at 10% opacity.
- **Chips/Tags:** Use a background of `#f1f5f9` and text of `#475569`. For active or selected states, use primary blue at 10% opacity with solid blue text.
- **Cards:** Cards should have no shadow by default, relying on a 1px border of `#e2e8f0`. On hover, they may lift slightly with a very soft shadow and a border shift to `#cbd5e1`.
- **Lists:** Use subtle horizontal dividers (`#f1f5f9`). Alternating row colors are not recommended; use hover states to highlight rows instead.
- **Progress Bars:** Use a light gray track (`#f1f5f9`) with a primary blue or accent purple fill.