import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const API_BASE = process.env.SCLIB_API_BASE || "https://api.jzis.org/sclib/v1";
const OUT_DIR = new URL("./generated/", import.meta.url);

const families = [
  "cuprate",
  "iron_based",
  "nickelate",
  "hydride",
  "mgb2",
  "heavy_fermion",
  "fulleride",
  "kagome",
  "organic",
  "bismuthate",
  "borocarbide",
  "ruthenate",
  "chalcogenide",
  "elemental",
  "conventional",
];

const tcBands = [
  ["0-10", 0, 10],
  ["10-20", 10, 20],
  ["20-30", 20, 30],
  ["30-40", 30, 40],
  ["40-50", 40, 50],
  ["50-60", 50, 60],
  ["60-70", 60, 70],
  ["70-80", 70, 80],
  ["80-90", 80, 90],
  ["90-100", 90, 100],
  ["100-120", 100, 120],
  ["120-150", 120, 150],
  ["150-200", 150, 200],
  ["200-251", 200, 251],
];

async function fetchJson(pathname) {
  const res = await fetch(`${API_BASE}${pathname}`);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${pathname}`);
  }
  return res.json();
}

function csvEscape(value) {
  if (value == null) return "";
  const s = String(value);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}

function toCsv(rows, columns) {
  const header = columns.join(",");
  const body = rows.map((row) => columns.map((c) => csvEscape(row[c])).join(","));
  return `${header}\n${body.join("\n")}\n`;
}

function unique(values) {
  return new Set(values.filter((v) => v != null && v !== ""));
}

function familyOf(point) {
  return point.family || "Other";
}

function pressureClass(point) {
  const p = point.pressure_gpa;
  if (p == null || Number.isNaN(Number(p))) return "unknown_pressure";
  if (Number(p) <= 1) return "ambient_or_low_pressure";
  return "high_pressure";
}

function evidenceRegime(point) {
  const evidence = point.is_theoretical ? "theoretical" : "experimental";
  return `${evidence}_${pressureClass(point)}`;
}

function summarizeTcBands(points) {
  return tcBands.map(([band, lo, hi]) => {
    const sub = points.filter((p) => p.tc_kelvin >= lo && p.tc_kelvin < hi);
    const famCounts = new Map();
    for (const p of sub) {
      const f = familyOf(p);
      famCounts.set(f, (famCounts.get(f) || 0) + 1);
    }
    const topFamilies = [...famCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([f, n]) => `${f}:${n}`)
      .join(" ");

    return {
      band,
      lower_k: lo,
      upper_k: hi,
      width_k: hi - lo,
      points: sub.length,
      point_density_per_k: sub.length / (hi - lo),
      experimental_points: sub.filter((p) => !p.is_theoretical).length,
      theoretical_points: sub.filter((p) => p.is_theoretical).length,
      unique_materials: unique(sub.map((p) => `${p.material}|${familyOf(p)}`)).size,
      unique_papers: unique(sub.map((p) => p.paper_id)).size,
      top_families: topFamilies,
    };
  });
}

function summarizeFamilyYears(family, points) {
  const byYear = new Map();
  for (const p of points) {
    const year = Number(p.year);
    if (!Number.isFinite(year)) continue;
    if (!byYear.has(year)) {
      byYear.set(year, {
        family,
        year,
        points: 0,
        experimental_points: 0,
        theoretical_points: 0,
        unique_materials_set: new Set(),
        unique_papers_set: new Set(),
        max_tc_k: 0,
      });
    }
    const row = byYear.get(year);
    row.points += 1;
    if (p.is_theoretical) row.theoretical_points += 1;
    else row.experimental_points += 1;
    row.unique_materials_set.add(p.material);
    if (p.paper_id) row.unique_papers_set.add(p.paper_id);
    row.max_tc_k = Math.max(row.max_tc_k, Number(p.tc_kelvin || 0));
  }

  return [...byYear.values()]
    .sort((a, b) => a.year - b.year)
    .map((row, _idx, rows) => {
      const prev = [1, 2, 3].map((delta) => {
        const found = rows.find((r) => r.year === row.year - delta);
        return found?.points || 0;
      });
      const prev3_avg_points = prev.reduce((sum, n) => sum + n, 0) / 3;
      const burst_score = (row.points + 1) / (prev3_avg_points + 1);
      return {
        family: row.family,
        year: row.year,
        points: row.points,
        unique_materials: row.unique_materials_set.size,
        unique_papers: row.unique_papers_set.size,
        experimental_points: row.experimental_points,
        theoretical_points: row.theoretical_points,
        max_tc_k: row.max_tc_k,
        prev3_avg_points,
        burst_score,
        burst_candidate:
          row.points >= 20 && row.unique_materials_set.size >= 3 && burst_score >= 3,
      };
    });
}

function summarizeEvidenceRegimes(points) {
  const map = new Map();
  for (const p of points) {
    const regime = evidenceRegime(p);
    if (!map.has(regime)) {
      map.set(regime, {
        regime,
        points: 0,
        unique_materials_set: new Set(),
        unique_papers_set: new Set(),
        max_tc_k: 0,
      });
    }
    const row = map.get(regime);
    row.points += 1;
    row.unique_materials_set.add(`${p.material}|${familyOf(p)}`);
    if (p.paper_id) row.unique_papers_set.add(p.paper_id);
    row.max_tc_k = Math.max(row.max_tc_k, Number(p.tc_kelvin || 0));
  }
  return [...map.values()].map((row) => ({
    regime: row.regime,
    points: row.points,
    unique_materials: row.unique_materials_set.size,
    unique_papers: row.unique_papers_set.size,
    max_tc_k: row.max_tc_k,
  }));
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const fetchedAt = new Date().toISOString();
  const stats = await fetchJson("/stats");
  const timeline = await fetchJson("/timeline");
  const timelineExperimental = await fetchJson("/timeline?experimental_only=true");

  const materialFamilyCounts = [];
  const familyYearRows = [];
  const familyCoverage = [];

  for (const family of families) {
    const [materials, familyTimeline] = await Promise.all([
      fetchJson(`/materials?family=${family}&limit=1`),
      fetchJson(`/timeline?family=${family}`),
    ]);
    materialFamilyCounts.push({
      family,
      default_material_rows: materials.total,
    });
    familyCoverage.push({
      family,
      timeline_points: familyTimeline.coverage.total_points,
      timeline_materials: familyTimeline.coverage.total_materials,
      year_min: familyTimeline.coverage.year_min,
      year_max: familyTimeline.coverage.year_max,
    });
    familyYearRows.push(...summarizeFamilyYears(family, familyTimeline.points));
  }

  const bandRows = summarizeTcBands(timeline.points);
  const evidenceRows = summarizeEvidenceRegimes(timeline.points);
  const burstCandidates = familyYearRows
    .filter((row) => row.burst_candidate)
    .sort((a, b) => b.burst_score - a.burst_score);

  const summary = {
    fetched_at: fetchedAt,
    api_base: API_BASE,
    stats,
    timeline_coverage: timeline.coverage,
    timeline_experimental_only_coverage: timelineExperimental.coverage,
    material_family_counts: materialFamilyCounts,
    family_coverage: familyCoverage,
    tc_bands: bandRows,
    evidence_regimes: evidenceRows,
    burst_candidates: burstCandidates,
  };

  await writeFile(new URL("preliminary_metrics.json", OUT_DIR), JSON.stringify(summary, null, 2));
  await writeFile(
    new URL("tc_bands.csv", OUT_DIR),
    toCsv(bandRows, [
      "band",
      "lower_k",
      "upper_k",
      "width_k",
      "points",
      "point_density_per_k",
      "experimental_points",
      "theoretical_points",
      "unique_materials",
      "unique_papers",
      "top_families",
    ]),
  );
  await writeFile(
    new URL("family_year_counts.csv", OUT_DIR),
    toCsv(familyYearRows, [
      "family",
      "year",
      "points",
      "unique_materials",
      "unique_papers",
      "experimental_points",
      "theoretical_points",
      "max_tc_k",
      "prev3_avg_points",
      "burst_score",
      "burst_candidate",
    ]),
  );
  await writeFile(
    new URL("evidence_regimes.csv", OUT_DIR),
    toCsv(evidenceRows, [
      "regime",
      "points",
      "unique_materials",
      "unique_papers",
      "max_tc_k",
    ]),
  );

  console.log(`Wrote preliminary metrics to ${fileURLToPath(OUT_DIR)}`);
  console.log(`Timeline points: ${timeline.coverage.total_points}`);
  console.log(`Burst candidates: ${burstCandidates.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
