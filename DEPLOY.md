# 🚀 DEPLOY & PRODUÇÃO - Guia Único

## ⚡ Status Atual (Nov 11, 2025)

✅ **PRODUÇÃO ATIVA**: Backend (Render) e Frontend (Vercel) integrados

- Backend: https://praiassp-tools.onrender.com
- Frontend: https://praias-sp-tools.vercel.app

---

## 🔑 Configuração .env (Copie/Cole)

Crie arquivo `.env` na raiz com:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-[sua-chave-da-openai-aqui]

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=[gere-uma-chave-aleatória-aqui-32-caracteres]

# Database
DATABASE_PATH=./data/historico_riviera.db

# Upload
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=52428800

# CORS
CORS_ORIGINS=https://praias-sp-tools.vercel.app,https://praiassp-tools.onrender.com
```

### Onde Obter as Chaves?

| Chave            | Onde Obter                                                           |
| ---------------- | -------------------------------------------------------------------- |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys                                 |
| `SECRET_KEY`     | Gere com: `python -c "import secrets; print(secrets.token_hex(16))"` |

---

## 🏃 Setup Local (Rápido)

```bash
# 1. Ativar venv
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Instalar
pip install -r requirements.txt

# 3. Criar .env (copiar .env.example)
cp .env.example .env
# EDITAR .env com suas chaves
```

---

## 🌎 Deploy Produção

### Backend (Render)

1. Conectar repo GitHub
2. Definir env vars do `.env`
3. Build automático
4. Start: `gunicorn --config gunicorn.conf.py api.index:app`

### Frontend (Vercel)

1. Conectar repo GitHub
2. Deploy automático
3. `vercel.json` e `.vercelignore` já configurados

---

## 🧪 Testes de Produção (curl)

```bash
# Testar resumo
curl -i https://praiassp-tools.onrender.com/api/resumo

# Testar movimentos
curl -i https://praiassp-tools.onrender.com/api/movimentos

# Testar upload PDF
curl -i https://praiassp-tools.onrender.com/api/upload -X POST -F "files=@seuarquivo.pdf"
```

---

## 🛠️ Troubleshooting

- 404 no Vercel: verifique se `index.html` está na raiz e `.vercelignore` não está ignorando arquivos estáticos
- 500 no backend: veja logs do Render
- CORS: confira se `CORS_ORIGINS` cobre ambos domínios

---

## 📋 Próximos Passos

- [ ] Monitoramento (Sentry, uptime)
- [ ] Otimização de performance
- [ ] Documentação de API

# 4. Rodar

python api/index.py

# 5. Testar

curl -F "file=@relatorio.pdf" http://localhost:5000/api/analyze-pdf

```

---

## 📊 O Que Funciona Agora

### ✅ Endpoint Implementado

```

POST /api/analyze-pdf

Input: multipart/form-data (file: PDF)

Output (200):
{
"status": "success",
"message": "PDF analisado e salvo com sucesso",
"data": {
"competencia": "11/2025",
"codigo_obra": "OBR001",
"obra_nome": "Riviera",
"movimentos": [
{"tipo": "Despesa", "valor": 10000.00, "fonte": "Fornecedor", "descricao": "..."}
],
"observacoes": "..."
}
}

```

---

## 🌐 Deploy Vercel (Frontend)

### Passo 1: Conectar Repositório

1. Abra https://vercel.com
2. Clique "New Project"
3. Selecione repositório `PraiasSP-Tools`
4. Deploy automático

### Passo 2: Variáveis de Ambiente

No Vercel Dashboard:

- Settings → Environment Variables
- Adicione:
```

REACT_APP_API_URL=https://[seu-render-domain].onrender.com

```

---

## 🖥️ Deploy Render (Backend)

### Passo 1: Criar Web Service

1. Abra https://render.com
2. New → Web Service
3. GitHub → Selecione `PraiasSP-Tools`

### Passo 2: Configurar

```

Name: praias-sp-tools-api
Runtime: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: gunicorn --config gunicorn.conf.py api.index:app

```

### Passo 3: Environment Variables

No Render Dashboard → Environment:

```

OPENAI_API_KEY=sk-proj-[sua-chave]
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=[sua-chave-secreta]
DATABASE_PATH=./data/historico_riviera.db
UPLOAD_FOLDER=/var/data/uploads
MAX_FILE_SIZE=52428800
CORS_ORIGINS=https://[seu-vercel-domain].vercel.app,http://localhost:3000
PORT=10000

````

### Passo 4: Deploy

Render faz deploy automático a cada push para `main`

---

## ✅ Verificar Deploy

```bash
# Testar Render
curl https://[seu-render-domain].onrender.com/health

# Resultado esperado:
# {"status": "ok", "timestamp": "...", "service": "Riviera Ingestor"}
````

---

## 🔴 Problemas Comuns & Soluções

### ❌ "OPENAI_API_KEY not found"

```
✓ Verificar: existe .env na raiz?
✓ Verificar: .env tem OPENAI_API_KEY=sk-proj-...?
✓ Render: confirmou variável em Environment?
```

### ❌ "ModuleNotFoundError: No module named 'openai'"

```
✓ Verificar: pip install -r requirements.txt?
✓ Render: Build command rodou?
```

### ❌ "Connection refused" (Render)

```
✓ Render ainda está fazendo build? Aguarde 2-3 min
✓ Verificar: Port 10000 configurado?
✓ Verificar: gunicorn.conf.py existe?
```

### ❌ "PDF not extractable"

```
✓ PDF não tem texto? (é imagem/scan?)
✓ Usar PDF com texto extraível
```

### ❌ "CORS error" (Vercel → Render)

```
✓ Verificar: CORS_ORIGINS em .env tem Vercel domain?
✓ Formato: https://seu-domain.vercel.app
```

---

## 📝 O Que Falta Implementar (Próximas Fases)

### FASE 2.2: Relatórios (próxima semana)

- [ ] Endpoint `/api/generate-report`
- [ ] Export Excel (formatado)
- [ ] Export HTML (responsivo)
- [ ] Export CSV

### FASE 2.3: Automação (2 semanas)

- [ ] Fila de processamento (threading)
- [ ] Processamento em background
- [ ] Email de notificação

### FASE 2.4: Segurança (3 semanas)

- [ ] Autenticação JWT
- [ ] Multi-tenancy
- [ ] Isolamento de dados

### FASE 2.5: Produção (4 semanas)

- [ ] Testes E2E
- [ ] Performance tuning
- [ ] Backup automático

---

## 🚨 Checklist Deploy Produção

**Local:**

- [ ] `.env` criado com todas as chaves
- [ ] `python api/index.py` funciona
- [ ] Teste PDF via cURL passa
- [ ] Dados aparecem em SQLite

**Render:**

- [ ] Repositório conectado
- [ ] Environment vars setadas
- [ ] Build passou (verifica logs)
- [ ] Health check retorna 200

**Vercel:**

- [ ] Frontend deployado
- [ ] CORS_ORIGINS configurado
- [ ] `REACT_APP_API_URL` aponta para Render

**Integração:**

- [ ] Vercel → Render comunica
- [ ] PDF upload funciona end-to-end
- [ ] Dados salvam no Render (banco)

---

## 📞 Debug Rápido

### Ver logs Render

```
Dashboard → Logs
Mostra tudo que acontece em produção
```

### Ver logs localmente

```bash
python api/index.py
Logs aparecem no terminal em tempo real
```

### Teste direto (cURL)

```bash
# Local
curl -F "file=@teste.pdf" http://localhost:5000/api/analyze-pdf

# Produção (Render)
curl -F "file=@teste.pdf" https://[seu-render-domain].onrender.com/api/analyze-pdf
```

---

## 💾 Backup Database

O banco SQLite está em: `data/historico_riviera.db`

**Para backup:**

```bash
# Copiar arquivo
cp data/historico_riviera.db backup/historico_riviera_$(date +%Y%m%d).db
```

**Render não persiste dados** (Free tier)
→ Considere PostgreSQL se precisar dados permanentes

---

## 🎯 Resumo: Próximos 30 min para Produção

1. ✅ `.env` preenchido com suas chaves (5 min)
2. ✅ Teste local: `python api/index.py` (5 min)
3. ✅ Push para GitHub (1 min)
4. ✅ Deploy Render (10 min, automático)
5. ✅ Deploy Vercel (5 min, automático)
6. ✅ Teste end-to-end (5 min)

**Total: ~30 minutos para estar em produção!**

---

**Status**: 🟢 PRONTO PARA DEPLOY
**Próxima Prioridade**: Fase 2.2 (Relatórios)
**Deadline**: Você define

Qualquer dúvida de config, me avisa!
