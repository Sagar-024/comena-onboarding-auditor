import { ShieldAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface ErpFlagsProps {
  flags: string[];
}

export default function ErpFlags({ flags }: ErpFlagsProps) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-base font-semibold">
        ERP mapping flags
        <Badge variant="secondary">{flags.length}</Badge>
      </h2>
      <div className="space-y-3">
        {flags.map((flag) => (
          <Alert key={flag}>
            <ShieldAlert />
            <AlertDescription>{flag}</AlertDescription>
          </Alert>
        ))}
      </div>
    </section>
  );
}
