"""Fix indentation issue on line 150 of traffic.py"""

lines = open('api/routes/traffic.py', 'r', encoding='utf-8').readlines()

# Line 150 (index 149) has extra spaces
if lines[149].startswith('        if not code:'):
    lines[149] = '    if not code:\n'
    print("Fixed line 150 indentation")

# Line 151 (index 150) also has extra spaces  
if lines[150].startswith('        return'):
    lines[150] = '        return {"error": "Acesso negado pelo usuario ou erro no OAuth do Facebook."}\n'
    print("Fixed line 151")

open('api/routes/traffic.py', 'w', encoding='utf-8').writelines(lines)
print("Done!")
