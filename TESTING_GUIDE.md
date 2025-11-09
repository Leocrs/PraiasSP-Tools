# 🧪 Guia de Testes - Riviera Ingestor

## ✅ Teste Rápido (5 minutos)

### 1. Verificar Estrutura

```bash
cd PraiasSP-Tools
ls -la
# Verificar se os arquivos principais existem
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
# Aguardar instalação completa
```

### 3. Rodar Testes Automáticos

```bash
bash test.sh
# Ou no Windows:
python test_windows.py
```

### 4. Inicializar Banco

```bash
python -c "from api.index import init_db; init_db()"
# Deve retornar: ✅ Banco de dados inicializado com sucesso
```

### 5. Executar Aplicação

```bash
python api/index.py
# Deve retornar:
# * Serving Flask app 'api.index'
# * WARNING: This is a development server
# * Running on http://127.0.0.1:5000
```

### 6. Acessar no Navegador

```
http://localhost:5000
```

---

## 🔍 Teste de Endpoints (usando curl)

### Health Check

```bash
curl http://localhost:5000/health

# Esperado:
# {
#   "status": "ok",
#   "timestamp": "2025-09-09T18:30:00",
#   "service": "Riviera Ingestor"
# }
```

### Listar Movimentos (Vazio no Início)

```bash
curl http://localhost:5000/api/movimentos

# Esperado:
# {
#   "status": "success",
#   "count": 0,
#   "data": []
# }
```

### Resumo

```bash
curl http://localhost:5000/api/resumo

# Esperado:
# {
#   "status": "success",
#   "resumo": {
#     "obras": [],
#     "totais": {...}
#   }
# }
```

### Configurações

```bash
curl http://localhost:5000/api/configuracoes

# Esperado:
# {
#   "status": "success",
#   "configuracoes": {}
# }
```

---

## 📤 Teste de Upload

### Com curl

```bash
curl -F "files=@exemplo.pdf" http://localhost:5000/api/upload

# Nota: O arquivo exemplo.pdf deve existir
```

### Com Python

```python
import requests

with open('exemplo.pdf', 'rb') as f:
    files = {'files': f}
    response = requests.post(
        'http://localhost:5000/api/upload',
        files=files
    )
    print(response.json())
```

### Com JavaScript

```javascript
const formData = new FormData();
formData.append("files", fileInput.files[0]);

fetch("/api/upload", {
  method: "POST",
  body: formData,
})
  .then((r) => r.json())
  .then((data) => console.log(data))
  .catch((e) => console.error(e));
```

---

## 💾 Teste de Banco de Dados

### Conectar Diretamente

```bash
sqlite3 data/historico_riviera.db

# Listar tabelas
.tables

# Ver schema
.schema movimentos

# Sair
.quit
```

### Com Python

```python
import sqlite3

conn = sqlite3.connect('data/historico_riviera.db')
cursor = conn.cursor()

# Listar tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tabelas: {tables}")

# Contar registros
cursor.execute("SELECT COUNT(*) FROM movimentos")
count = cursor.fetchone()[0]
print(f"Movimentos: {count}")

conn.close()
```

---

## 🎨 Teste de Interface

### Elementos que Devem Estar Visíveis

✅ **Header**

- Logo verde
- Título "Riviera Ingestor"
- Subtítulo

✅ **Navegação**

- Menu com 5 abas
- Hover effects

✅ **Dashboard**

- 4 cards de métricas
- Cards com cores diferentes
- Tabela vazia (sem dados ainda)

✅ **Upload**

- Input de arquivo
- Botões "Fazer Upload" e "Limpar"

✅ **Formulários**

- Inputs com label
- Validação visual

✅ **Responsividade**

- Redimensionar janela
- Verificar se layout se adapta

---

## 🔐 Teste de Segurança

### Verificar .gitignore

```bash
# Verificar se .env está ignorado
git check-ignore .env
# Deve retornar: .env

# Verificar se *.db está ignorado
git check-ignore data/historico_riviera.db
# Deve retornar: data/historico_riviera.db
```

### Testar SQL Injection

```bash
# Isto não deve quebrar o sistema
curl "http://localhost:5000/api/movimentos?codigo_obra=603'; DROP TABLE movimentos;--"

# O sistema deve retornar erro gracefully
```

### Testar Upload de Arquivo Inválido

```bash
# Tentar fazer upload de arquivo .txt
curl -F "files=@teste.txt" http://localhost:5000/api/upload

# Deve retornar erro: "apenas PDFs"
```

---

## 📊 Teste com Dados de Exemplo

### Inserir Dados Manualmente

```python
from api.index import get_db_connection

dados = [
    ('2025-09', '603', 'Ampliação Shopping Riviera', 'Despesa', 1000000.00, 'Manual'),
    ('2025-09', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 500000.00, 'Manual'),
]

with get_db_connection() as conn:
    cursor = conn.cursor()
    for dado in dados:
        cursor.execute('''
            INSERT INTO movimentos
            (competencia, codigo_obra, obra_nome, tipo, valor, fonte)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', dado)
    conn.commit()

print("✅ Dados inseridos!")
```

### Verificar Dados no Dashboard

```bash
# Abrir http://localhost:5000
# Verificar se os dados aparecem:
# - Cards atualizados
# - Tabela de obras preenchida
```

---

## 🐛 Troubleshooting Rápido

### Erro: `ModuleNotFoundError: No module named 'flask'`

```bash
pip install -r requirements.txt
```

### Erro: `Port 5000 already in use`

```bash
# Mudar porta
export PORT=5001
python api/index.py

# Ou matar processo
lsof -ti:5000 | xargs kill -9
```

### Erro: `Database locked`

```bash
# SQLite está em uso - aguarde ou reinicie
# Verificar se há outro processo Python rodando
ps aux | grep python
```

### Interface não carrega

```bash
# Verificar console do navegador (F12)
# Verificar se CSS e JS estão sendo carregados
# Verificar aba "Network"
```

---

## ✨ Teste de Qualidade

### Performance

- Dashboard carrega em < 2 segundos
- Upload de arquivo em < 5 segundos
- Busca de dados em < 1 segundo

### Responsividade

- Desktop: 100% funcional
- Tablet: layout adaptado
- Mobile: navegação por abas

### Browser Compatibility

- Chrome ✅
- Firefox ✅
- Safari ✅
- Edge ✅

---

## 📋 Checklist de Testes Antes de Deploy

```bash
# Executar tudo isto antes de fazer deploy

# 1. Teste estrutura
bash test.sh

# 2. Teste API
curl http://localhost:5000/health

# 3. Teste banco
python -c "from api.index import init_db; init_db()"

# 4. Verificar segurança
git check-ignore .env
git check-ignore '*.db'

# 5. Verificar dependências
pip check

# 6. Verificar código
python -m py_compile api/index.py

# 7. Limpar cache
find . -type d -name __pycache__ -exec rm -rf {} +

# 8. Listar arquivos
git status

# 9. Fazer commit
git add .
git commit -m "Deploy Phase 1 - Riviera Ingestor v1.0.0"

# 10. Push
git push origin main
```

---

## 🎓 Scripts de Teste Úteis

### test_api.py

```python
import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    print(f"Health: {r.status_code}")
    return r.status_code == 200

def test_api():
    endpoints = [
        "/api/movimentos",
        "/api/resumo",
        "/api/orcamento",
        "/api/configuracoes"
    ]

    for endpoint in endpoints:
        r = requests.get(f"{BASE_URL}{endpoint}")
        print(f"{endpoint}: {r.status_code}")

if __name__ == "__main__":
    print("🧪 Testando API...")
    test_health()
    test_api()
    print("✅ Testes completos!")
```

---

## 📸 Screenshots Esperadas

### 1. Dashboard

```
┌─────────────────────────────────────────┐
│  🟢 Riviera Ingestor - Tools            │
│  Consolidação de Relatórios Financeiros │
└─────────────────────────────────────────┘

Dashboard | Upload | Movimentos | Orçamento | Relatórios

┌──────────┬──────────┬──────────┬──────────┐
│Despesas  │  Aportes │Rental.  │ Saldo   │
│R$ 0,00   │ R$ 0,00  │R$ 0,00  │ R$ 0,00 │
└──────────┴──────────┴──────────┴──────────┘

Tabela vazia (sem dados)
```

### 2. Upload

```
Selecione os arquivos PDF
[📁 Escolher Arquivos]
0 arquivo(s) selecionado(s)

[✓ Fazer Upload] [🗑️ Limpar]
```

---

## 🎯 Resultado Esperado

✅ Estrutura criada  
✅ Dependências instaladas  
✅ Banco funcionando  
✅ API respondendo  
✅ Interface carregando  
✅ Dashboard vazio (pronto para dados)

**Status**: 🟢 **Pronto para Fase 2**

---

**Tempo Esperado para Testes Completos**: 10-15 minutos
