import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remover checagem throw new Error
content = re.sub(
    r'if \(!token\) throw new Error\("Usu[aá]rio n[aã]o autenticado no Borges OS"\);',
    r'// Token verificado no backend via pendingId',
    content
)

# 2. Remover header Authorization do fetch adaccounts
content = re.sub(
    r'headers:\s*\{\s*[\'"]Authorization[\'"]:\s*[\'"]Bearer\s*[\'"]\s*\+\s*token\s*\}',
    r'headers: { "Content-Type": "application/json" }',
    content
)

# 3. Remover header Authorization do submit
content = re.sub(
    r'headers:\s*\{\s*[\'"]Content-Type[\'"]\s*:\s*[\'"]application/json[\'"]\s*,\s*[\'"]Authorization[\'"]:\s*`Bearer\s*\$\{token\}`\s*\}',
    r'headers: { "Content-Type": "application/json" }',
    content
)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html modificado para ignorar token nos fetches META.")
