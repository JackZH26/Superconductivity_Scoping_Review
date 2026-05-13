from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


VALIDATION_FIELDS = [
    "formula_valid",
    "family_valid",
    "tc_valid",
    "pressure_valid",
    "pressure_role_valid",
    "ambient_valid",
    "evidence_type_valid",
    "is_theoretical_valid",
]


def parse_bool(value):
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    if s in {"true", "t", "yes", "y", "1"}:
        return True
    if s in {"false", "f", "no", "n", "0"}:
        return False
    return None


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    phat = k / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = z * ((phat * (1 - phat) / n + z**2 / (4 * n**2)) ** 0.5) / denom
    return center - margin, center + margin


def score_field(frame: pd.DataFrame, field: str) -> dict:
    vals = frame[field].map(parse_bool)
    reviewed = vals.dropna()
    n = len(reviewed)
    k = int(reviewed.sum()) if n else 0
    lo, hi = wilson_ci(k, n)
    return {
        "field": field,
        "reviewed_n": n,
        "valid_n": k,
        "accuracy": k / n if n else None,
        "wilson95_low": lo,
        "wilson95_high": hi,
    }


def explode_strata(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        strata = str(row.get("sample_strata", "")).split(";")
        for stratum in [s for s in strata if s]:
            out = row.to_dict()
            out["stratum"] = stratum
            rows.append(out)
    return pd.DataFrame(rows)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 validation/score_validation.py <validation_sample.csv>")

    path = Path(sys.argv[1]).resolve()
    frame = pd.read_csv(path)
    out_dir = path.parent

    metrics = pd.DataFrame([score_field(frame, field) for field in VALIDATION_FIELDS])

    exclude_vals = frame.get("should_exclude_from_main", pd.Series([], dtype=object)).map(parse_bool)
    reviewed_exclude = exclude_vals.dropna()
    if len(reviewed_exclude):
        metrics = pd.concat(
            [
                metrics,
                pd.DataFrame(
                    [
                        {
                            "field": "should_exclude_from_main_rate",
                            "reviewed_n": len(reviewed_exclude),
                            "valid_n": int(reviewed_exclude.sum()),
                            "accuracy": reviewed_exclude.mean(),
                            "wilson95_low": wilson_ci(int(reviewed_exclude.sum()), len(reviewed_exclude))[0],
                            "wilson95_high": wilson_ci(int(reviewed_exclude.sum()), len(reviewed_exclude))[1],
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    metrics.to_csv(out_dir / "validation_metrics.csv", index=False)

    stratum_frame = explode_strata(frame)
    stratum_rows = []
    if len(stratum_frame):
        for stratum, group in stratum_frame.groupby("stratum"):
            for field in VALIDATION_FIELDS:
                row = score_field(group, field)
                row["stratum"] = stratum
                stratum_rows.append(row)
    pd.DataFrame(stratum_rows).to_csv(out_dir / "validation_stratum_metrics.csv", index=False)

    print(metrics.to_string(index=False))
    print(f"Wrote metrics to {out_dir}")


if __name__ == "__main__":
    main()
