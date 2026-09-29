import { z } from "zod";

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
export const MAX_FILE_SIZE_MB = MAX_FILE_SIZE_BYTES / (1024 * 1024);

export const unitMismatchSchema = z.object({
  sku: z.string(),
  description: z.string(),
  po_unit: z.string(),
  catalog_unit: z.string(),
});
export type UnitMismatch = z.infer<typeof unitMismatchSchema>;

export const catalogGapSchema = z.object({
  description: z.string(),
  best_candidate_sku: z.string().nullable(),
  best_candidate_score: z.number().nullable(),
});
export type CatalogGap = z.infer<typeof catalogGapSchema>;

/**
 * Mirrors backend/app/models/schemas.py exactly. The backend response has no
 * per-document payload — `catalog_gaps` and `unit_mismatches` carry the
 * per-line detail the report UI needs.
 */
export const readinessReportSchema = z.object({
  documents_processed: z.number(),
  total_line_items: z.number(),
  matched_items: z.number(),
  match_rate: z.number(),
  overall_score: z.number(),
  unmatched_descriptions: z.array(z.string()),
  catalog_gaps: z.array(catalogGapSchema),
  unit_mismatches: z.array(unitMismatchSchema),
  erp_mapping_flags: z.array(z.string()),
  recommendations: z.array(z.string()),
});
export type ReadinessReport = z.infer<typeof readinessReportSchema>;
