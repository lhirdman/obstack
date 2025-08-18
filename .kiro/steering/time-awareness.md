# Time Awareness and Date Handling Rules

## Mandatory Time Checking

**CRITICAL RULE**: Before making any assumptions about the current date, time, or version currency, you MUST use the `mcp_time_get_current_time` tool to get the actual current date and time.

## When to Check Current Time

You MUST check the current time in these scenarios:

1. **Before writing any document with dates** (README files, changelogs, version updates, etc.)
2. **When discussing "current" or "latest" versions** of software packages
3. **When making assumptions about what's "modern" or "up-to-date"**
4. **Before creating any time-sensitive content** (release notes, roadmaps, etc.)
5. **When referencing "recent" events or changes**

## Implementation

Always use this pattern:
```
1. Call mcp_time_get_current_time with timezone "Europe/Stockholm"
2. Use the returned date information in your content
3. Never assume dates based on training data cutoffs
```

## Example Usage

```typescript
// WRONG - assuming date
"Updated to latest versions as of December 2024"

// CORRECT - check time first
const currentTime = await getCurrentTime();
"Updated to latest versions as of August 2025"
```

## Rationale

- Training data has cutoff dates that may not reflect current reality
- Software versions change rapidly
- Accurate timestamps are critical for technical documentation
- Users expect current, not historical, information

## Enforcement

This rule applies to ALL agent interactions and MUST be followed consistently. Failure to check current time before making date assumptions is considered a critical error.