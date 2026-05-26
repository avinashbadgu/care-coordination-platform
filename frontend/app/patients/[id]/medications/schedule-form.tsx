"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export function ScheduleMedicationForm({ patientId }: { patientId: number }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [dosage, setDosage] = useState("");
  const [times, setTimes] = useState("08:00, 20:00");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const parsed = times
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      await api.scheduleMedication(patientId, {
        medication_name: name.trim(),
        dosage: dosage.trim() || undefined,
        times_of_day: parsed,
      });
      setName("");
      setDosage("");
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-3" onSubmit={submit}>
      <div className="space-y-1.5">
        <Label htmlFor="name">Medication name</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="dosage">Dosage</Label>
        <Input id="dosage" value={dosage} onChange={(e) => setDosage(e.target.value)} placeholder="500mg" />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="times">Times of day (HH:MM, comma-separated)</Label>
        <Input id="times" value={times} onChange={(e) => setTimes(e.target.value)} />
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
      <Button type="submit" disabled={submitting || !name.trim()}>
        {submitting ? "Scheduling…" : "Schedule"}
      </Button>
    </form>
  );
}
