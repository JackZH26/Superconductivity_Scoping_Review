import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const API_BASE = process.env.SCLIB_API_BASE || "https://api.jzis.org/sclib/v1";
const SNAPSHOT_ID =
  process.env.SCLIB_SNAPSHOT_ID ||
  new Date().toISOString().slice(0, 10).replaceAll("-", ".");
const OUT_DIR = new URL(`./snapshots/${SNAPSHOT_ID}/`, import.meta.url);
const MATERIAL_LIMIT = Number(process.env.SCLIB_MATERIAL_LIMIT || 200);
const INCLUDE_DETAILS = process.argv.includes("--details");

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

async function fetchJson(pathname) {
  const url = `${API_BASE}${pathname}`;
  const maxAttempts = 6;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const res = await fetch(url, {
      headers: { "User-Agent": "SCLib-scope-review-freeze/0.1" },
    });
    if (res.ok) return res.json();

    const retryable = res.status === 429 || res.status >= 500;
    if (!retryable || attempt === maxAttempts) {
      throw new Error(`${res.status} ${res.statusText}: ${url}`);
    }

    const retryAfter = Number(res.headers.get("retry-after"));
    const waitMs = Number.isFinite(retryAfter)
      ? retryAfter * 1000
      : Math.min(60_000, 1500 * 2 ** (attempt - 1));
    console.log(
      `retry ${attempt}/${maxAttempts - 1} after ${res.status} for ${pathname}; waiting ${Math.round(waitMs / 1000)}s`,
    );
    await new Promise((resolve) => setTimeout(resolve, waitMs));
  }
}

function csvEscape(value) {
  if (value == null) return "";
  const s = typeof value === "object" ? JSON.stringify(value) : String(value);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}

function toCsv(rows, columns) {
  const header = columns.join(",");
  const body = rows.map((row) => columns.map((c) => csvEscape(row[c])).join(","));
  return `${header}\n${body.join("\n")}\n`;
}

async function writeJson(name, payload) {
  const bytes = JSON.stringify(payload, null, 2);
  await writeFile(new URL(name, OUT_DIR), bytes);
  return createHash("sha256").update(bytes).digest("hex");
}

async function writeCsv(name, rows, columns) {
  const bytes = toCsv(rows, columns);
  await writeFile(new URL(name, OUT_DIR), bytes);
  return createHash("sha256").update(bytes).digest("hex");
}

async function fetchAllMaterials(extraQuery = "") {
  const rows = [];
  let offset = 0;
  let total = null;
  while (total == null || offset < total) {
    const joiner = extraQuery ? `&${extraQuery}` : "";
    const payload = await fetchJson(
      `/materials?limit=${MATERIAL_LIMIT}&offset=${offset}${joiner}`,
    );
    total = payload.total;
    rows.push(...payload.results);
    offset += payload.results.length;
    if (payload.results.length === 0) break;
    process.stdout.write(
      `materials ${extraQuery || "default"}: ${rows.length}/${total}\r`,
    );
  }
  process.stdout.write("\n");
  return { total, results: rows };
}

async function fetchMaterialDetails(materials) {
  const details = [];
  let i = 0;
  for (const material of materials) {
    i += 1;
    const encoded = encodeURIComponent(material.id);
    details.push(await fetchJson(`/materials/${encoded}`));
    if (i % 100 === 0 || i === materials.length) {
      process.stdout.write(`material details: ${i}/${materials.length}\r`);
    }
  }
  process.stdout.write("\n");
  return details;
}

function flattenTimelinePoints(points) {
  return points.map((p) => ({
    material: p.material,
    formula_latex: p.formula_latex,
    family: p.family || "Other",
    tc_kelvin: p.tc_kelvin,
    year: p.year,
    pressure_gpa: p.pressure_gpa,
    paper_id: p.paper_id,
    is_theoretical: p.is_theoretical,
  }));
}

function familyCountsFromMaterials(materials) {
  const counts = new Map();
  for (const row of materials) {
    const key = row.family || "Other";
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([family, count]) => ({ family, count }));
}

function deriveSnapshotReadme(metadata) {
  return `# SCLib Snapshot ${metadata.snapshot_id}

Frozen at: ${metadata.frozen_at}

API base: ${metadata.api_base}

Dataset version reported by SCLib: ${metadata.stats.dataset_version || "unknown"}

## Contents

- \`metadata.json\`: freeze metadata, counts, and file hashes.
- \`stats.json\`: SCLib stats endpoint payload.
- \`timeline.json\`: full public timeline endpoint payload.
- \`timeline_experimental_only.json\`: timeline endpoint with \`experimental_only=true\`.
- \`timeline_points.csv\`: flattened timeline points for notebook analysis.
- \`timeline_experimental_only_points.csv\`: flattened experimental-only points.
- \`materials_default_summary.json/csv\`: default public materials list.
- \`materials_all_summary.json/csv\`: materials list with \`include_pending=true&include_skeletons=true\`.
- \`material_family_counts.csv\`: family counts from all material summaries.

This API-level snapshot is sufficient for the first timeline-landscape analysis.
For the final manuscript, export a database-level snapshot of papers, material
details, and raw \`materials.records\` to support full validation and provenance.
`;
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const frozenAt = new Date().toISOString();
  const fileHashes = {};

  console.log(`Freezing SCLib API snapshot ${SNAPSHOT_ID}`);
  console.log(`Output: ${fileURLToPath(OUT_DIR)}`);

  const stats = await fetchJson("/stats");
  const timeline = await fetchJson("/timeline");
  const timelineExperimental = await fetchJson("/timeline?experimental_only=true");
  const materialsDefault = await fetchAllMaterials("");
  const materialsAll = await fetchAllMaterials(
    "include_pending=true&include_skeletons=true",
  );

  const timelineRows = flattenTimelinePoints(timeline.points || []);
  const timelineExperimentalRows = flattenTimelinePoints(
    timelineExperimental.points || [],
  );
  const familyCounts = familyCountsFromMaterials(materialsAll.results);

  fileHashes["stats.json"] = await writeJson("stats.json", stats);
  fileHashes["timeline.json"] = await writeJson("timeline.json", timeline);
  fileHashes["timeline_experimental_only.json"] = await writeJson(
    "timeline_experimental_only.json",
    timelineExperimental,
  );
  fileHashes["materials_default_summary.json"] = await writeJson(
    "materials_default_summary.json",
    materialsDefault,
  );
  fileHashes["materials_all_summary.json"] = await writeJson(
    "materials_all_summary.json",
    materialsAll,
  );
  fileHashes["timeline_points.csv"] = await writeCsv(
    "timeline_points.csv",
    timelineRows,
    [
      "material",
      "formula_latex",
      "family",
      "tc_kelvin",
      "year",
      "pressure_gpa",
      "paper_id",
      "is_theoretical",
    ],
  );
  fileHashes["timeline_experimental_only_points.csv"] = await writeCsv(
    "timeline_experimental_only_points.csv",
    timelineExperimentalRows,
    [
      "material",
      "formula_latex",
      "family",
      "tc_kelvin",
      "year",
      "pressure_gpa",
      "paper_id",
      "is_theoretical",
    ],
  );
  fileHashes["materials_default_summary.csv"] = await writeCsv(
    "materials_default_summary.csv",
    materialsDefault.results,
    [
      "id",
      "formula",
      "formula_latex",
      "family",
      "subfamily",
      "tc_max",
      "tc_max_conditions",
      "tc_ambient",
      "discovery_year",
      "total_papers",
      "status",
      "pairing_symmetry",
      "structure_phase",
      "ambient_sc",
      "is_topological",
      "is_unconventional",
      "is_2d_or_interface",
      "has_competing_order",
    ],
  );
  fileHashes["materials_all_summary.csv"] = await writeCsv(
    "materials_all_summary.csv",
    materialsAll.results,
    [
      "id",
      "formula",
      "formula_latex",
      "family",
      "subfamily",
      "tc_max",
      "tc_max_conditions",
      "tc_ambient",
      "discovery_year",
      "total_papers",
      "status",
      "pairing_symmetry",
      "structure_phase",
      "ambient_sc",
      "is_topological",
      "is_unconventional",
      "is_2d_or_interface",
      "has_competing_order",
    ],
  );
  fileHashes["material_family_counts.csv"] = await writeCsv(
    "material_family_counts.csv",
    familyCounts,
    ["family", "count"],
  );

  if (INCLUDE_DETAILS) {
    const details = await fetchMaterialDetails(materialsAll.results);
    fileHashes["materials_all_details.json"] = await writeJson(
      "materials_all_details.json",
      { total: details.length, results: details },
    );
  }

  const metadata = {
    snapshot_id: SNAPSHOT_ID,
    frozen_at: frozenAt,
    api_base: API_BASE,
    include_details: INCLUDE_DETAILS,
    stats,
    endpoint_counts: {
      timeline_points: timeline.coverage?.total_points,
      timeline_materials: timeline.coverage?.total_materials,
      timeline_experimental_only_points:
        timelineExperimental.coverage?.total_points,
      timeline_experimental_only_materials:
        timelineExperimental.coverage?.total_materials,
      materials_default_total: materialsDefault.total,
      materials_all_total: materialsAll.total,
    },
    family_slugs_checked: families,
    file_hashes_sha256: fileHashes,
    limitations: [
      "This is an API-level snapshot, not a direct production database dump.",
      "The public timeline endpoint is already filtered and de-duplicated by SCLib rules.",
      "The materials summary endpoint does not include full materials.records arrays unless --details is used.",
      "A final manuscript-grade freeze should include database-level papers, chunks metadata, materials details, and raw per-paper NER records.",
    ],
  };
  fileHashes["metadata.json"] = await writeJson("metadata.json", metadata);
  await writeFile(new URL("README.md", OUT_DIR), deriveSnapshotReadme(metadata));

  console.log("Snapshot complete");
  console.log(JSON.stringify(metadata.endpoint_counts, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
