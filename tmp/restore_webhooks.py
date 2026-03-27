import os

filepath = "/var/www/borges_os/api/routes/webhooks.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
removed_count = 0
for line in lines:
    if "[WEBHOOK IG]" in line:
        removed_count += 1
        continue
    new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Restored webhooks.py. Removed {removed_count} debug lines.")
