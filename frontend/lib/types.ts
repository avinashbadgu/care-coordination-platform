export type Urgency = "low" | "medium" | "high";

export type CaregiverRole = "patient" | "family" | "caretaker" | "nurse" | "admin";

export interface Patient {
  id: number;
  full_name: string;
  date_of_birth: string | null;
  timezone: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Caregiver {
  id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatientCaregiverLink {
  id: number;
  patient_id: number;
  caregiver_id: number;
  role: CaregiverRole;
  created_at: string;
}

export interface TimelineEvent {
  id: number;
  patient_id: number;
  event_type: string;
  urgency: Urgency;
  occurred_at: string;
  summary: string | null;
  payload: Record<string, unknown> | null;
  source: string;
  actor_caregiver_id: number | null;
  confidence: number | null;
  related_medication_id: number | null;
  related_reminder_id: number | null;
  related_document_id: number | null;
  related_voice_note_id: number | null;
  created_at: string;
}

export interface MedicationSchedule {
  id: number;
  patient_id: number;
  medication_name: string;
  dosage: string | null;
  instructions: string | null;
  times_of_day: string[];
  starts_on: string | null;
  ends_on: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export type ReminderStatus = "pending" | "sent" | "acknowledged" | "missed" | "failed";

export interface Reminder {
  id: number;
  patient_id: number;
  medication_schedule_id: number | null;
  scheduled_for: string;
  sent_at: string | null;
  acknowledged_at: string | null;
  status: ReminderStatus;
  channel: string | null;
  retries: number;
  created_at: string;
  updated_at: string;
}

export type DocumentKind = "prescription" | "lab_report" | "discharge_summary" | "other";
export type DocumentStatus =
  | "uploaded"
  | "ocr_running"
  | "ocr_completed"
  | "ocr_failed"
  | "review_required";

export interface UploadedDocument {
  id: number;
  patient_id: number;
  uploaded_by_caregiver_id: number | null;
  kind: DocumentKind;
  original_filename: string;
  mime_type: string | null;
  storage_path: string;
  status: DocumentStatus;
  raw_text: string | null;
  extracted_entities: Record<string, unknown> | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export type VoiceNoteStatus =
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "extracted"
  | "failed";

export interface VoiceNote {
  id: number;
  patient_id: number;
  recorded_by_caregiver_id: number | null;
  original_filename: string;
  mime_type: string | null;
  storage_path: string;
  duration_seconds: number | null;
  status: VoiceNoteStatus;
  transcript: string | null;
  extracted_entities: Record<string, unknown> | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export type AlertStatus = "open" | "acknowledged" | "resolved";

export interface Alert {
  id: number;
  patient_id: number;
  urgency: Urgency;
  title: string;
  detail: string | null;
  status: AlertStatus;
  resolved_at: string | null;
  resolved_by_caregiver_id: number | null;
  source_event_id: number | null;
  created_at: string;
  updated_at: string;
}

export type EscalationStatus = "open" | "notified" | "resolved" | "cancelled";

export interface Escalation {
  id: number;
  patient_id: number;
  alert_id: number | null;
  rule: string | null;
  reason: string | null;
  status: EscalationStatus;
  notified_caregiver_id: number | null;
  notified_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DailySummary {
  id: number;
  patient_id: number;
  summary_date: string;
  headline: string | null;
  body: string;
  metrics: Record<string, unknown> | null;
  prompt_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface CarePlanTask {
  id: number;
  care_plan_id: number;
  title: string;
  cadence: string | null;
  instructions: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CarePlan {
  id: number;
  patient_id: number;
  title: string;
  description: string | null;
  starts_on: string | null;
  ends_on: string | null;
  created_by_caregiver_id: number | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  tasks: CarePlanTask[];
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface HandoffSummary {
  patient_id: number;
  window_start: string;
  window_end: string;
  headline: string;
  body: string;
  events: Record<string, number>;
  open_alerts: number;
  open_escalations: number;
  metrics: Record<string, unknown>;
}
