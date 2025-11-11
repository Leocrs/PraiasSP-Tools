# Riviera Ingestor - Praias SP Tools

**Assistente de Consolidação de Relatórios Financeiros - Riviera de São Lourenço**

## 📋 Sobre o Projeto

Aplicação web profissional para automatizar o processamento mensal das prestações de contas da **Praias SP / Sobloco** referentes às obras da **Riviera de São Lourenço**, consolidando dados em **Excel** e **HTML** executivos.

### Objetivos Principais

✅ Ler PDFs mensais enviados pela Praias SP (POSIÇÃO FINANC. / DESPESAS)
✅ Extrair despesas por obra, aportes, rentabilidade e saldos
✅ Consolidar em base de dados cumulativa
✅ Gerar relatórios executivos em HTML
✅ Calcular comparativos: Custo Previsto vs Realizado
✅ Rateio automático de aportes (configurável)
✅ Exportar para BI (Power BI, Tableau)

---

## 🏗️ Arquitetura

```
PraiasSP-Tools/
├── api/
│   ├── __init__.py
│   └── index.py                 # API Principal (Flask) - com endpoint /api/analyze-pdf
├── static/
│   ├── styles.css               # Estilos (Identidade Verde Tools)
│   └── app.js                   # Frontend JavaScript
├── templates/
│   └── index.html               # Template HTML
├── data/                        # Banco de dados (ignorado git)
│   └── historico_riviera.db
├── uploads/                     # PDFs temporários (ignorado git)
├── .env.example                 # Template variáveis de ambiente
├── .gitignore                   # Proteção: .env, data/, uploads/
├── requirements.txt             # Dependências Python
├── vercel.json                  # Configuração Vercel (frontend)
├── Procfile                     # Configuração Render (backend)
├── runtime.txt                  # Python 3.11.7
├── gunicorn.conf.py             # Servidor produção
├── DEPLOY.md                    # 🚀 Guia deployment
├── TAREFAS_PENDENTES.md         # 📋 Roadmap
├── STATUS_PRODUCAO.md           # 📊 Status atual
└── README.md                    # Este arquivo
```

---

## 🚀 Quick Start Local

### Pré-requisitos

- Python 3.11+
- Git
- pip/conda

### 1. Clonar Repositório

```bash
git clone https://github.com/Leocrs/PraiasSP-Tools.git
cd PraiasSP-Tools
```

### 2. Criar Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
# Adicionar OPENAI_API_KEY e outras variáveis
```

### 5. Inicializar Banco de Dados

```bash
python -c "from api.index import init_db; init_db()"
```

### 6. Executar Aplicação

```bash
# Desenvolvimento (com debug)
export FLASK_ENV=development
export FLASK_DEBUG=1
python api/index.py

# Ou com Gunicorn (produção)
gunicorn -c gunicorn.conf.py api.index:app
```

**Acesso**: http://localhost:5000

---

## 🤖 Funcionalidades - FASE 2.1 (Nov 11, 2025)

### ✅ Análise Automática de PDFs com OpenAI

**Endpoint**: `POST /api/analyze-pdf`

```bash
curl -F "file=@relatorio.pdf" http://localhost:5000/api/analyze-pdf
```

**Response**:

```json
{
  "status": "success",
  "analysis": {
    "tipo_documento": "Relatório Financeiro",
    "periodo": "2025-11",
    "despesas_totais": 2154037.89,
    "aportes": 850000.0,
    "saldo": 962170.12,
    "obras": ["603 - Ampliação Shopping Riviera"],
    "insights": "Análise realizada por GPT-4o"
  },
  "saved_to_db": true
}
```

**Como funciona**:

1. Extrai texto do PDF com PyPDF2
2. Envia para GPT-4o com prompt especializado
3. Analisa estrutura de dados financeiros
4. Salva resultado em tabela `movimentos` do SQLite
5. Retorna JSON estruturado

---

## 📦 Dependências Principais

| Pacote        | Versão  | Descrição                   |
| ------------- | ------- | --------------------------- |
| Flask         | 2.3.3   | Web framework               |
| flask-cors    | 4.0.0   | CORS para API               |
| OpenAI        | ≥1.40.0 | GPT-4o para análise PDFs    |
| PyPDF2        | 3.0.1   | Extração de texto PDFs      |
| pandas        | ≥2.0.0  | Processamento de dados      |
| openpyxl      | ≥3.10.0 | Geração de Excel (Fase 2.2) |
| gunicorn      | 21.2.0  | WSGI HTTP Server            |
| python-dotenv | 1.0.1   | Variáveis de ambiente       |

---

## 🌍 Próximos Passos

### 🚀 Deploy em Produção

→ Leia **`DEPLOY.md`** para deploy em Vercel + Render

### 📋 Roadmap de Desenvolvimento

→ Leia **`TAREFAS_PENDENTES.md`** para fases 2.2-2.5

### 📊 Status Atual

→ Leia **`STATUS_PRODUCAO.md`** para checklist deployment

### 🔐 Segurança

→ Leia **`SECURITY.md`** para boas práticas

---

## 🔐 Segurança & Variáveis de Ambiente

---

## 🗄️ Estrutura de Dados

### Tabelas SQLite

#### `movimentos`

```sql
CREATE TABLE movimentos (
    id INTEGER PRIMARY KEY,
    competencia TEXT,              -- YYYY-MM
    codigo_obra TEXT,              -- 603, 616, etc
    obra_nome TEXT,                -- Nome da obra
    tipo TEXT,                     -- Despesa, Aporte_Rateado, etc
    valor REAL,
    fonte TEXT,
    data_insercao DATETIME
)
```

#### `orcamento_previsto`

```sql
CREATE TABLE orcamento_previsto (
    id INTEGER PRIMARY KEY,
    codigo_obra TEXT UNIQUE,
    obra_nome TEXT,
    custo_previsto REAL,
    data_atualizacao DATETIME
)
```

#### `configuracoes`

```sql
CREATE TABLE configuracoes (
    id INTEGER PRIMARY KEY,
    chave TEXT UNIQUE,             -- Ex: 'metodo_rateio_aporte'
    valor TEXT,
    data_atualizacao DATETIME
)
```

---

## 🔌 API Endpoints

### Health Check

```
GET /health
→ { "status": "ok", "service": "Riviera Ingestor" }
```

### Movimentos Financeiros

```
GET /api/movimentos?competencia=2025-09&codigo_obra=603
→ { "status": "success", "count": 10, "data": [...] }
```

### Resumo Consolidado

```
GET /api/resumo
→ {
    "status": "success",
    "resumo": {
        "obras": [...],
        "totais": { "despesas_totais": ..., "aportes_rateados": ... }
    }
}
```

### Upload de PDFs

```
POST /api/upload
Content-Type: multipart/form-data
Files: [SHOPP_..._POSIÇÃO_FINANC.pdf, ...]
→ { "status": "success", "processados": 3, "total": 3 }
```

### Configurações

```
GET /api/configuracoes
POST /api/configuracoes
Body: { "metodo_rateio_aporte": "proporcional_despesa_mes" }
```

### Orçamento Previsto

```
GET /api/orcamento
POST /api/orcamento
Body: [{ "codigo_obra": "603", "custo_previsto": 20000000 }, ...]
```

---

## 📤 Upload de PDFs

### Padrão de Nomes de Arquivo

A aplicação reconhece automaticamente:

```
SHOPP 562 601 603 e 604 POSIÇÃO FINANC SETEMBRO 2025.pdf
SHOPP 562 601 603 e 604 DESPESAS SETEMBRO 2025.pdf
OBRA 616 BCO 435 POSIÇÃO FINANC SETEMBRO 2025.pdf
```

### Competências Suportadas

- Formato: `YYYY-MM`
- Detectadas automaticamente do nome do arquivo
- Exemplos: `2025-09`, `2025-08`

---

## 🎨 Identidade Visual

A aplicação usa a paleta de cores **verde** da Tools:

```css
--color-primary: #1a7d4d       /* Verde principal */
--color-primary-light: #2d9b6a  /* Verde claro */
--color-primary-dark: #0f5a3a   /* Verde escuro */
--color-accent: #45b88f         /* Verde acentuação */
```

### Componentes

- ✅ Logo verde responsiva
- ✅ Gradient backgrounds
- ✅ Cards com border verde
- ✅ Buttons com hover effects
- ✅ Tabelas com header verde
- ✅ Mobile-first responsive design

---

## 🔐 Segurança & Variáveis de Ambiente

### Arquivo `.env` (NUNCA commitar!)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxx

# Flask
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta

# Database
DATABASE_PATH=./data/historico_riviera.db

# Upload
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=52428800  # 50MB

# CORS
CORS_ORIGINS=https://yourdomain.com

# Server
PORT=5000
```

### `.gitignore` Configurado Para:

- ✅ `.env` e variáveis sensíveis
- ✅ `__pycache__` e `.pyc`
- ✅ `*.db` e banco de dados
- ✅ `uploads/` e PDFs
- ✅ Arquivos Excel/HTML gerados
- ✅ `.venv` e ambientes virtuais

---

## 🌍 Deploy

### Vercel (Recomendado para Frontend)

```bash
# Instalar CLI
npm install -g vercel

# Deploy
vercel deploy

# Variáveis de ambiente
vercel env add OPENAI_API_KEY
```

**Arquivo**: `vercel.json` já configurado

### Render (Recomendado para Backend)

```bash
# Conectar repositório
# 1. Ir para https://dashboard.render.com
# 2. Criar novo "Web Service"
# 3. Conectar repositório GitHub
# 4. Build command: ./build.sh
# 5. Start command: gunicorn -c gunicorn.conf.py api.index:app
```

**Arquivo**: `Procfile` já configurado

### Variáveis de Ambiente no Render/Vercel

```
OPENAI_API_KEY=sk-proj-xxxxx
FLASK_ENV=production
DATABASE_PATH=/tmp/historico_riviera.db
UPLOAD_FOLDER=/tmp/uploads
```

---

## 📊 Funcionalidades

### Dashboard

- Cards de métricas (Despesas, Aportes, Rentabilidade, Saldo)
- Tabela de resumo por obra
- Auto-refresh a cada 5 minutos

### Upload

- Múltiplos arquivos PDF
- Detecção automática de competência
- Validação de tamanho e formato
- Feedback em tempo real

### Movimentos

- Filtro por competência e obra
- Histórico completo de transações
- Busca rápida e intuitiva

### Orçamento Previsto

- Comparativo Previsto vs Realizado
- Cálculo automático de % realizado
- Desvio em reais
- Status (em andamento, dentro, acima)

### Relatórios

- Geração em HTML
- Exportação Excel
- CSV para BI
- Agendamento futuro

---

## 🤖 GPT / Assistente IA

### Prompt Padrão

```
Você é o Assistente Riviera Ingestor, responsável por processar
os relatórios financeiros mensais das obras da Riviera de São
Lourenço, enviados pela Praias SP e executados pela Sobloco.

Quando eu fizer upload de PDFs mensais (POSIÇÃO FINANC. e DESPESAS):
1. Leia todos os arquivos
2. Extraia despesas por obra, aportes, rentabilidade e saldo
3. Gere automaticamente:
   - Um arquivo Excel consolidado com base acumulada
   - Um relatório HTML com cards e tabelas executivas
4. Mantenha a estrutura e nomenclaturas do modelo padrão
5. Apresente os links de download dos arquivos
```

### Configuração no ChatGPT Plus

1. Ir para https://chatgpt.com/gpts/mine
2. Criar novo GPT personalizado
3. Copiar nome: "Riviera Ingestor - Praias SP"
4. Colar prompt acima
5. Fazer upload do arquivo: `Riviera_Consolidado_Base.xlsx`
6. Adicionar instruções personalizadas

---

## 📈 Próximas Implementações

- [ ] Integração com Google Drive para buscar PDFs automaticamente
- [ ] Alertas automáticos (desvio > 10%)
- [ ] Agendamento de relatórios (envio por email)
- [ ] Integração Power BI nativa
- [ ] Autenticação de usuários
- [ ] Multi-tenancy (múltiplos projetos)
- [ ] Webhook para Slack/Teams
- [ ] API de terceiros (análise OCR)

---

## 🐛 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'flask'`

```bash
pip install -r requirements.txt
```

### Erro: `OPENAI_API_KEY not found`

```bash
# Verificar .env
cat .env
# Recriar se necessário
cp .env.example .env
# Editar com suas chaves
```

### Erro: `Database locked`

```bash
# Aguardar ou reiniciar aplicação
# SQLite tem limite de conexões simultâneas
```

### Porta já em uso

```bash
# Mudar porta
export PORT=5001
python api/index.py
```

---

## 📞 Suporte

- 📧 Email: dev@tools.com.br
- 💬 Slack: #riviera-ingestor
- 📚 Documentação: `/docs`
- 🐛 Issues: GitHub Issues

---

## 📄 Licença

© 2025 **Tools Engenharia**. Todos os direitos reservados.

---

## 👥 Colaboradores

- **Leonardo** - Desenvolvedor Principal
- **CEO Praias SP** - Requisitos & Validação
- **Sobloco** - Gestão de Obras

---

## 🎯 Roadmap

### Q4 2025

- [ ] v1.0 - Versão inicial
- [ ] Deployment Vercel/Render
- [ ] Primeira integração com dados reais

### Q1 2026

- [ ] v1.1 - OCR aprimorado
- [ ] Alertas automáticos
- [ ] BI nativo

### Q2 2026

- [ ] v2.0 - Multi-tenancy
- [ ] Autenticação
- [ ] Dashboard avançado

---

## ✨ Desenvolvido com

```
╔═══════════════════════════════════╗
║   🟢 TOOLS ENGENHARIA             ║
║   Riviera Ingestor v1.0.0         ║
║   © 2025                          ║
╚═══════════════════════════════════╝
```

**Créditos**: Desenvolvido com ❤️ para Praias SP / Sobloco

---

**Última atualização**: 9 de Novembro de 2025
