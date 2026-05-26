import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, formatDateTime } from "@/lib/utils";
import { GenerateSummaryButton } from "./actions";

export const dynamic = "force-dynamic";

export default async function SummariesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const summaries = await api.listSummaries(patientId);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Daily summaries</h1>
          <p className="text-sm text-muted-foreground">
            AI-generated operational digests. Reduces caregiver cognitive load.
          </p>
        </div>
        <GenerateSummaryButton patientId={patientId} />
      </header>

      <div className="space-y-4">
        {summaries.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-sm text-muted-foreground">
              No summaries yet. Generate today's to get started.
            </CardContent>
          </Card>
        ) : (
          summaries.map((s) => (
            <Card key={s.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>{formatDate(s.summary_date)}</CardTitle>
                  <span className="text-xs text-muted-foreground">
                    Updated {formatDateTime(s.updated_at)}
                  </span>
                </div>
                {s.headline && (
                  <p className="text-sm text-muted-foreground">{s.headline}</p>
                )}
              </CardHeader>
              <CardContent className="space-y-2">
                <pre className="whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
                  {s.body}
                </pre>
                {s.metrics && (
                  <details>
                    <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                      metrics
                    </summary>
                    <pre className="mt-1 overflow-auto rounded bg-muted p-2 text-xs">
                      {JSON.stringify(s.metrics, null, 2)}
                    </pre>
                  </details>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
