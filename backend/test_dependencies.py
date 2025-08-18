import sys

packages = [
    "blinker",
    "certifi",
    "cffi",
    "click",
    "contourpy",
    "cycler",
    "Flask",
    "flask_cors",
    "flatbuffers",
    "fontTools",
    "geographiclib",
    "geopy",
    "h3",
    "itsdangerous",
    "jinja2",
    "kiwisolver",
    "MarkupSafe",
    "matplotlib",
    "numpy",
    "packaging",
    "PIL",
    "pycparser",
    "pyparsing",
    "dateutil",
    "six",
    "timezonefinder",
    "werkzeug",
    "gunicorn",
    "flatlib",
    "pytz",
    "swisseph"
]

failed = []

for pkg in packages:
    try:
        __import__(pkg)
        print(f"[OK] {pkg}")
    except ImportError as e:
        print(f"[FAIL] {pkg} → {e}")
        failed.append(pkg)

if failed:
    print("\nДеякі пакети не імпортуються:")
    for f in failed:
        print(f" - {f}")
    sys.exit(1)

print("\nУсі пакети імпортуються без помилок!")

# Тест Gunicorn (dry-run)
print("\nТест Gunicorn (dry-run)...")
import subprocess

try:
    subprocess.run(
        ["gunicorn", "--version"],
        check=True
    )
    print("[OK] Gunicorn доступний")
except Exception as e:
    print(f"[FAIL] Gunicorn → {e}")
    sys.exit(1)