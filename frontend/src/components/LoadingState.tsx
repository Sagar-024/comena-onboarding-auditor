import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const STAT_SLOTS = ["score", "rate", "documents"] as const;

export default function LoadingState() {
  return (
    <section aria-label="Loading analysis" className="mt-6 space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        {STAT_SLOTS.map((slot) => (
          <Card key={slot}>
            <CardContent className="space-y-2 p-5">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardContent className="space-y-3 p-5">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-3/5" />
        </CardContent>
      </Card>
    </section>
  );
}
