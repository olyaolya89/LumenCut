import type { Voice } from "./types";

const SWATCHES = [
  "bg-[radial-gradient(circle_at_30%_30%,#5b8def,transparent_55%),#1e3a8a]",
  "bg-[radial-gradient(circle_at_30%_30%,#93c5fd,#1d4ed8)]",
  "bg-[radial-gradient(circle_at_30%_30%,#fda4af,transparent_55%),#9f1239]",
  "bg-[radial-gradient(circle_at_30%_30%,#5eead4,#0f766e)]",
  "bg-[radial-gradient(circle_at_30%_30%,#86efac,transparent_55%),#166534]",
  "bg-[radial-gradient(circle_at_30%_30%,#fbbf24,transparent_55%),#78350f]",
  "bg-[radial-gradient(circle_at_30%_30%,#60a5fa,transparent_55%),#1e40af]",
  "bg-[radial-gradient(circle_at_30%_30%,#d6d3d1,transparent_55%),#44403c]",
];

export type LumeanLibraryVoice = {
  voice_id?: string;
  id?: string;
  name?: string;
  display_name?: string;
  preview_url?: string;
  previewUrl?: string;
  samples?: { url?: string; preview_url?: string }[];
  gender?: string;
  age?: string;
  descriptive?: string;
  use_case?: string;
  accent?: string;
  language?: string;
  description?: string;
  category?: string;
  labels?: Record<string, string>;
};

function ageLabel(age: string): string {
  const a = age.toLowerCase();
  if (a.includes("young")) return "Young";
  if (a.includes("old") || a.includes("senior")) return "Senior";
  return "Middle-Aged";
}

function genderLabel(g: string): Voice["gender"] {
  return g.toLowerCase() === "female" ? "Female" : "Male";
}

export function lumeanVoiceId(id: string | undefined): string {
  const ident = (id || "").trim();
  if (ident.startsWith("lumean:")) return ident.slice(7);
  if (ident.startsWith("lumean-")) return ident.slice(7);
  return ident;
}

export function isLumeanVoiceId(id: string | undefined): boolean {
  const ident = (id || "").trim();
  return ident.startsWith("lumean:") || ident.startsWith("lumean-");
}

function str(v: unknown): string {
  return typeof v === "string" ? v.trim() : "";
}

export function fromLumeanVoice(raw: LumeanLibraryVoice, i: number): Voice | null {
  const labels = raw.labels && typeof raw.labels === "object" ? raw.labels : {};
  const id = str(raw.voice_id || raw.id);
  const name = str(raw.name || raw.display_name);
  if (!id || !name) return null;
  const gender = str(raw.gender || labels.gender || "male");
  const age = str(raw.age || labels.age || "middle_aged");
  const style = str(raw.use_case || labels.use_case || raw.descriptive || labels.descriptive || raw.category || "Narrative").replace(
    /_/g,
    " ",
  );
  const accent = str(raw.accent || labels.accent);
  const language = str(raw.language || labels.language);
  const sample = Array.isArray(raw.samples) ? raw.samples[0] : undefined;
  const preview = str(raw.preview_url || raw.previewUrl || sample?.preview_url || sample?.url);
  const note = [accent, language, style].filter(Boolean).join(" · ") || "Lumean";
  return {
    id: `lumean:${id}`,
    ttsId: id,
    name: `${name} — Lumean`,
    note,
    noteRu: note,
    gender: genderLabel(gender),
    age: ageLabel(age),
    style,
    swatch: SWATCHES[i % SWATCHES.length]!,
    source: "lumean",
    previewUrl: preview || undefined,
  };
}
