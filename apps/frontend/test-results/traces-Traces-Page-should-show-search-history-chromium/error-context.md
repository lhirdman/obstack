# Page snapshot

```yaml
- navigation:
  - link "ObservaStack":
    - /url: /
  - link "Dashboard":
    - /url: /
  - link "Metrics":
    - /url: /metrics
  - link "Traces":
    - /url: /traces
  - button "Logout"
- heading "Traces" [level=1]
- paragraph: Search and visualize distributed traces to understand request flows and performance
- heading "Trace Search" [level=2]
- text: Trace ID
- textbox "Trace ID": 1234567890abcdef
- button
- paragraph: Valid trace ID format
- button "Search Trace"
- text: Press Enter to search
- heading "Recent Searches" [level=3]
- button "1234567890abcdef"
- heading "Search Tips" [level=4]
- list:
  - listitem: • Trace IDs are hexadecimal strings (0-9, a-f)
  - listitem: • Typical length is 16 or 32 characters
  - listitem: • You can only search traces from your tenant
  - listitem: • Recent searches are saved for quick access
- heading "Trace Waterfall" [level=2]
- text: "2 spans Total Duration:1.00s Spans:2 Start Time:01:00:00.000 Services:1 0ms250.00ms500.00ms750.00ms1.00s frontendGET /api/users 1.00s 1.00s Start: 01:00:00.000GET /api/users abcdef12... frontenddatabase query 700.00ms 700.00ms Start: 01:00:00.100DB Query fedcba09..."
- heading "Legend" [level=4]
- text: Success Warning Error Colors represent different services Indentation shows span hierarchy
- heading "Span Details" [level=2]
- img
- paragraph: Click on a span in the waterfall to view its details
```