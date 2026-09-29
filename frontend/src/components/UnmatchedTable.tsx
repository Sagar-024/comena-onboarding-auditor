import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CatalogGap } from "@/lib/types";

interface UnmatchedTableProps {
  gaps: CatalogGap[];
}

export default function UnmatchedTable({ gaps }: UnmatchedTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Unmatched descriptions</CardTitle>
        <CardDescription>
          These items had no catalog SKU above the match threshold. The nearest
          candidate shows how far off the catalog was.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description</TableHead>
              <TableHead>Nearest catalog SKU</TableHead>
              <TableHead className="text-right">Best score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {gaps.map((gap) => (
              <TableRow key={gap.description}>
                <TableCell className="max-w-72 truncate font-medium" title={gap.description}>
                  {gap.description}
                </TableCell>
                <TableCell className="tabular-nums">{gap.best_candidate_sku ?? "—"}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {gap.best_candidate_score === null ? "—" : gap.best_candidate_score.toFixed(1)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
