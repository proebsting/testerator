import difflib
import pprint

RED, GREEN, RESET = "", "", ""
try:
    import colorama

    colorama.init(autoreset=True)
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    RESET = colorama.Fore.RESET
except ModuleNotFoundError:
    pass

INDENT = 4
WIDTH = 80


def compare_objects(correct: "object", student: "object") -> "list[str]":
    correct_str: str = pprint.pformat(correct, indent=INDENT, width=WIDTH)
    student_str: str = pprint.pformat(student, indent=INDENT, width=WIDTH)

    diff_iter = diff_strs(correct_str, student_str)
    return list(diff_iter)


def print_diff(diff_iter: "list[str]", color=True) -> None:
    for line in diff_iter:
        marker = line[0]
        if marker == " ":
            print(line)
        elif marker == "+":
            print(RED + f"{line.replace('+', '-')}")
        elif marker == "-":
            print(GREEN + f"{line.replace('-', '+')}")
        else:
            continue
        print(RESET, end="")
    print()


def diff_strs(correct: str, student: str) -> "list[str]":
    differ = difflib.Differ()
    diff = differ.compare(correct.splitlines(), student.splitlines())
    return list(diff)
