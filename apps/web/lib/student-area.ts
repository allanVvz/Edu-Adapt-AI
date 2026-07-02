export interface StudentStorySummary {
  id: string;
  title: string | null;
  status?: string | null;
}

export interface StudentActivityCard {
  id: string;
  activity_id: string;
  title: string | null;
  discipline: string | null;
  story: StudentStorySummary | null;
  status: string;
  created_at: string;
  completed_at?: string | null;
  score?: number | null;
  max_score?: number | null;
  percentage?: number | null;
  has_result?: boolean;
}

export interface StudentResultCard {
  id: string;
  adaptation_id: string;
  activity_id: string;
  title: string | null;
  discipline: string | null;
  story: StudentStorySummary | null;
  score: number | null;
  max_score: number | null;
  percentage: number | null;
  status: string;
  finished_at: string | null;
  created_at: string;
  completion_time_seconds?: number | null;
}

export interface DisciplineGroup<T> {
  id: string;
  label: string;
  activities: T[];
}

export interface StoryGroup<T> {
  id: string;
  label: string;
  activities: T[];
}

export interface DisciplineTheme {
  icon: string;
  accent: string;
  softBg: string;
  border: string;
  text: string;
  badge: string;
  button: string;
  ring: string;
}

const DEFAULT_DISCIPLINE_THEME: DisciplineTheme = {
  icon: "✨",
  accent: "bg-slate-900",
  softBg: "bg-slate-50",
  border: "border-slate-200",
  text: "text-slate-800",
  badge: "bg-slate-100 text-slate-700",
  button: "bg-slate-900 text-white hover:bg-slate-800",
  ring: "ring-slate-200",
};

const DISCIPLINE_THEMES: Record<string, DisciplineTheme> = {
  portugues: {
    icon: "Aa",
    accent: "bg-amber-500",
    softBg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    badge: "bg-amber-100 text-amber-800",
    button: "bg-amber-600 text-white hover:bg-amber-700",
    ring: "ring-amber-200",
  },
  matematica: {
    icon: "123",
    accent: "bg-blue-600",
    softBg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-800",
    badge: "bg-blue-100 text-blue-800",
    button: "bg-blue-600 text-white hover:bg-blue-700",
    ring: "ring-blue-200",
  },
  ciencias: {
    icon: "🌱",
    accent: "bg-emerald-600",
    softBg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-800",
    badge: "bg-emerald-100 text-emerald-800",
    button: "bg-emerald-600 text-white hover:bg-emerald-700",
    ring: "ring-emerald-200",
  },
  historia: {
    icon: "🏛",
    accent: "bg-rose-600",
    softBg: "bg-rose-50",
    border: "border-rose-200",
    text: "text-rose-800",
    badge: "bg-rose-100 text-rose-800",
    button: "bg-rose-600 text-white hover:bg-rose-700",
    ring: "ring-rose-200",
  },
  geografia: {
    icon: "🌎",
    accent: "bg-sky-600",
    softBg: "bg-sky-50",
    border: "border-sky-200",
    text: "text-sky-800",
    badge: "bg-sky-100 text-sky-800",
    button: "bg-sky-600 text-white hover:bg-sky-700",
    ring: "ring-sky-200",
  },
  "sem-disciplina": DEFAULT_DISCIPLINE_THEME,
};

export function slugifySection(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function getDisciplineTheme(labelOrId: string | null | undefined): DisciplineTheme {
  const id = slugifySection(labelOrId?.trim() || "Sem disciplina");
  return DISCIPLINE_THEMES[id] ?? DEFAULT_DISCIPLINE_THEME;
}

export function getDisciplineHref(id: string) {
  return `/student/disciplines/${id}`;
}

function sortByCreatedAtAsc<T extends { created_at: string }>(items: T[]) {
  return [...items].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
}

export function groupActivitiesByDiscipline<T extends { discipline: string | null; created_at: string }>(
  activities: T[],
): DisciplineGroup<T>[] {
  const grouped = new Map<string, DisciplineGroup<T>>();

  for (const activity of activities) {
    const label = activity.discipline?.trim() || "Sem disciplina";
    const id = slugifySection(label);
    const current = grouped.get(id);

    if (current) {
      current.activities.push(activity);
    } else {
      grouped.set(id, {
        id,
        label,
        activities: [activity],
      });
    }
  }

  return Array.from(grouped.values())
    .map((group) => ({
      ...group,
      activities: sortByCreatedAtAsc(group.activities),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
}

export function groupActivitiesByStory<T extends { story: StudentStorySummary | null; created_at: string }>(
  activities: T[],
): StoryGroup<T>[] {
  const grouped = new Map<string, StoryGroup<T>>();

  for (const activity of activities) {
    const story = activity.story;
    if (!story?.id) continue;

    const label = story.title?.trim() || "Conto";
    const current = grouped.get(story.id);

    if (current) {
      current.activities.push(activity);
    } else {
      grouped.set(story.id, {
        id: story.id,
        label,
        activities: [activity],
      });
    }
  }

  return Array.from(grouped.values())
    .map((group) => ({
      ...group,
      activities: sortByCreatedAtAsc(group.activities),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
}
