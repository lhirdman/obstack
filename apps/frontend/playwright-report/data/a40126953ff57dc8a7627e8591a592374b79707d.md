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
- textbox "Trace ID": invalid-trace-id
- button
- paragraph: Trace ID should be a hexadecimal string (16-32 characters)
- button "Search Trace"
- text: Press Enter to search
- heading "Search Tips" [level=4]
- list:
  - listitem: • Trace IDs are hexadecimal strings (0-9, a-f)
  - listitem: • Typical length is 16 or 32 characters
  - listitem: • You can only search traces from your tenant
  - listitem: • Recent searches are saved for quick access
- heading "Trace Waterfall" [level=2]
- heading "No trace selected" [level=3]
- paragraph: Enter a trace ID above to view the distributed trace waterfall.
- heading "Span Details" [level=2]
- img
- paragraph: Click on a span in the waterfall to view its details
```