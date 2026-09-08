import type { ColorGrade, MontageStyle } from "./types.ts";
import { STYLE_BY_ID, type StylePreset } from "./style-presets.ts";

/** Canva-inspired YouTube packs. Connect API needs a user OAuth token — these packs run locally. */
export type CanvaStyle = {
  id: string;
  name: string;
  nameRu: string;
  blurb: string;
  blurbRu: string;
  themeId: string;
  montage: MontageStyle;
  fontId: string;
  grade: ColorGrade;
  backgroundId: string;
  color: string;
  swatch: [string, string, string];
  avgShot: number;
  photoShare: number;
  plaqueRate: number;
  titles: string;
  canvaCreate: string;
};

export const CANVA_CREATE = "https://www.canva.com/create/";
export const CANVA_YT = "https://www.canva.com/youtube-thumbnails/";

export const CANVA_STYLES: CanvaStyle[] = [
  {
    id: "canva-bold-yt",
    name: "Bold YouTube",
    nameRu: "Жирный YouTube",
    blurb: "Punchy type, hard cuts, thumbnail energy.",
    blurbRu: "Ударный набор, жёсткие склейки, энергия обложки.",
    themeId: "modern",
    montage: "dynamic",
    fontId: "bebas",
    grade: "kodak",
    backgroundId: "ink",
    color: "#e11d48",
    swatch: ["#0b0b0f", "#e11d48", "#fbbf24"],
    avgShot: 2.4,
    photoShare: 0.35,
    plaqueRate: 0.72,
    titles: "bold caps",
    canvaCreate: CANVA_YT,
  },
  {
    id: "canva-pastel",
    name: "Soft Pastel",
    nameRu: "Пастель",
    blurb: "Quiet lifestyle grades, long holds, round type.",
    blurbRu: "Тихий лайфстайл, длинные планы, мягкий шрифт.",
    themeId: "minimal",
    montage: "minimal",
    fontId: "nunito",
    grade: "polaroid",
    backgroundId: "mist",
    color: "#ec4899",
    swatch: ["#f8e7ee", "#ec4899", "#7dd3fc"],
    avgShot: 4.2,
    photoShare: 0.7,
    plaqueRate: 0.28,
    titles: "sentence case",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-editorial",
    name: "Editorial Serif",
    nameRu: "Редакторский",
    blurb: "Magazine plaques, slow dissolves, paper stock.",
    blurbRu: "Журнальные плашки, медленные dissolve, бумага.",
    themeId: "history",
    montage: "history",
    fontId: "playfair",
    grade: "vintage",
    backgroundId: "linen",
    color: "#1c1917",
    swatch: ["#e8dcc4", "#1c1917", "#b45309"],
    avgShot: 3.8,
    photoShare: 0.55,
    plaqueRate: 0.48,
    titles: "serif headline",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-neon",
    name: "Neon Night",
    nameRu: "Неон",
    blurb: "Dark board, cyan accent, snap cuts.",
    blurbRu: "Тёмная доска, циан, резкие склейки.",
    themeId: "modern",
    montage: "dynamic",
    fontId: "russo",
    grade: "cool",
    backgroundId: "void",
    color: "#22d3ee",
    swatch: ["#020617", "#22d3ee", "#a855f7"],
    avgShot: 2.2,
    photoShare: 0.3,
    plaqueRate: 0.64,
    titles: "neon lower-third",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-amber-doc",
    name: "Amber Desk",
    nameRu: "Янтарный стол",
    blurb: "Documentary captions, archival grain, match cuts.",
    blurbRu: "Документальные подписи, зерно, match cut.",
    themeId: "standard",
    montage: "documentary",
    fontId: "oswald",
    grade: "noir",
    backgroundId: "grid",
    color: "#d97706",
    swatch: ["#111111", "#d97706", "#e7e5e4"],
    avgShot: 3.2,
    photoShare: 0.42,
    plaqueRate: 0.52,
    titles: "condensed caption",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-cream",
    name: "Cream Lecture",
    nameRu: "Кремовая лекция",
    blurb: "Academic paper, measured type, analog warmth.",
    blurbRu: "Учебная бумага, спокойный набор, аналог.",
    themeId: "history",
    montage: "history",
    fontId: "fraunces",
    grade: "vintage",
    backgroundId: "paper",
    color: "#b45309",
    swatch: ["#efe6d6", "#b45309", "#44403c"],
    avgShot: 4.0,
    photoShare: 0.62,
    plaqueRate: 0.4,
    titles: "lecture title",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-corporate",
    name: "Clean Board",
    nameRu: "Чистая доска",
    blurb: "Corporate slides, almost no chrome, Inter.",
    blurbRu: "Корпоратив, почти без хрома, Inter.",
    themeId: "minimal",
    montage: "minimal",
    fontId: "inter",
    grade: "none",
    backgroundId: "slate",
    color: "#3b6cff",
    swatch: ["#1a1d22", "#3b6cff", "#e5e7eb"],
    avgShot: 3.6,
    photoShare: 0.5,
    plaqueRate: 0.32,
    titles: "plain statement",
    canvaCreate: CANVA_CREATE,
  },
  {
    id: "canva-crime",
    name: "Red File",
    nameRu: "Красное дело",
    blurb: "True-crime board, glitch hops, condensed type.",
    blurbRu: "True crime, глитч, узкий гротеск.",
    themeId: "crime",
    montage: "history",
    fontId: "roboto-cond",
    grade: "noir",
    backgroundId: "ember",
    color: "#e23a3a",
    swatch: ["#120406", "#e23a3a", "#c9a227"],
    avgShot: 2.8,
    photoShare: 0.38,
    plaqueRate: 0.58,
    titles: "case file",
    canvaCreate: CANVA_CREATE,
  },
];

export const CANVA_BY_ID: Record<string, CanvaStyle> = Object.fromEntries(CANVA_STYLES.map((s) => [s.id, s]));

export function canvaStyleById(id?: string | null): CanvaStyle | undefined {
  if (!id) return undefined;
  return CANVA_BY_ID[id];
}

export function montageForCanva(id?: string | null): StylePreset {
  const pack = canvaStyleById(id);
  if (!pack) return STYLE_BY_ID.documentary;
  return STYLE_BY_ID[pack.montage];
}

export function brandPatchFromCanva(style: CanvaStyle) {
  return {
    canvaStyleId: style.id,
    themeId: style.themeId,
    color: style.color,
    backgroundId: style.backgroundId,
    editingStyle: {
      avgShot: style.avgShot,
      photoShare: style.photoShare,
      plaqueRate: style.plaqueRate,
      titles: style.titles,
      grade: style.grade,
    },
  };
}
