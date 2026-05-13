# Analysis Notebooks

Notebook order:

1. `01_timeline_landscape.ipynb`: first-pass analysis of the frozen API snapshot, including Tc bands, family composition, burst candidates, and theory/experiment regimes.

Before running notebooks, create a snapshot:

```bash
node data_freeze/freeze_sclib_snapshot.mjs
```

The default notebook path assumes:

```text
data_freeze/snapshots/2026.05.13/
```

If you use another snapshot id, update `SNAPSHOT_DIR` in the first notebook cell.
