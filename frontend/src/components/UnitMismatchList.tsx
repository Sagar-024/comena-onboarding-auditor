import { ArrowRightLeft } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import type { UnitMismatch } from "@/lib/types";

interface UnitMismatchListProps {
  mismatches: UnitMismatch[];
}

export default function UnitMismatchList({ mismatches }: UnitMismatchListProps) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-base font-semibold">
        Unit mismatches
        <Badge variant="secondary">{mismatches.length}</Badge>
      </h2>
      <div className="space-y-3">
        {mismatches.map((mismatch) => (
          <Alert
            key={`${mismatch.sku}-${mismatch.description}`}
            className="border-amber-500/30 bg-amber-50 [&>svg]:text-amber-600"
          >
            <ArrowRightLeft />
            <AlertTitle>{mismatch.description}</AlertTitle>
            <AlertDescription>
              {mismatch.sku} — the PO orders in “{mismatch.po_unit}” but the catalog
              lists “{mismatch.catalog_unit}”. The ERP will need a unit conversion rule.
            </AlertDescription>
          </Alert>
        ))}
      </div>
    </section>
  );
}
