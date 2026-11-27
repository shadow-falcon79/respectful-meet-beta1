import { apiGet } from "./client";

// The export shape is intentionally loose here (unknown, not a strict
// interface): it's a one-off download the user opens as JSON, not data the
// app renders or relies on structurally, so there is nothing to gain from
// duplicating the full backend schema client-side and something to lose
// (drifting silently out of sync with app/api/v1/privacy.py).
export function fetchMyDataExport(): Promise<Record<string, unknown>> {
  return apiGet<Record<string, unknown>>("/privacy/export");
}
