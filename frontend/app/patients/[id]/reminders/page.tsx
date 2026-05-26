import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTime } from "@/lib/utils";
import { ReminderActions, ReminderRowActions } from "./actions";

export const dynamic = "force-dynamic";

export default async function RemindersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const reminders = await api.listReminders(patientId);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reminders</h1>
          <p className="text-sm text-muted-foreground">
            Expand today's schedule, dispatch due reminders, ack on patient response, or
            run miss-detection.
          </p>
        </div>
        <ReminderActions patientId={patientId} />
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Recent reminders</CardTitle>
        </CardHeader>
        <CardContent>
          {reminders.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No reminders yet. Schedule a medication and then click <b>Expand today</b>.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scheduled for</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Retries</TableHead>
                  <TableHead>Acked</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reminders.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono text-xs">
                      {formatDateTime(r.scheduled_for)}
                    </TableCell>
                    <TableCell><StatusBadge status={r.status} /></TableCell>
                    <TableCell className="text-muted-foreground">{r.channel || "—"}</TableCell>
                    <TableCell>{r.retries}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {r.acknowledged_at ? formatDateTime(r.acknowledged_at) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <ReminderRowActions reminderId={r.id} status={r.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
