import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MatchRateChartProps {
  matchedItems: number;
  totalItems: number;
  matchRate: number;
}

const MATCHED_COLOR = "#10b981";
const UNMATCHED_COLOR = "#d4d4d8";

export default function MatchRateChart({ matchedItems, totalItems, matchRate }: MatchRateChartProps) {
  const unmatchedItems = Math.max(0, totalItems - matchedItems);
  const segments = [
    { name: "Matched", value: matchedItems, fill: MATCHED_COLOR },
    { name: "Unmatched", value: unmatchedItems, fill: UNMATCHED_COLOR },
  ].filter((segment) => segment.value > 0);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Match rate</CardTitle>
      </CardHeader>
      <CardContent>
        {totalItems === 0 ? (
          <p className="text-sm leading-5 text-muted-foreground">
            No line items were extracted from the uploaded documents, so there is
            nothing to match yet.
          </p>
        ) : (
          <>
            <div className="relative mx-auto h-40 w-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={segments}
                    dataKey="value"
                    innerRadius="70%"
                    outerRadius="98%"
                    startAngle={90}
                    endAngle={-270}
                    strokeWidth={0}
                    isAnimationActive={false}
                  >
                    {segments.map((segment) => (
                      <Cell key={segment.name} fill={segment.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-semibold tabular-nums">
                  {Math.round(matchRate * 100)}%
                </span>
                <span className="text-xs text-muted-foreground">of line items</span>
              </div>
            </div>
            <ul className="mt-4 space-y-1.5 text-sm">
              <li className="flex items-center gap-2">
                <span className="size-2.5 rounded-full" style={{ backgroundColor: MATCHED_COLOR }} />
                Matched · {matchedItems}
              </li>
              <li className="flex items-center gap-2">
                <span className="size-2.5 rounded-full" style={{ backgroundColor: UNMATCHED_COLOR }} />
                Unmatched · {unmatchedItems}
              </li>
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}
