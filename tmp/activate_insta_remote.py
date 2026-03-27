import sys

filepath = "/var/www/borges_os/api/routes/webhooks.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'return {"status": "temporarily_disabled"}' in line:
        new_lines.append(f"# {line}")
        print("Commented out kill-switch line.")
    elif 'if obj_type == "instagram":' in line and ":" in line:
        new_lines.append(f"# {line}")
        print("Commented out kill-switch condition.")
    else:
        new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Instagram kill-switch removed successfully.")
