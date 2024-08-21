import argparse
import pprint
from typing import Any, Optional

from .worker import create, run, TestResult, dump_pickles


def main() -> None:
    args: argparse.Namespace = parse_args()
    inputs: list[str]
    name: Optional[str]
    match args.command:
        case "dump":
            inputs = args.input
            name = args.name
            dump_pickles(inputs, name)
        case "create":
            create(args)
        case "run":
            inputs = args.input
            verbose: bool = args.verbose or args.crash
            crash: bool = args.crash
            name = args.name
            results: list[tuple[dict[str, Any], bool, TestResult]]
            results = run(inputs, verbose, crash, name)
            out: list[dict[str, str]] = [
                {"name": te["file"], "passed": str(passed)} for te, passed, _ in results
            ]
            pprint.pprint(out, indent=4)
        case _:
            assert False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    dump = subparsers.add_parser("dump", help="Dump test pickles")
    dump.add_argument("input", nargs="+", help="input test pickle file(s)")
    dump.add_argument("--name", type=str, default=None, help="limit to a specific test")

    create = subparsers.add_parser("create", help="create a test pickle")
    create.add_argument("input", type=str, nargs="+", help="input file(s)")
    create.add_argument("--output", type=str, required=True, help="output file")
    create.add_argument("--function", type=str, required=True, help="function to test")
    create.add_argument(
        "--compare", type=str, required=True, help="comparison function"
    )
    create.add_argument("--verbose", action="store_true", help="verbose output")

    format = create.add_mutually_exclusive_group(required=True)
    format.add_argument("--pickle", action="store_true", help="input is a pickle")
    format.add_argument("--json", action="store_true", help="input is a json")
    format.add_argument("--text", action="store_true", help="input is a text file")

    run = subparsers.add_parser("run", help="run tests in a pickle file")
    run.add_argument("input", nargs="+", help="input test pickle file(s)")
    run.add_argument("--verbose", action="store_true", help="enable verbose output")
    run.add_argument("--crash", action="store_true", help="crash on error")
    run.add_argument("--name", type=str, default=None, help="limit to a specific test")

    return parser.parse_args()


if __name__ == "__main__":
    main()
