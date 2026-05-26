"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function GenerateSummaryButton({ patientId }: { patientId: number }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  return (
    <Button
      onClick={() =>
        start(async () => {
          await api.generateSummary(patientId);
          router.refresh();
        })
      }
      disabled={pending}
    >
      {pending ? "Generating…" : "Generate today's summary"}
    </Button>
  );
}
