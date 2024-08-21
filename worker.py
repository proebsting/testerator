import pprint
import argparse
import pickle
import contextlib
import io
import json
import sys
import importlib
from typing import (
    Callable,
    Tuple,
    Any,
    Optional,
    Dict,
    NamedTuple,
    List,
    TypeAlias,
)


def get_module_value(s: str):
    vs = s.split(".")
    mod = importlib.import_module(".".join(vs[:-1]))
    root = getattr(mod, vs[-1])
    return mod, root


# pyright: basic


class TestResult(NamedTuple):
    retval: Any
    out: io.StringIO
    err: io.StringIO
    exc: Optional[Exception]


def print_test(result: TestResult, test: Dict):
    print(f"file: {test['file']}")
    print(f"input: {test['input']}")
    print(f"expected return value: {test['output']}")
    print(f"actual return value: {result.retval}")
    print(f"expected stdout: {repr(test['stdout'])}")
    print(f"stdout: {repr(result.out.getvalue())}")
    print(f"expected stderr: {repr(test['stderr'])}")
    print(f"stderr: {repr(result.err.getvalue())}")
    if result.exc is not None:
        print(f"exception: {result.exc}")


def print_result(result: TestResult):
    print(f"actual return value:")
    pprint.pprint(result.retval)
    print(f"actual stdout: {repr(result.out.getvalue())}")
    print(f"actual stderr: {repr(result.err.getvalue())}")
    if result.exc is not None:
        print(f"actual exception: {result.exc}")


def get_function(name: str) -> Callable:
    _, fn = get_module_value(name)
    return fn


Runner: TypeAlias = Callable[[Any], Any]


def run_limited(fn: Runner, input: Any):
    limit = 100000000

    def limiter(a, b, c):
        nonlocal limit
        limit -= 1
        if limit == 0:
            raise Exception("Time limit exceeded")
        return limiter

    sys.settrace(limiter)
    student = fn(input)
    sys.settrace(None)
    return student


def run_test(input: str, funcname: str, verbose: bool, crash: bool) -> TestResult:
    out = io.StringIO()
    err = io.StringIO()
    try:
        fn = get_function(funcname)
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                student = run_limited(fn, input)
        return TestResult(student, out, err, None)
    except Exception as e:
        if crash:
            raise
        return TestResult(None, out, err, e)


def evaluate_test(
    test: Dict, verbose: bool, crash: bool
) -> Tuple[bool, TestResult, list[str]]:
    compare = get_function(test["compare"])
    result: TestResult = run_test(test["input"], test["function"], verbose, crash)
    notes: list[str] = []
    try:
        res = compare(result.retval, test["output"], crash)
    except Exception as e:
        # print(e.__notes__)
        if crash:
            raise
        res = False
        notes = [str(e)] + e.__notes__
    if res:
        res, notes = compare_text("stdout", result.out.getvalue(), test["stdout"])
    if res:
        res, notes = compare_text("stderr", result.err.getvalue(), test["stderr"])
    return (
        (type(result.exc).__name__ == type(test["error"]).__name__ and res),
        result,
        notes,
    )


def compare_text(name: str, student: str, expected: str) -> tuple[bool, list[str]]:
    if student != expected:
        notes: List[str] = [
            f"Expected {name}:\n{expected}",
            f"Actual {name}:\n{student}",
        ]
        return False, notes
    return True, []


def run(
    filenames: list[str],
    verbose: bool,
    crash: bool,
    name: Optional[str] = None,
) -> list[tuple[dict[str, Any], bool, TestResult]]:
    if verbose:
        print("Running tests")
    all: list[tuple[dict[str, Any], bool, TestResult]] = []
    for filename in filenames:
        if verbose:
            print(f"Reading {filename}")
        with open(filename, "rb") as f:
            tests: List[Dict] = pickle.load(f)
        test: dict[str, Any]
        for test in tests:
            if name is not None and test["file"] != name:
                continue
            if verbose:
                pprint.pprint(test, indent=1)
            passed: bool
            result: TestResult
            notes: list[str]
            passed, result, notes = evaluate_test(test, verbose, crash)
            all.append((test, passed, result))
            if verbose:
                print(f"passed: {passed}")
                print_result(result)
                if notes:
                    print("\n".join(notes))
                print("-----")
            elif not passed:
                print("--- Failed test:", test["file"])
                print("\n".join(notes))
    return all


def process_test_inputs(compare_name, fn_name, file_name, input: Any, verbose) -> Dict:
    result = run_test(input, fn_name, verbose, False)
    test = {
        "file": file_name,
        "function": fn_name,
        "compare": compare_name,
        "input": input,
        "output": result.retval,
        "stdout": result.out.getvalue(),
        "stderr": result.err.getvalue(),
        "error": result.exc,
    }
    return test


def read_input(args, input) -> list[str]:
    if args.verbose:
        print(f"Reading {input}")
    if args.pickle:
        with open(input, "rb") as f:
            tests = pickle.load(f)
    elif args.json:
        with open(input, "r") as f:
            tests = json.load(f)
    elif args.text:
        with open(input, "r") as f:
            tests = [f.read()]
    else:
        assert False
    return tests


def create(args: argparse.Namespace) -> None:
    outputs = []
    for fname in args.input:
        tests: list[str] = read_input(args, fname)
        for input in tests:
            output = process_test_inputs(
                args.compare,
                args.function,
                fname,
                input,
                args.verbose,
            )
            outputs.append(output)
    if args.verbose:
        print(f"Writing output.  {len(outputs)} tests")
    with open(args.output, "wb") as f:
        pickle.dump(outputs, f)


def dump_pickles(inputs: list[str], name: Optional[str]):
    for filename in inputs:
        with open(filename, "rb") as f:
            tests: list[dict[str, Any]] = pickle.load(f)
        test: dict[str, Any]
        for test in tests:
            if name is None or test["file"] == name:
                pprint.pprint(test, indent=1)
