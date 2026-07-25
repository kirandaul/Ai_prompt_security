"""
benchmark.py — run the labelled test set through the detection engine and
measure accuracy (true/false positives and negatives).

    cd backend
    python benchmark.py            # 1000 cases
    python benchmark.py 250        # smaller run

Results are stored in psg_logs.db (benchmark_runs / benchmark_cases) and shown
on the dashboard. This calls the engine directly, so it does NOT pollute the
live audit log.

Outcomes
  TP  expected sensitive, detected      -> correct catch
  FN  expected sensitive, missed        -> DANGEROUS (a leak would get through)
  FP  expected safe, flagged            -> false alarm (annoys users)
  TN  expected safe, silent             -> correct
"""
from __future__ import annotations

import asyncio
import sys
import time

import server
import storage
from benchmark_dataset import build_dataset


async def run(n: int = 1000) -> dict:
    dataset = build_dataset(n)
    storage.init_db()

    results = []
    tp = fp = tn = fn = 0
    started = time.perf_counter()

    for case in dataset:
        res = await server.scan_prompt(case["prompt"])
        detected = len(res.get("findings", [])) > 0
        expected = case["expected"]

        if expected and detected:
            outcome = "TP"; tp += 1
        elif expected and not detected:
            outcome = "FN"; fn += 1
        elif not expected and detected:
            outcome = "FP"; fp += 1
        else:
            outcome = "TN"; tn += 1

        results.append({
            "prompt": case["prompt"],
            "category": case["category"],
            "expected": expected,
            "detected": detected,
            "outcome": outcome,
            "risk_score": res.get("riskScore", 0),
            "findings": [f["reason"] for f in res.get("findings", [])],
        })

    duration_ms = int((time.perf_counter() - started) * 1000)
    total = len(results)
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

    summary = {
        "total": total, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": round(accuracy, 4), "precision": round(precision, 4),
        "recall": round(recall, 4), "f1": round(f1, 4),
        "duration_ms": duration_ms,
    }

    run_id = storage.save_benchmark(summary, results)
    summary["run_id"] = run_id

    # ---- report ----
    print("=" * 62)
    print(f"ACCURACY BENCHMARK  ·  {total} cases  ·  {duration_ms} ms "
          f"({duration_ms/total:.1f} ms/case)")
    print("=" * 62)
    print(f"  True  Positives : {tp:4}   (correctly blocked)")
    print(f"  True  Negatives : {tn:4}   (correctly allowed)")
    print(f"  False Positives : {fp:4}   (false alarms)")
    print(f"  False Negatives : {fn:4}   (MISSED leaks)")
    print("-" * 62)
    print(f"  Accuracy  {accuracy*100:6.2f}%     Precision {precision*100:6.2f}%")
    print(f"  Recall    {recall*100:6.2f}%     F1        {f1*100:6.2f}%")
    print("=" * 62)

    wrong = [r for r in results if r["outcome"] in ("FP", "FN")]
    if wrong:
        print(f"\nWrong cases ({len(wrong)}) — first 15:")
        for r in wrong[:15]:
            print(f"  [{r['outcome']}] {r['category']:20} | {r['prompt'][:56]}"
                  f" -> {','.join(r['findings']) or '-'}")
    else:
        print("\nNo wrong cases.")

    print(f"\nSaved as run #{run_id}. View it on the dashboard.")
    return summary


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    asyncio.run(run(count))
