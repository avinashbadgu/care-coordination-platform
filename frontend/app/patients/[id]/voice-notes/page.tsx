import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTime } from "@/lib/utils";
import { UploadVoiceNoteForm } from "./upload-form";

export const dynamic = "force-dynamic";

export default async function VoiceNotesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const notes = await api.listVoiceNotes(patientId);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Voice notes</h1>
        <p className="text-sm text-muted-foreground">
          Audio → transcript → entity extraction → typed timeline events.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-3">
          {notes.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-sm text-muted-foreground">
                No voice notes yet.
              </CardContent>
            </Card>
          ) : (
            notes.map((n) => (
              <Card key={n.id}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-base">{n.original_filename}</CardTitle>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={n.status} />
                    {n.confidence !== null && (
                      <span className="text-xs text-muted-foreground">
                        conf {n.confidence.toFixed(2)}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-xs text-muted-foreground">
                    Uploaded {formatDateTime(n.created_at)}
                  </div>
                  {n.transcript && (
                    <p className="rounded-md bg-muted p-3 text-sm">{n.transcript}</p>
                  )}
                  {n.extracted_entities && (
                    <details>
                      <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                        extracted entities
                      </summary>
                      <pre className="mt-1 overflow-auto rounded bg-muted p-2 text-xs">
                        {JSON.stringify(n.extracted_entities, null, 2)}
                      </pre>
                    </details>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Upload voice note</CardTitle>
          </CardHeader>
          <CardContent>
            <UploadVoiceNoteForm patientId={patientId} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
