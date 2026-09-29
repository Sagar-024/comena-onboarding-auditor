import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import LoadingState from "@/components/LoadingState";
import UploadForm from "@/components/UploadForm";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { analyzeReadiness, REPORT_QUERY_KEY, storeReport } from "@/lib/api";

export default function Home() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ pdfs, catalog }: { pdfs: File[]; catalog: File }) =>
      analyzeReadiness(pdfs, catalog),
    onSuccess: (report) => {
      queryClient.setQueryData(REPORT_QUERY_KEY, report);
      storeReport(report);
      navigate("/report");
    },
  });

  return (
    <main className="mx-auto w-full max-w-2xl px-4 pb-16 pt-10 sm:pt-16">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          Comena Onboarding Readiness Auditor
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
          Upload sample purchase orders and a product catalog to assess onboarding
          readiness before deployment.
        </p>
      </header>

      <div className="mt-8 rounded-xl border bg-card p-5 shadow-sm sm:p-6">
        <UploadForm
          pending={mutation.isPending}
          onSubmit={(pdfs, catalog) => mutation.mutate({ pdfs, catalog })}
        />
      </div>

      {mutation.isPending ? <LoadingState /> : null}

      {mutation.isError ? (
        <Alert variant="destructive" className="mt-6">
          <AlertTriangle />
          <AlertTitle>Analysis failed</AlertTitle>
          <AlertDescription>{mutation.error.message}</AlertDescription>
        </Alert>
      ) : null}
    </main>
  );
}
