import type {
  Alert,
  CarePlan,
  Caregiver,
  DailySummary,
  Escalation,
  HandoffSummary,
  MedicationSchedule,
  Page,
  Patient,
  PatientCaregiverLink,
  Reminder,
  TimelineEvent,
  UploadedDocument,
  VoiceNote,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const body = json !== undefined ? JSON.stringify(json) : (init.body as BodyInit | null | undefined);
  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(headers as Record<string, string> | undefined),
  };
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    body,
    headers: finalHeaders,
    cache: "no-store",
  });
  if (!res.ok) {
    let detail: unknown = await res.text().catch(() => "");
    try {
      detail = typeof detail === "string" && detail ? JSON.parse(detail) : detail;
    } catch {
      // keep as text
    }
    throw new ApiError(res.status, detail, `HTTP ${res.status} on ${path}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // patients
  listPatients: () => request<Page<Patient>>("/v1/patients"),
  getPatient: (id: number) => request<Patient>(`/v1/patients/${id}`),
  createPatient: (data: { full_name: string; timezone?: string; notes?: string }) =>
    request<Patient>("/v1/patients", { method: "POST", json: data }),

  // caregivers
  listCaregivers: () => request<Page<Caregiver>>("/v1/caregivers"),
  createCaregiver: (data: { full_name: string; phone?: string; email?: string }) =>
    request<Caregiver>("/v1/caregivers", { method: "POST", json: data }),
  linkCaregiver: (patientId: number, data: { caregiver_id: number; role: string }) =>
    request<PatientCaregiverLink>(`/v1/patients/${patientId}/caregivers`, {
      method: "POST",
      json: data,
    }),
  listPatientCaregivers: (patientId: number) =>
    request<PatientCaregiverLink[]>(`/v1/patients/${patientId}/caregivers`),

  // timeline
  listTimeline: (patientId: number, params?: { limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    return request<Page<TimelineEvent>>(
      `/v1/patients/${patientId}/timeline${q.toString() ? `?${q}` : ""}`,
    );
  },
  recordEvent: (
    patientId: number,
    data: {
      event_type: string;
      urgency?: "low" | "medium" | "high";
      summary?: string;
      payload?: Record<string, unknown>;
    },
  ) =>
    request<TimelineEvent>(`/v1/patients/${patientId}/timeline`, {
      method: "POST",
      json: data,
    }),

  // medications
  listMedications: (patientId: number) =>
    request<MedicationSchedule[]>(`/v1/patients/${patientId}/medications`),
  scheduleMedication: (
    patientId: number,
    data: {
      medication_name: string;
      dosage?: string;
      instructions?: string;
      times_of_day: string[];
    },
  ) =>
    request<MedicationSchedule>(`/v1/patients/${patientId}/medications`, {
      method: "POST",
      json: data,
    }),

  // reminders
  listReminders: (patientId: number) =>
    request<Reminder[]>(`/v1/patients/${patientId}/reminders`),
  expandReminders: (patientId: number) =>
    request<Reminder[]>(`/v1/patients/${patientId}/reminders/expand`, { method: "POST" }),
  dispatchDue: () =>
    request<{ sent: number }>(`/v1/reminders/dispatch`, { method: "POST" }),
  detectMisses: () =>
    request<{ missed: number }>(`/v1/reminders/detect-misses`, { method: "POST" }),
  ackReminder: (id: number) =>
    request<Reminder>(`/v1/reminders/${id}/ack`, { method: "POST", json: {} }),

  // care plans
  listCarePlans: (patientId: number) =>
    request<CarePlan[]>(`/v1/patients/${patientId}/care-plans`),
  createCarePlan: (
    patientId: number,
    data: {
      title: string;
      description?: string;
      tasks?: { title: string; cadence?: string }[];
    },
  ) =>
    request<CarePlan>(`/v1/patients/${patientId}/care-plans`, {
      method: "POST",
      json: data,
    }),
  completeTask: (carePlanId: number, taskId: number) =>
    request(`/v1/care-plans/${carePlanId}/tasks/${taskId}/complete`, {
      method: "POST",
      json: {},
    }),

  // documents
  listDocuments: (patientId: number) =>
    request<UploadedDocument[]>(`/v1/patients/${patientId}/documents`),
  uploadDocument: async (
    patientId: number,
    file: File,
    kind: string,
  ): Promise<UploadedDocument> => {
    const form = new FormData();
    form.append("file", file);
    form.append("kind", kind);
    const res = await fetch(`${API_BASE}/v1/patients/${patientId}/documents`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new ApiError(res.status, await res.text(), "upload failed");
    return res.json();
  },

  // voice notes
  listVoiceNotes: (patientId: number) =>
    request<VoiceNote[]>(`/v1/patients/${patientId}/voice-notes`),
  uploadVoiceNote: async (patientId: number, file: File): Promise<VoiceNote> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/v1/patients/${patientId}/voice-notes`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new ApiError(res.status, await res.text(), "upload failed");
    return res.json();
  },

  // alerts & escalations
  listAlerts: (patientId: number, onlyOpen = false) =>
    request<Alert[]>(
      `/v1/patients/${patientId}/alerts${onlyOpen ? "?only_open=true" : ""}`,
    ),
  resolveAlert: (id: number) =>
    request<Alert>(`/v1/alerts/${id}/resolve`, { method: "POST", json: {} }),
  listEscalations: (patientId: number) =>
    request<Escalation[]>(`/v1/patients/${patientId}/escalations`),
  resolveEscalation: (id: number) =>
    request<Escalation>(`/v1/escalations/${id}/resolve`, { method: "POST" }),

  // summaries
  listSummaries: (patientId: number) =>
    request<DailySummary[]>(`/v1/patients/${patientId}/summaries`),
  generateSummary: (patientId: number) =>
    request<DailySummary>(`/v1/patients/${patientId}/summaries`, { method: "POST" }),

  // handoff
  getHandoff: (patientId: number, hours = 12) =>
    request<HandoffSummary>(`/v1/patients/${patientId}/handoff?hours=${hours}`),
};

export { ApiError };
