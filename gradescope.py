from typing import Optional, Any
import json
from .worker import run, TestResult


def do_gradescope(
    filenames: list[str],
    outfile: str,
    allOrNothing: Optional[float],
    minutes_late: float,
    previous_score: float,
) -> None:
    all: list[tuple[dict[str, Any], bool, TestResult]] = run(
        filenames, False, False
    )

    gradescope: dict[str, Any] = {
        "score": 0,
        "output": "",
        "visibility": "visible",
        "tests": [],
    }
    correct = 0
    total: int = len(all)
    test: dict[str, Any]
    passed: bool
    for test, passed, _ in all:
        gradescope_test = {
            "status": "passed" if passed else "failed",
            "name": test["file"],
        }
        if passed:
            correct += 1
        gradescope["tests"].append(gradescope_test)
    gradescope["output"] = f"{correct} / {total} correct"
    ratio: float = correct / total
    score: float
    if allOrNothing is not None:
        threshold = allOrNothing
        if ratio >= threshold:
            score = 100
        else:
            score = 0
    else:
        score = 100 * correct / total
    print(f"Raw score: {score}")
    if minutes_late > 0:
        penalty = minutes_late
        print(f"Late penalty: {penalty}")
        score = max(0, score - penalty)
    elif minutes_late < 0:
        bonus = -minutes_late / 1000.0
        bonus = min(10, bonus)
        print(f"Early bonus: {bonus}")
        score = score + bonus
    if previous_score > score:
        print(f"Keeping previous score: {previous_score}")
        score = previous_score
    gradescope["score"] = score

    j = json.dumps(gradescope, indent=2)
    with open(outfile, "w") as f:
        f.write(j)
