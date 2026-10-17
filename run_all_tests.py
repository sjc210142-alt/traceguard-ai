import os
import sys
import subprocess
import importlib.util
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

TEST_FILES = [
    "test_graph.py",
    "test_fraud_detector.py",
    "test_ai_assistant.py",
]

results = []


def run_test(name, command):
    print(f"\n{'=' * 60}")
    print(f"TEST: {name}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=240,
            encoding="utf-8",
            errors="replace",
        )

        if result.stdout:
            print(result.stdout[-6000:])

        if result.stderr:
            print("ERROR OUTPUT:")
            print(result.stderr[-3000:])

        passed = result.returncode == 0
        results.append((name, passed))

        print("RESULT:", "PASS" if passed else "FAIL")

    except subprocess.TimeoutExpired:
        results.append((name, False))
        print("RESULT: FAIL - Test timed out")

    except Exception as exc:
        results.append((name, False))
        print(f"RESULT: FAIL - {exc}")


def check_module(name):
    available = importlib.util.find_spec(name) is not None
    results.append((f"Package: {name}", available))
    print(f"{name}: {'PASS' if available else 'FAIL'}")


def main():
    print("=" * 60)
    print("          TRACEGUARD AI - AUTOMATED TEST RUNNER")
    print("=" * 60)

    print("\nPython executable:", sys.executable)
    print("Project directory:", PROJECT_DIR)

    # 1. Check required packages.
    print("\n--- PACKAGE CHECKS ---")

    for package in [
        "streamlit",
        "pandas",
        "falkordb",
        "streamlit_agraph",
    ]:
        check_module(package)

    # 2. Check required project files.
    print("\n--- FILE CHECKS ---")

    required_files = [
        "app.py",
        "fraud_detector.py",
        "ai_assistant.py",
        "investigation_history.py",
    ]

    for filename in required_files:
        exists = (PROJECT_DIR / filename).exists()

        # Some project files may be inside .venv.
        if not exists:
            exists = (PROJECT_DIR / ".venv" / filename).exists()

        results.append((f"File: {filename}", exists))
        print(f"{filename}: {'PASS' if exists else 'FAIL'}")

    # 3. Check FalkorDB connectivity.
    run_test(
        "FalkorDB connectivity",
        [
            sys.executable,
            "-c",
            (
                "from falkordb import FalkorDB; "
                "db = FalkorDB(host='localhost', port=6379); "
                "graph = db.select_graph('traceguard'); "
                "result = graph.query('RETURN 1 AS test'); "
                "assert result.result_set; "
                "print('FalkorDB connection and query successful')"
            ),
        ],
    )

    # 4. Run existing tests.
    for filename in TEST_FILES:
        test_path = PROJECT_DIR / filename

        if not test_path.exists():
            test_path = PROJECT_DIR / ".venv" / filename

        if test_path.exists():
            run_test(
                filename,
                [sys.executable, str(test_path)],
            )
        else:
            results.append((filename, False))
            print(f"\nMISSING TEST FILE: {filename}")

    # 5. Check investigation-history database.
    run_test(
        "Investigation history",
        [
            sys.executable,
            "-c",
            (
                "from investigation_history import "
                "initialize_database, get_investigation_history; "
                "initialize_database(); "
                "records = get_investigation_history(limit=5); "
                "assert isinstance(records, list); "
                "print('History module works; records found:', len(records))"
            ),
        ],
    )

    # 6. Check AI model availability.
    run_test(
        "Ollama service and model",
        [
            sys.executable,
            "-c",
            (
                "import json, urllib.request; "
                "url = 'http://localhost:11434/api/tags'; "
                "response = urllib.request.urlopen(url, timeout=5); "
                "data = json.loads(response.read().decode()); "
                "models = [m.get('name', '') for m in data.get('models', [])]; "
                "print('Available models:', models); "
                "assert any(m == 'llama3.2' or m.startswith('llama3.2:') "
                "for m in models), 'llama3.2 model not found'; "
                "print('Ollama and llama3.2 are available')"
            ),
        ],
    )

    # 7. Final summary.
    print("\n" + "=" * 60)
    print("              FINAL TEST REPORT")
    print("=" * 60)

    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    passed_count = sum(1 for _, passed in results if passed)
    failed_count = len(results) - passed_count

    print("-" * 60)
    print("TOTAL:", len(results))
    print("PASSED:", passed_count)
    print("FAILED:", failed_count)
    print("=" * 60)

    if failed_count:
        print("\nSome checks failed. Review the errors above.")
        sys.exit(1)

    print("\nAll configured checks passed!")


if __name__ == "__main__":
    main()