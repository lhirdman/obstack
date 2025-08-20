### AI UI Generation Prompt: Obstack Main Dashboard

**1. High-Level Goal:**

Create a responsive, dark-mode dashboard screen for an observability platform called "Obstack". This screen is the main landing page after a user logs in. It should provide a high-level, at-a-glance view of system health, active alerts, and infrastructure costs. The design must be clean, modern, data-dense, and professional, targeting an audience of DevOps engineers and developers.

**2. Detailed, Step-by-Step Instructions:**

1.  **Tech Stack:** Use **React** with **TypeScript** and **Tailwind CSS**. All components should be functional components using hooks. Use **Heroicons** for all icons.
2.  **Overall Layout:**
    *   Create a main application shell with a persistent vertical navigation rail on the left and a main content area on the right.
    *   The background color for the entire application should be a dark gray (`#111827`).
3.  **Left Navigation Rail:**
    *   The navigation rail should be approximately 60px wide.
    *   It should contain a list of icon-only links for the primary views: Dashboard, Search, Logs, Metrics, Traces, Alerts, and Cost Insights.
    *   Use the "outline" style from Heroicons for these. For example, a chart bar icon for Dashboard, a magnifying glass for Search, etc.
    *   The currently active link should have a different background color or a colored left border to indicate it's selected. Use the primary indigo color (`#4F46E5`) for the active state.
4.  **Main Content Area - Header:**
    *   At the top of the main content area, create a header.
    *   This header must contain a prominent **Unified Search Bar**.
    *   To the right of the search bar, add a **Global Time Range Selector** button (e.g., a dropdown button that says "Last 15 minutes").
5.  **Main Content Area - Dashboard Grid:**
    *   Below the header, create a responsive grid of widgets. On desktop, this should be a 2 or 3-column grid. On mobile, the widgets should stack vertically into a single column.
    *   **Widget 1: Active Alerts Summary:**
        *   Title: "Active Alerts"
        *   Content: Display counts for "Critical" and "Warning" alerts with corresponding red (`#EF4444`) and amber (`#F59E0B`) colored icons.
        *   Make the entire widget clickable.
    *   **Widget 2: API Latency (p95):**
        *   Title: "API Latency (p95)"
        *   Content: Display a time-series **Line Chart**. The line should be the primary indigo color (`#4F46E5`). The background of the chart should be a slightly lighter gray than the main background.
    *   **Widget 3: API Error Rate:**
        *   Title: "API Error Rate (%)"
        *   Content: Display another time-series **Line Chart**. The line should be the error red color (`#EF4444`).
    *   **Widget 4: Cost Overview:**
        *   Title: "Current Infrastructure Cost"
        *   Content: Display a large metric showing the current hourly or daily cost (e.g., "$5.72/hr"). Below it, show a small **Bar Chart** breaking down the cost by the top 3 namespaces.

**3. Code Examples, Data Structures & Constraints:**

*   **Styling:** Use **Tailwind CSS** for ALL styling. Do not use any other styling libraries like Material-UI, CSS-in-JS, or custom CSS files.
*   **Colors:**
    *   Background: `#111827`
    *   Primary/Indigo: `#4F46E5`
    *   Error/Red: `#EF4444`
    *   Warning/Amber: `#F59E0B`
    *   Text: A light gray or white that meets WCAG AA contrast ratios against the dark background.
*   **Fonts:** Use a standard sans-serif font stack (`Inter` is preferred if available).
*   **Data:** The charts can be populated with placeholder or static data for now. The focus is on the UI structure and style.
*   **Constraints:** Do NOT implement the functionality for the search bar or time range selector; focus only on the UI elements. Do NOT build any other screens.

**4. Define a Strict Scope:**

You should only create the components necessary for this single dashboard screen. The expected output is a single React component (e.g., `DashboardScreen.tsx`) that contains the layout and all the widgets described above. You can break the widgets into smaller sub-components if you wish. Do not create any routing or state management logic.
