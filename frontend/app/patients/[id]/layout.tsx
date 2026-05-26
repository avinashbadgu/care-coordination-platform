import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ClipboardList,
  FileText,
  Mic,
  PillIcon,
  Sparkles,
  Bell,
  ArrowRightLeft,
} from "lucide-react";
import { api } from "@/lib/api";
import { Separator } from "@/components/ui/separator";
import { PatientSidebarLink } from "./sidebar-link";

export default async function PatientLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const patientId = Number(id);
  if (!Number.isFinite(patientId)) notFound();

  let patient;
  try {
    patient = await api.getPatient(patientId);
  } catch {
    notFound();
  }

  const base = `/patients/${patient.id}`;
  const items = [
    { href: `${base}`, label: "Timeline", icon: Activity },
    { href: `${base}/medications`, label: "Medications", icon: PillIcon },
    { href: `${base}/reminders`, label: "Reminders", icon: Bell },
    { href: `${base}/care-plan`, label: "Care plan", icon: ClipboardList },
    { href: `${base}/documents`, label: "Documents", icon: FileText },
    { href: `${base}/voice-notes`, label: "Voice notes", icon: Mic },
    { href: `${base}/alerts`, label: "Alerts", icon: AlertTriangle },
    { href: `${base}/summaries`, label: "Daily summary", icon: Sparkles },
    { href: `${base}/handoff`, label: "Shift handoff", icon: ArrowRightLeft },
  ];

  return (
    <div className="grid gap-8 lg:grid-cols-[220px_1fr]">
      <aside>
        <div className="mb-4">
          <Link href="/patients" className="text-xs text-muted-foreground hover:text-foreground">
            ← All patients
          </Link>
          <h2 className="mt-1 text-lg font-semibold leading-tight">{patient.full_name}</h2>
          <p className="text-xs text-muted-foreground">{patient.timezone}</p>
        </div>
        <Separator className="mb-3" />
        <nav className="flex flex-col gap-1 text-sm">
          {items.map(({ href, label, icon: Icon }) => (
            <PatientSidebarLink key={href} href={href}>
              <Icon className="h-4 w-4" />
              {label}
            </PatientSidebarLink>
          ))}
        </nav>
      </aside>
      <section className="min-w-0">{children}</section>
    </div>
  );
}
