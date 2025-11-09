# 🔐 Guia de Segurança - Riviera Ingestor

## ⚠️ Informações Sensíveis

Esta aplicação lida com dados financeiros sensíveis da Praias SP / Sobloco. Siga rigorosamente as práticas abaixo.

---

## 🚫 NUNCA COMMITAR ESTES ARQUIVOS

```
.env                           # Chaves API e senhas
.env.local
.env.production
*.db (arquivos de banco)
uploads/                       # PDFs enviados
data/historico_riviera.db
```

**Verificar antes de cada push:**

```bash
git status
# Confirmar que nenhum arquivo sensível está staged
```

---

## 🔑 Gestão de Chaves API

### OpenAI API Key

**ONDE OBTER:**

1. Ir para https://platform.openai.com/api-keys
2. Criar nova chave (prefixar com `sk-proj-`)
3. Copiar imediatamente (não será exibida novamente)

**ONDE USAR:**

```bash
# .env local
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Variável de ambiente em produção
export OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

**⚠️ IMPORTANTE:**

- Nunca hardcode no código
- Nunca commitar chaves no Git
- Rotacionar chaves mensalmente
- Revogar imediatamente se expostas

### Chaves no Vercel/Render

**Vercel:**

```bash
vercel env add OPENAI_API_KEY
# Cole a chave (não aparece na tela)
```

**Render:**

1. Dashboard → Projeto
2. Environment → Add Secret
3. Nome: `OPENAI_API_KEY`
4. Valor: sua chave

---

## 🔒 Proteção de Dados

### Banco de Dados

```python
# ✅ SEGURO - Usar context manager
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(db_path, timeout=10)
    try:
        yield conn
    finally:
        conn.close()

# ✅ USO
with get_db_connection() as conn:
    # Sua lógica aqui
    pass
```

### PDFs Uploadados

```
uploads/                       # Pasta temporária
├── 20250909_180530_SHOPP_..._POSIÇÃO.pdf
├── 20250909_180531_SHOPP_..._DESPESAS.pdf
└── ...

# Limpeza automática após processamento
# Tempo de retenção: 7 dias máximo
```

### Criptografia (Futuro)

```python
# TODO: Implementar para dados sensíveis
from cryptography.fernet import Fernet

cipher = Fernet(encryption_key)
encrypted_data = cipher.encrypt(sensitive_data)
```

---

## 🛡️ CORS & Headers

```python
# ✅ CORS apenas para domínios autorizados
CORS(app, origins=[
    "https://praiassp.com",
    "https://sobloco.com",
])

# ✅ Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

## 🔍 Validação de Entrada

### PDFs Upload

```python
# ✅ Validar tipo
if not filename.endswith('.pdf'):
    return error("Apenas PDFs")

# ✅ Validar tamanho
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
if file.size > MAX_FILE_SIZE:
    return error("Arquivo muito grande")

# ✅ Sanitizar nome
import os
filename = os.path.basename(filename)  # Remove paths
```

### Parâmetros API

```python
# ✅ Validar competência
import re
competencia = request.args.get('competencia')
if not re.match(r'\d{4}-\d{2}', competencia):
    return error("Formato inválido: YYYY-MM")

# ✅ SQL Injection Prevention (com Parameterized Queries)
cursor.execute(
    'SELECT * FROM movimentos WHERE codigo_obra = ?',
    (codigo_obra,)  # ✅ Seguro, não string formatting
)
```

---

## 📊 Auditoria & Logs

### Log de Acesso

```python
# logs/access.log
[2025-09-09 18:05:30] POST /api/upload - user_id=123 - 200 OK
[2025-09-09 18:06:15] GET /api/resumo - user_id=123 - 200 OK
```

### Log de Erros

```python
# logs/error.log
[2025-09-09 18:07:45] ERROR - OPENAI_API_KEY not found
[2025-09-09 18:08:20] ERROR - Database connection timeout
```

### Rastreamento de Mudanças

```sql
-- Tabela de auditoria (TODO)
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY,
    usuario TEXT,
    acao TEXT,           -- INSERT, UPDATE, DELETE
    tabela TEXT,
    dados_antigos JSON,
    dados_novos JSON,
    data_acao DATETIME,
    ip TEXT
)
```

---

## 🔑 Autenticação Futura

```python
# TODO: Implementar JWT para API
from flask_jwt_extended import JWTManager

jwt = JWTManager(app)

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # Validar
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@app.route('/api/movimentos', methods=['GET'])
@jwt_required()
def get_movimentos():
    current_user = get_jwt_identity()
    # Retornar apenas dados do usuário
    pass
```

---

## 🌐 HTTPS & TLS

### Em Produção

```bash
# ✅ Vercel (automático)
# ✅ Render (automático)

# ✅ Local (teste)
pip install pyopenssl
# Gerar certificado auto-assinado
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Usar em Flask
app.run(ssl_context=('cert.pem', 'key.pem'))
```

---

## 🚨 Incidentes de Segurança

### Se chave API foi exposta:

1. ✅ Revogue imediatamente em https://platform.openai.com/account/api-keys
2. ✅ Criar nova chave
3. ✅ Atualizar em Vercel/Render
4. ✅ Redeploy automático
5. ✅ Notificar CEO

### Procedimento:

```bash
# 1. Revogar chave antiga
# (via dashboard OpenAI)

# 2. Criar nova
NEW_KEY=$(curl -X POST https://api.openai.com/v1/api_keys \
  -H "Authorization: Bearer $ADMIN_KEY" \
  | jq -r '.key')

# 3. Atualizar ambiente
vercel env remove OPENAI_API_KEY
vercel env add OPENAI_API_KEY
# (colar nova chave)

# 4. Redeploy
vercel deploy --prod
```

---

## 📋 Checklist de Deploy

Antes de fazer deploy, verificar:

- [ ] `.env` não está em `.gitignore` e ainda está rastreado?

  ```bash
  git status
  ```

- [ ] Todas as variáveis sensíveis estão em `.env.example` sem valores?

  ```bash
  grep -i "key\|password\|token" .env.example
  ```

- [ ] Arquivo `requirements.txt` está atualizado?

  ```bash
  pip freeze | grep -E "flask|pandas|openpyxl" > requirements.txt
  ```

- [ ] Banco de dados não está commitado?

  ```bash
  ls -la data/
  ```

- [ ] `.gitignore` cobre todos os sensíveis?
  ```bash
  cat .gitignore
  ```

---

## 🔗 Referências de Segurança

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/security/)
- [Python Secrets](https://docs.python.org/3/library/secrets.html)
- [OpenAI Security](https://platform.openai.com/docs/guides/production-best-practices)

---

## 📞 Reportar Vulnerabilidades

Se encontrar uma vulnerabilidade:

1. **NÃO** abra issue pública
2. Envie email: security@tools.com.br
3. Aguarde resposta em 48 horas
4. Coordene divulgação responsável

---

## ✅ Confirmação

Ao trabalhar com este projeto, você confirma:

- [ ] Compreendi os riscos de dados sensíveis
- [ ] Nunca vou commitar `.env` ou chaves API
- [ ] Vou usar as boas práticas de validação
- [ ] Vou reportar vulnerabilidades responsavelmente
- [ ] Vou rotacionar chaves regularmente

---

**Versão**: 1.0.0  
**Última atualização**: 9 de Novembro de 2025  
**Status**: ✅ Ativo
