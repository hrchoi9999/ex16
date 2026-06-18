# Developer Handover Guide: AI Calendar Project

## 1. Design System & Tokens
- **Theme Support**: The project supports both Dark (default) and Light modes.
- **Colors**: Use the extracted CSS variables from `{{DATA:DESIGN_SYSTEM:DESIGN_SYSTEM_1}}` (Light) and `{{DATA:DESIGN_SYSTEM:DESIGN_SYSTEM_2}}` (Dark).
- **Typography**: Hanken Grotesk / Inter (refer to design system docs for weight and scale).
- **Icons**: Material Symbols (Rounded) are used throughout.

## 2. Layout Architecture (3-Panel Workspace)
- **Sidebars**: Fixed width (approx. 240px - 320px depending on screen size).
- **Main Content**: Fluid layout for the calendar grid.
- **Responsiveness**: PC screens use a 3-column flex/grid container. Mobile screens collapse sidebars into bottom sheets or drawer menus as seen in the mobile mockups.

## 3. Key Components
- **AI Command Bar**: Persistent input field with autocomplete and AI status indicators.
- **Calendar Grid**: Needs to handle drag-and-drop and real-time sync updates.
- **Insight Cards**: Use elevated surfaces with `border-outline-variant` in Light mode and `surface-bright` in Dark mode.

## 4. Integration Logic
- The UI mimics VS Code's activity bar for source switching (Google, Outlook, etc.).
- Sync status is indicated by a green dot or progress bar within the sidebar.
