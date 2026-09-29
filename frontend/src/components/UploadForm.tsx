import { zodResolver } from "@hookform/resolvers/zod";
import { FileSpreadsheet, FileText, Loader2, Paperclip } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from "@/lib/types";

const hasExtension = (file: File, extension: string): boolean =>
  file.name.toLowerCase().endsWith(extension);

// RHF stores file input values as a FileList in the DOM but surfaces them as
// File[] through its state; accept both so validation works for real selections.
const fileListSchema = z
  .union([z.instanceof(FileList), z.array(z.instanceof(File))])
  .transform((files) => Array.from(files));

const uploadFormSchema = z.object({
  pdfs: fileListSchema.pipe(
    z
      .array(z.instanceof(File))
      .min(1, "Attach at least one purchase order PDF.")
      .refine(
        (files) => files.every((file) => hasExtension(file, ".pdf")),
        "Purchase orders must be PDF files.",
      )
      .refine(
        (files) => files.every((file) => file.size <= MAX_FILE_SIZE_BYTES),
        `Each PDF must be ${MAX_FILE_SIZE_MB} MB or smaller.`,
      ),
  ),
  catalog: fileListSchema.pipe(
    z
      .array(z.instanceof(File))
      .length(1, "Attach exactly one catalog CSV.")
      .refine(
        (files) => files.every((file) => hasExtension(file, ".csv")),
        "The catalog must be a CSV file.",
      )
      .refine(
        (files) => files.every((file) => file.size <= MAX_FILE_SIZE_BYTES),
        `The catalog must be ${MAX_FILE_SIZE_MB} MB or smaller.`,
      ),
  ),
});

interface UploadFormProps {
  pending: boolean;
  onSubmit: (pdfs: File[], catalog: File) => void;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function selectedFileList(files: FileList | File[] | undefined) {
  const list = files === undefined ? [] : Array.from(files);
  if (list.length === 0) return null;
  return (
    <ul className="space-y-1">
      {list.map((file) => (
        <li key={file.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Paperclip className="size-3 shrink-0" aria-hidden="true" />
          <span className="truncate">{file.name}</span>
          <span className="ml-auto shrink-0 tabular-nums">{formatBytes(file.size)}</span>
        </li>
      ))}
    </ul>
  );
}

export default function UploadForm({ pending, onSubmit }: UploadFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<z.input<typeof uploadFormSchema>, unknown, z.output<typeof uploadFormSchema>>({
    resolver: zodResolver(uploadFormSchema),
    mode: "onChange",
  });
  const pdfs = watch("pdfs");
  const catalog = watch("catalog");

  const submit = handleSubmit((values) => {
    const [catalogFile] = values.catalog;
    if (!catalogFile) return;
    onSubmit(values.pdfs, catalogFile);
  });

  return (
    <form onSubmit={(event) => void submit(event)} noValidate>
      <fieldset disabled={pending} className="space-y-8 border-0 p-0">
        <div className="space-y-2">
          <Label
            htmlFor="purchase-orders"
            className="flex cursor-pointer flex-col items-center gap-1.5 rounded-lg border border-dashed bg-card px-6 py-8 text-center transition-colors hover:border-foreground/25 hover:bg-accent"
          >
            <FileText className="size-6 text-muted-foreground" aria-hidden="true" />
            <span className="text-sm font-medium">Purchase order PDFs</span>
            <span className="text-xs text-muted-foreground">
              One or more files, up to {MAX_FILE_SIZE_MB} MB each
            </span>
          </Label>
          <Input
            id="purchase-orders"
            type="file"
            multiple
            accept=".pdf,application/pdf"
            className="sr-only w-px"
            {...register("pdfs")}
          />
          {selectedFileList(pdfs)}
          {errors.pdfs ? <p className="text-sm text-destructive">{errors.pdfs.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label
            htmlFor="catalog"
            className="flex cursor-pointer flex-col items-center gap-1.5 rounded-lg border border-dashed bg-card px-6 py-8 text-center transition-colors hover:border-foreground/25 hover:bg-accent"
          >
            <FileSpreadsheet className="size-6 text-muted-foreground" aria-hidden="true" />
            <span className="text-sm font-medium">Product catalog CSV</span>
            <span className="text-xs text-muted-foreground">
              One file with SKU, description and unit columns
            </span>
          </Label>
          <Input
            id="catalog"
            type="file"
            accept=".csv,text/csv"
            className="sr-only w-px"
            {...register("catalog")}
          />
          {selectedFileList(catalog)}
          {errors.catalog ? (
            <p className="text-sm text-destructive">{errors.catalog.message}</p>
          ) : null}
        </div>

        <Button type="submit" disabled={!isValid || pending} className="w-full sm:w-auto">
          {pending ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Analyzing…
            </>
          ) : (
            "Analyze readiness"
          )}
        </Button>
      </fieldset>
    </form>
  );
}
