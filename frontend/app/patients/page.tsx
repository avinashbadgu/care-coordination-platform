import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";
import { NewPatientButton } from "./new-patient-button";

export const dynamic = "force-dynamic";

export default async function PatientsPage() {
  let patients;
  try {
    const page = await api.listPatients();
    patients = page.items;
  } catch (e) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Patients</h1>
        <Card>
          <CardContent className="py-8 text-sm text-muted-foreground">
            Could not reach the API at <code>{process.env.NEXT_PUBLIC_API_BASE}</code>.
            Start the backend with <code>uvicorn app.main:app --reload</code>.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Patients</h1>
          <p className="text-sm text-muted-foreground">
            Select a patient to open their care timeline and workflows.
          </p>
        </div>
        <NewPatientButton />
      </div>

      {patients.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No patients yet. Create the first one to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {patients.map((p) => (
            <Link key={p.id} href={`/patients/${p.id}`} className="block">
              <Card className="transition-colors hover:bg-accent">
                <CardHeader>
                  <CardTitle>{p.full_name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <div>Timezone: {p.timezone}</div>
                  <div>Added {formatDateTime(p.created_at)}</div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
