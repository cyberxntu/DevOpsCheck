import re
import subprocess

secret_patterns = [
    r'AKIA[0-9A-Z]{16}',
    r'sk_live_[0-9a-zA-Z]{24}',
    r'sk_test_[0-9a-zA-Z]{16,}',
    r'(?i)secret[_-]?key\s*[:=]\s*["\']?[A-Za-z0-9-_]{8,}["\']?',
    r'(?i)password\s*[:=]\s*["\']?[^"\']{6,}["\']?',
    r'(?i)api[_-]?key\s*[:=]\s*["\']?[A-Za-z0-9-_]{16,}["\']?',
    r'(?i)(auth|user)?[_-]?pass(word)?\s*[:=]\s*["\']?[^"\']{6,}["\']?',
    r'(?i)(access|refresh)?[_-]?token\s*[:=]\s*["\']?[A-Za-z0-9\-_]{16,}["\']?',
    r'(?i)(client)?[_-]?secret\s*[:=]\s*["\']?[A-Za-z0-9\-_]{8,}["\']?'
]

file_extensions = ('.py', '.env', '.json', '.yml', '.yaml', '.js', '.ts')

matches = []

def load_ignore_list(file_path=".scannerignore"):
    ignore_list = set()
    if os.path.exists(file_path):
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_list.add(line)
    return ignore_list

def should_ignore(filepath, ignore_list):
    return any(ignored in filepath for ignored in ignore_list)

def scan_line(file, line, lineno):
    for pattern in secret_patterns:
        if re.search(pattern, line):
            matches.append({
                "file": file,
                "line": lineno,
                "pattern": pattern,
                "content": line.strip()
            })

def scan_git_diff():
    try:
        diff = subprocess.check_output(["git", "diff", "HEAD~1"], text=True)
        for i, line in enumerate(diff.splitlines(), 1):
            if line.startswith("+") and not line.startswith("++"):
                scan_line("GIT_DIFF", line, i)
    except Exception as e:
        print(f"[!] Git diff scan failed: {e}")

if __name__ == '__main__':
    ignore_list = load_ignore_list()
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(file_extensions):
                filepath = os.path.join(root, file)
                if should_ignore(filepath, ignore_list):
                    continue
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            scan_line(file, line, i)
                except Exception as e:
                    print(f"[!] Could not read file: {filepath} ({e})")

    scan_git_diff()

    if matches:
        with open("secrets_found.json", "w") as out:
            json.dump(matches, out, indent=2)
        print("Secrets detected:")
        for match in matches:
            print(match)
        sys.exit(1)
    else:
        print("No secrets found.")
        sys.exit(0)

