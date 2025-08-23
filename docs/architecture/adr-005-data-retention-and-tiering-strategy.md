# ADR-005: Data Retention and Tiering Strategy

**Date:** 2025-08-22

**Status:** Proposed

## Context

As decided in previous ADRs and architectural discussions, we will be unifying all long-term telemetry data (logs, metrics, traces, synthetic results, etc.) into a central OpenSearch cluster. While this provides immense analytical power, OpenSearch's storage footprint is significantly larger than that of purpose-built time-series databases (like Prometheus) or log-optimized stores (like Loki).

To ensure the platform remains cost-effective, especially when deployed in a public cloud environment, we must have a proactive strategy to manage data storage costs without sacrificing essential analytical capabilities.

## Decision

We will implement a multi-tiered data storage strategy for all time-series data stored in OpenSearch, automated by its built-in **Index Lifecycle Management (ILM)** feature. This strategy will automatically transition data through different storage tiers based on its age, balancing performance, accessibility, and cost.

The defined lifecycle will be as follows:

1.  **Hot Tier (0-14 Days):**
    *   **Purpose:** Ingesting new data and serving the most frequent queries for immediate troubleshooting and analysis.
    *   **Storage:** High-performance, low-latency local SSDs (e.g., AWS I3en/I4i instances). This is the most expensive tier.
    *   **Action:** New daily indices are created in this tier.

2.  **Warm Tier (15-90 Days):**
    *   **Purpose:** Storing data that is still relevant and searchable but accessed less frequently.
    *   **Storage:** Lower-cost, storage-dense nodes, typically with HDDs (e.g., AWS D3 instances).
    *   **Action:** ILM will automatically migrate indices from Hot to Warm nodes. The indices may be shrunk to fewer shards and force-merged to reduce their resource footprint.

3.  **Cold Tier (91-365 Days):**
    *   **Purpose:** Long-term archival for compliance and deep, infrequent analysis.
    *   **Storage:** Ultra-low-cost object storage (e.g., Amazon S3, MinIO). Data is stored as **Searchable Snapshots**.
    *   **Action:** ILM will automatically move indices to this tier. The data remains queryable directly from object storage, albeit with higher latency.

4.  **Delete Phase (>365 Days):**
    *   **Purpose:** To enforce a final retention policy and prevent indefinite storage costs.
    *   **Action:** ILM will automatically and permanently delete indices after they exceed the maximum retention period.

Additionally, we will employ **Rollups** for metric data, summarizing high-granularity data into lower-resolution aggregates (e.g., 1-minute or 1-hour averages) for long-term trend analysis, allowing the original high-resolution data to be deleted sooner.

### Long-Term Log Metrics via Recording Rules

To address the performance and cost challenges of generating metrics from raw logs over long time periods, we will leverage **Loki Recording Rules**.

-   **Mechanism:** LogQL queries that calculate a metric from log data (e.g., counting application errors) will be configured as Recording Rules. Loki will execute these queries at regular intervals.
-   **Output:** The result of the rule is not a log line, but a new time-series metric. This metric will be written to our central **Prometheus** instance.
-   **Storage & Unification:** Prometheus will store this pre-aggregated metric efficiently and forward it to **OpenSearch** via its `remote_write` configuration.

This pattern allows us to create fast, efficient, long-term dashboards based on log data by querying the highly optimized and pre-calculated metrics in Prometheus and OpenSearch, rather than performing expensive queries against raw log files in Loki.

## Consequences

**Positive:**

-   **Significant Cost Reduction:** This strategy directly addresses the primary concern of OpenSearch storage costs, making the unified analytics approach economically viable at scale.
-   **Balanced Performance:** Keeps the most recent, relevant data on the fastest hardware for the best user experience, while transparently moving older data to more economical storage.
-   **Automated & Scalable:** ILM policies are a "set and forget" feature. The process is fully automated and scales with the volume of data.
-   **Data Compliance:** Provides a clear, enforceable retention policy, which is often a requirement for enterprise customers.

**Negative:**

-   **Increased Operational Complexity:** Requires careful configuration and monitoring of the ILM policies and the different hardware tiers (Hot/Warm/Cold nodes).
-   **Variable Query Performance:** Users will experience slower query times for data in the Warm and especially the Cold tiers. This is an expected trade-off that must be clearly communicated in the UI.

---
