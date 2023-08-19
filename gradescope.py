from typing import Optional, Any
import json
from worker import run, TestResult


def do_gradescope(
    filenames: list[str], outfile: str, allOrNothing: Optional[str] = None
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
    if allOrNothing is not None:
        threshold = float(allOrNothing)
        if ratio >= threshold:
            gradescope["score"] = 100
        else:
            gradescope["score"] = 0
    else:
        gradescope["score"] = 100 * correct / total

    j = json.dumps(gradescope, indent=2)
    with open(outfile, "w") as f:
        f.write(j)
