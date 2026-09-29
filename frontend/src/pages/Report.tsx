import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  ListChecks,
  ScanSearch,
} from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import ErpFlags from "@/components/ErpFlags";
import MatchRateChart from "@/components/MatchRateChart";
import ReadinessScore from "@/components/ReadinessScore";
import Recommendations from "@/components/Recommendations";
import UnmatchedTable from "@/components/UnmatchedTable";
import UnitMismatchList from "@/components/UnitMismatchList";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { REPORT_QUERY_KEY, restoreReport } from "@/lib/api";
import type { ReadinessReport } from "@/lib/types";

type ReportState = { status: "ready"; report: ReadinessReport } | { status: "missing" };

function useReportState(): ReportState {
  const queryClient = useQueryClient();
  const cached = queryClient.getQueryData<ReadinessReport>(REPORT_QUERY_KEY);
  if (cached !== undefined) return { status: "ready", report: cached };
  const restored = restoreReport();
  return restored === null ? { status: "missing" } : { status: "ready", report: restored };
}

interface SummaryRow {
  icon: typeof FileText;
  label: string;
  value: number;
}

function analysisRows(report: ReadinessReport): SummaryRow[] {
  return [
    { icon: FileText, label: "Documents processed", value: report.documents_processed },
    { icon: ScanSearch, label: "Line items extracted", value: report.total_line_items },
    { icon: ListChecks, label: "Matched to catalog", value: report.matched_items },
    { icon: CheckCircle2, label: "Unmatched", value: report.total_line_items - report.matched_items },
  ];
}

export default function Report() {
  const state = useReportState();
  if (state.status === "missing") return <Navigate to="/" replace />;
  const { report } = state;

  return (
    <main className="mx-auto w-full max-w-4xl px-4 pb-16 pt-8 sm:pt-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">Readiness report</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Based on the purchase orders and catalog you uploaded.
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/">
            <ArrowLeft className="size-4" aria-hidden="true" />
            Analyze another
          </Link>
        </Button>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <ReadinessScore report={report} />
        <MatchRateChart
          matchedItems={report.matched_items}
          totalItems={report.total_line_items}
          matchRate={report.match_rate}
        />
        <Card className="h-full">
          <CardHeader>
            <CardTitle>Analysis summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {analysisRows(report).map((row) => (
              <div key={row.label} className="flex items-center justify-between gap-3 text-sm">
                <span className="flex items-center gap-2 text-muted-foreground">
                  <row.icon className="size-4" aria-hidden="true" />
                  {row.label}
                </span>
                <span className="font-medium tabular-nums">{row.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {report.recommendations.length > 0 ? (
        <div className="mt-4">
          <Recommendations recommendations={report.recommendations} />
        </div>
      ) : null}

      {report.unit_mismatches.length > 0 ? (
        <div className="mt-8">
          <UnitMismatchList mismatches={report.unit_mismatches} />
        </div>
      ) : null}

      {report.erp_mapping_flags.length > 0 ? (
        <div className="mt-8">
          <ErpFlags flags={report.erp_mapping_flags} />
        </div>
      ) : null}

      <div className="mt-8">
        {report.catalog_gaps.length > 0 ? (
          <UnmatchedTable gaps={report.catalog_gaps} />
        ) : (
          <Card>
            <CardContent className="flex items-center gap-3 p-5 text-sm">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-600" aria-hidden="true" />
              <p>
                Every extracted line item matched a catalog SKU above the threshold —
                no catalog gaps were found.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
      <Separator className="mt-10" />
      <p className="mt-4 text-xs text-muted-foreground">
        Comena Onboarding Readiness Auditor — results are indicative and based only on
        the uploaded samples.
      </p>
    </main>
  );
}
