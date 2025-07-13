import subprocess
import sys
import os

MAIN_SCRIPT = "llama.py"
INGREDIENTS_FILE = "ingredients_comma_format.txt"

# Helper to update OR_IDENTIFIERS in llama.py
def update_or_identifiers(terms):
    # Build the Python list string for OR_IDENTIFIERS
    or_identifiers_str = str(terms)
    # Read llama.py
    with open(MAIN_SCRIPT, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Find and replace OR_IDENTIFIERS line
    for i, line in enumerate(lines):
        if line.strip().startswith("OR_IDENTIFIERS ="):
            lines[i] = f"OR_IDENTIFIERS = {or_identifiers_str}  # Any of these terms will match (OR logic)\n"
            break
    with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:
        f.writelines(lines)

# Run llama.py and wait for output
def run_llama():
    # Show live output in console
    process = subprocess.Popen([sys.executable, MAIN_SCRIPT], stdout=sys.stdout, stderr=sys.stderr)
    process.communicate()

# Main batch loop
def main():
    with open(INGREDIENTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[14:]:  # Start from line 13 (0-indexed)
            line = line.strip()
            if not line:
                continue
            # Split by comma, strip quotes and whitespace
            terms = [term.strip().strip("'") for term in line.split(",") if term.strip()]
            print(f"\n=== Running for ingredients: {terms} ===")
            update_or_identifiers(terms)
            run_llama()

if __name__ == "__main__":
    main()
