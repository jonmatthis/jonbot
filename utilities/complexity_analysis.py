import os

from radon.complexity import cc_visit
from radon.metrics import h_visit
from radon.raw import analyze


def get_complexity_results(directory):
    cc_results = []
    mi_results = {}
    halstead_results = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                    # Fetch cyclomatic complexity results
                    cc_results.extend(cc_visit(code))
                    # Fetch raw metrics results (like number of lines, etc.)
                    mi_results[filepath] = analyze(code)
                    # Fetch Halstead complexity results
                    halstead_results[filepath] = h_visit(code)

    return cc_results, mi_results, halstead_results


def main(directory):
    cc_results, mi_results, halstead_results = get_complexity_results(directory)

    CC_THRESHOLD = 15

    print("Areas to consider based on Cyclomatic Complexity:")
    for result in cc_results:
        if result.complexity > CC_THRESHOLD:
            print(f"{result.nick_name} in {result.filename}, Line {result.lineno}, CC: {result.complexity}")
    print("\n" + "-" * 50)  # Add separator for readability

    print("\nAreas to consider based on Raw Metrics:")
    for filename, result in mi_results.items():
        print(f"\nFile: {filename}")
        print(f"  LOC: {result.loc}, LLOC: {result.lloc}, SLOC: {result.sloc}")
        print(f"  Comments: {result.comments}, Multi-line comments: {result.multi}")
        print(f"  Blank lines: {result.blank}, Single-line comments: {result.single_comments}")
    print("\n" + "-" * 50)  # Add separator for readability

    print("\nHalstead Metrics:")
    for filename, result in halstead_results.items():
        print(f"\nFile: {filename}")
        print(f"  Vocabulary: {result.vocabulary}, Length: {result.length}")
        print(f"  Volume: {round(result.volume, 2)}, Difficulty: {round(result.difficulty, 2)}")
        print(f"  Effort: {round(result.effort, 2)}, Time: {round(result.time, 2)}, Bugs: {round(result.bugs, 4)}")


if __name__ == "__main__":
    directory = r"C:\Users\jonma\github_repos\jonmatthis\jonbot\jonbot"
    main(directory)
