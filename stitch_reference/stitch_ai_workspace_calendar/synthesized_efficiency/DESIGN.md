---
name: Synthesized Efficiency
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1c'
  surface-container: '#202020'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c3c6d7'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#303030'
  outline: '#8d90a0'
  outline-variant: '#434655'
  surface-tint: '#b4c5ff'
  primary: '#b4c5ff'
  on-primary: '#002a78'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#0053db'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#bec6e0'
  on-tertiary: '#283044'
  tertiary-container: '#656d84'
  on-tertiary-container: '#eef0ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353535'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
  mono-ui:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar-width-mobile: 64px
  ai-panel-height-mobile: 40%
  gutter: 12px
  base-unit: 4px
  margin-safe: 16px
---

## Brand & Style

The design system is engineered for high-performance productivity, targeting professionals who manage complex schedules across multiple platforms. The personality is "Intelligent Precision"—combining the technical, high-density utility of a code editor with the refined polish of a modern enterprise application.

The design style is **Corporate Modern with a Developer-Centric edge**. It prioritizes information density, utilizing a crisp, structured interface that avoids unnecessary decorative elements. The UI should evoke a sense of calm control, clarity, and systematic organization, making "AI Calendar" feel like a professional IDE for time management rather than a consumer social app.

## Colors

The palette is anchored in a professional dark mode inspired by modern IDE environments. 

- **Primary (Enterprise Blue):** Used for primary actions, current day indicators, and core navigation highlights. It represents reliability and professional standard.
- **Secondary (AI Purple):** Reserved specifically for AI-generated insights, smart scheduling suggestions, and the AI chat interface. It signals "intelligence" and distinguishes automated actions from manual ones.
- **Backgrounds:** Utilizes a tiered neutral system. The main workspace sits on `#0F172A` (Slate 950), while sidebars and panels use `#1E1E1E` to provide a subtle structural contrast.
- **Status Colors:** Standardized semantic colors (Success Green, Warning Amber, Error Red) are used for integration status indicators (e.g., Google/Outlook sync states).

## Typography

This design system utilizes a dual-font approach to balance readability with a technical aesthetic. 

**Inter** is the workhorse for all content, body text, and headings, chosen for its exceptional legibility in data-dense environments. **Geist** is used for labels, metadata, and the AI chat interface to provide a "developer-tool" feel that aligns with the VS Code-inspired narrative.

To maintain high density on mobile:
- Use **label-sm** for secondary metadata like time-stamps or integration names.
- Use **mono-ui** for status indicators and technical details to emphasize the "utility" aspect.
- Headlines are kept compact to maximize the vertical space for calendar events.

## Layout & Spacing

The layout follows a **3-panel split concept** optimized for a high-density mobile experience.

1.  **Source Sidebar (Left):** On mobile, this collapses into a narrow rail (64px) showing only integration icons (Google, Outlook) and core view switchers.
2.  **Calendar View (Center):** The primary focus. Uses a fluid grid where time blocks are defined by a strict 4px base unit. 
3.  **AI/Detail Panel (Right/Bottom):** On mobile, this transforms from a side panel into a bottom sheet that can be toggled or anchored.

**Grid Philosophy:** Use a 12-column grid for tablet/desktop, but on mobile, rely on a "Paneled" approach. Panes are separated by 1px borders rather than wide gutters to preserve screen real estate.

## Elevation & Depth

This design system shuns heavy shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**. 

- **Level 0 (Base):** The darkest layer (`#0F172A`), used for the main calendar background.
- **Level 1 (Panels):** Sidebars and bottom sheets use `#1E1E1E` with a subtle 1px border of `#334155`.
- **Level 2 (Popovers/Modals):** Elements that float above the UI use a slightly lighter surface with a 10% primary-tinted stroke.
- **Active State:** Instead of a shadow, active calendar events or selected time slots use a high-opacity border of the Primary Blue or AI Purple to indicate focus.

## Shapes

The shape language is **Soft (0.25rem)**. This ensures the UI feels professional and precise. 

- **Small elements (Buttons, Chips):** Use a 4px corner radius.
- **Containers (Cards, AI Chat Box):** Use an 8px radius (`rounded-lg`).
- **Interactive States:** Hover or focus states on the calendar grid remain sharp-edged to align with the time-block boundaries, while the content inside them respects the 4px radius.

## Components

### AI Chat Input
A dedicated area at the bottom of the AI Panel. It features a persistent `#8B5CF6` (AI Purple) accent. The input box uses a monospaced font for the prompt to reinforce the "command line" efficiency of the AI.

### Calendar Events
High-density blocks. Each block must include:
- A 2px left-border color-coded to the source (e.g., Blue for Work, Purple for AI-suggested).
- High-contrast text (`#FFFFFF`) for the title.
- Small integration icons in the top right corner (12x12px).

### Status Indicators
Small circular pips next to integration names in the sidebar rail.
- **Connected:** Pulsing Green.
- **Syncing:** Rotating Neutral.
- **Error:** Static Red.

### Buttons
- **Primary:** Solid Blue, no gradients, white text.
- **Ghost:** Transparent background with a 1px Slate-700 border. Used for secondary navigation actions.
- **AI Action:** Solid Purple, used exclusively for "Apply AI Suggestion" or "Schedule with AI".

### Lists
High-density row items with a 40px height. Each row uses a 1px bottom border to separate items, maximizing the number of visible items on mobile screens.