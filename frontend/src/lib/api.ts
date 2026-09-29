import { z } from "zod";
import { readinessReportSchema, type ReadinessReport } from "./types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const stringDetailSchema = z.object({ detail: z.string() });
const fieldDetailSchema = z.object({
  detail: z.array(z.object({ msg: z.string(), loc: z.array(z.union([z.string(), z.number()])) })),
});

function extractErrorDetail(payload: unknown): string | null {
  const text = stringDetailSchema.safeParse(payload);
  if (text.success) return text.data.detail;
  const fields = fieldDetailSchema.safeParse(payload);
  if (fields.success) {
    return fields.data.detail.map((issue) => issue.msg).join("; ");
  }
  return null;
}

export async function analyzeReadiness(pdfs: File[], catalog: File): Promise<ReadinessReport> {
  const body = new FormData();
  for (const pdf of pdfs) {
    body.append("pdfs", pdf);
  }
  body.append("catalog", catalog);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, { method: "POST", body });
  } catch {
    throw new ApiError("Could not reach the analysis service. Is the backend running?", 0);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      extractErrorDetail(payload) ?? `Analysis failed with status ${response.status}.`,
      response.status,
    );
  }

  const result = readinessReportSchema.safeParse(payload);
  if (!result.success) {
    throw new ApiError("The analysis service returned an unexpected response format.", response.status);
  }
  return result.data;
}

export const REPORT_QUERY_KEY = ["report"] as const;

const REPORT_STORAGE_KEY = "comena:readiness-report";

export function storeReport(report: ReadinessReport): void {
  sessionStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(report));
}

export function restoreReport(): ReadinessReport | null {
  const raw = sessionStorage.getItem(REPORT_STORAGE_KEY);
  if (raw === null) return null;
  try {
    const parsed = readinessReportSchema.safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}
