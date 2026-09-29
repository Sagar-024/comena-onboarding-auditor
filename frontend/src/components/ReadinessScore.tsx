import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { ReadinessReport } from "@/lib/types";

interface ReadinessScoreProps {
  report: ReadinessReport;
}

interface ScoreBand {
  label: string;
  text: string;
  bar: string;
}

function scoreBand(score: number): ScoreBand {
  if (score >= 90) {
    return { label: "Ready for automation", text: "text-emerald-600", bar: "[&>div]:bg-emerald-500" };
  }
  if (score >= 70) {
    return { label: "Review before go-live", text: "text-amber-600", bar: "[&>div]:bg-amber-500" };
  }
  return { label: "Enrich catalog first", text: "text-red-600", bar: "[&>div]:bg-red-500" };
}

export default function ReadinessScore({ report }: ReadinessScoreProps) {
  const band = scoreBand(report.overall_score);
  const summary = `${report.matched_items} of ${report.total_line_items} line items matched across ${report.documents_processed} ${report.documents_processed === 1 ? "document" : "documents"}.`;

  return (
    <Card className="h-full">
      <CardContent className="space-y-4 p-5 sm:p-6">
        <div>
          <p className="text-sm text-muted-foreground">Overall readiness</p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className={`text-5xl font-semibold tracking-tight tabular-nums ${band.text}`}>
              {report.overall_score}
            </span>
            <span className="text-sm text-muted-foreground">/ 100</span>
          </div>
          <p className={`mt-1 text-sm font-medium ${band.text}`}>{band.label}</p>
        </div>
        <Progress value={report.overall_score} className={`h-2 ${band.bar}`} />
        <p className="text-sm leading-5 text-muted-foreground">{summary}</p>
      </CardContent>
    </Card>
  );
}
