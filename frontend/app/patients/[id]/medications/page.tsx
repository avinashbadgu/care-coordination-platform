import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScheduleMedicationForm } from "./schedule-form";

export const dynamic = "force-dynamic";

export default async function MedicationsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const meds = await api.listMedications(patientId);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Medications</h1>
        <p className="text-sm text-muted-foreground">
          Schedules expand into reminder rows. Acknowledgements drive adherence.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader>
            <CardTitle>Active schedules</CardTitle>
          </CardHeader>
          <CardContent>
            {meds.length === 0 ? (
              <p className="text-sm text-muted-foreground">No medications scheduled yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Medication</TableHead>
                    <TableHead>Dosage</TableHead>
                    <TableHead>Times</TableHead>
                    <TableHead className="text-right">Active</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {meds.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="font-medium">{m.medication_name}</TableCell>
                      <TableCell>{m.dosage || "—"}</TableCell>
                      <TableCell className="font-mono text-xs">
                        {m.times_of_day.join(", ")}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={m.active ? "default" : "muted"}>
                          {m.active ? "yes" : "no"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Schedule a medication</CardTitle>
          </CardHeader>
          <CardContent>
            <ScheduleMedicationForm patientId={patientId} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
