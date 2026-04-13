import re
with open(r"D:\SANJAYA\sanjaya\dashboard.html", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "API" in line and ("const" in line or "var" in line or "let" in line):
        print(f"Line {i+1}: {line.strip()}")
