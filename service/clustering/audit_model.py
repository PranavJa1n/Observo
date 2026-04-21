"""Quick audit script — prints sample logs from good and bad buckets
so you can visually verify the model is making the right calls.

Usage:
    .\venv\Scripts\python.exe service\clustering\audit_model.py
"""

from service.clustering.pipeline import LogClusteringPipeline
from service.clustering.dataset_loader import load_logs
from service.clustering.config import ClusteringConfig

AUDIT_SAMPLE_SIZE = 5000     # logs to run through the pipeline
PRINT_SAMPLES    = 15        # how many examples to print per bucket

config = ClusteringConfig()

# ------------------------------------------------------------------ #
# 1. Load the trained pipeline                                        #
# ------------------------------------------------------------------ #
pipeline = LogClusteringPipeline(config)
print("Loading trained artifacts...")
pipeline.load_artifacts()

# ------------------------------------------------------------------ #
# 2. Load a fresh sample of logs (different from training data)       #
# ------------------------------------------------------------------ #
print(f"Loading {AUDIT_SAMPLE_SIZE} logs for audit...\n")
logs = load_logs(
    dataset_dir=config.dataset_dir,
    max_lines_per_file=500,        # 500 lines × ~31 files ≈ 15k candidates
    total_line_cap=AUDIT_SAMPLE_SIZE,
)

# ------------------------------------------------------------------ #
# 3. Run inference                                                    #
# ------------------------------------------------------------------ #
split = pipeline.cluster_batch(logs)

total = len(split.good_logs) + len(split.bad_logs)
pct_bad  = 100 * len(split.bad_logs)  / max(total, 1)
pct_good = 100 * len(split.good_logs) / max(total, 1)

print("=" * 60)
print("AUDIT RESULTS")
print("=" * 60)
print(f"Total logs classified : {total:,}")
print(f"Good (normal) logs    : {len(split.good_logs):,}  ({pct_good:.1f}%)")
print(f"Bad  (anomaly) logs   : {len(split.bad_logs):,}   ({pct_bad:.1f}%)")
print("=" * 60)

# ------------------------------------------------------------------ #
# 4. Print samples so you can visually verify correctness            #
# ------------------------------------------------------------------ #

print(f"\n--- SAMPLE GOOD LOGS (should look normal / informational) ---")
for log in split.good_logs[:PRINT_SAMPLES]:
    print(f"  {log}")

print(f"\n--- SAMPLE BAD LOGS (should contain errors / failures) ---")
for log in split.bad_logs[:PRINT_SAMPLES]:
    print(f"  {log}")

# ------------------------------------------------------------------ #
# 5. Check for obvious misclassifications                            #
# ------------------------------------------------------------------ #

from service.clustering.cluster_classifier import BAD_KEYWORD_RE

# Good logs that contain bad keywords (false negatives)
fn = [log for log in split.good_logs if BAD_KEYWORD_RE.search(log)]
# Bad logs that don't contain bad keywords (possible false positives)
fp = [log for log in split.bad_logs if not BAD_KEYWORD_RE.search(log)]

fn_pct = 100 * len(fn) / max(len(split.good_logs), 1)
fp_pct = 100 * len(fp) / max(len(split.bad_logs), 1)

print(f"\n--- ACCURACY CHECK ---")
print(f"Good logs that CONTAIN error keywords (possible false negatives): {len(fn):,} ({fn_pct:.1f}%)")
print(f"Bad logs with NO error keywords (possible false positives):       {len(fp):,} ({fp_pct:.1f}%)")

if fn:
    print(f"\n  Samples of good logs that might be wrong:")
    for log in fn[:5]:
        print(f"    {log}")

if fp:
    print(f"\n  Samples of bad logs without keywords:")
    for log in fp[:5]:
        print(f"    {log}")

print("\nDone.")
