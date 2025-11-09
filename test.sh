#!/bin/bash
# Script de testes para Riviera Ingestor

echo "🧪 Testando Riviera Ingestor..."
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ================================
# 1. VERIFICAÇÃO DE DEPENDÊNCIAS
# ================================

echo -e "${YELLOW}📦 Verificando dependências...${NC}"

# Verificar Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python instalado: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 não encontrado${NC}"
    exit 1
fi

# Verificar pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip instalado${NC}"
else
    echo -e "${RED}✗ pip não encontrado${NC}"
    exit 1
fi

# ================================
# 2. VERIFICAÇÃO DE ESTRUTURA
# ================================

echo ""
echo -e "${YELLOW}📁 Verificando estrutura de pastas...${NC}"

required_dirs=("api" "static" "templates" "data")

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ Pasta '$dir' existe${NC}"
    else
        echo -e "${RED}✗ Pasta '$dir' não encontrada${NC}"
        mkdir -p "$dir"
        echo -e "${YELLOW}  Criada automaticamente${NC}"
    fi
done

# ================================
# 3. VERIFICAÇÃO DE ARQUIVOS
# ================================

echo ""
echo -e "${YELLOW}📄 Verificando arquivos principais...${NC}"

required_files=(
    "api/index.py"
    "api/__init__.py"
    "static/styles.css"
    "static/app.js"
    "templates/index.html"
    ".gitignore"
    "requirements.txt"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ Arquivo '$file' encontrado${NC}"
    else
        echo -e "${RED}✗ Arquivo '$file' não encontrado${NC}"
    fi
done

# ================================
# 4. TESTE DE BANCO DE DADOS
# ================================

echo ""
echo -e "${YELLOW}🗄️ Testando banco de dados...${NC}"

python3 << EOF
import sqlite3
import sys
import os

try:
    db_path = './data/historico_riviera.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar tabelas
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = cursor.fetchall()
    
    if tables:
        print(f"\033[92m✓ Banco de dados com {len(tables)} tabelas:\033[0m")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("\033[93m⚠ Nenhuma tabela encontrada - inicializando...\033[0m")
        from api.index import init_db
        init_db()
        print("\033[92m✓ Banco inicializado\033[0m")
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"\033[91m✗ Erro: {e}\033[0m")
    sys.exit(1)
EOF

# ================================
# 5. TESTE DE CONFIGURAÇÃO
# ================================

echo ""
echo -e "${YELLOW}⚙️ Verificando configurações...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Arquivo .env encontrado${NC}"
    
    # Verificar OPENAI_API_KEY
    if grep -q "OPENAI_API_KEY" .env; then
        if grep -q "OPENAI_API_KEY=sk-" .env; then
            echo -e "${GREEN}✓ OPENAI_API_KEY configurada${NC}"
        else
            echo -e "${YELLOW}⚠ OPENAI_API_KEY vazia ou inválida${NC}"
        fi
    else
        echo -e "${RED}✗ OPENAI_API_KEY não encontrada em .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Arquivo .env não encontrado${NC}"
    echo "   Execute: cp .env.example .env"
fi

# ================================
# 6. TESTE DE IMPORTS
# ================================

echo ""
echo -e "${YELLOW}🔌 Testando imports Python...${NC}"

python3 << EOF
import sys

modules_to_test = [
    'flask',
    'flask_cors',
    'sqlite3',
    'pandas',
    'openpyxl',
]

missing = []

for module in modules_to_test:
    try:
        __import__(module)
        print(f"\033[92m✓ {module} importado com sucesso\033[0m")
    except ImportError:
        print(f"\033[91m✗ {module} não encontrado\033[0m")
        missing.append(module)

if missing:
    print(f"\n\033[93mPacotes faltando: {', '.join(missing)}\033[0m")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\033[92m✓ Todos os módulos importados com sucesso\033[0m")
    sys.exit(0)
EOF

TEST_IMPORTS=$?

# ================================
# 7. TESTE DE API
# ================================

echo ""
echo -e "${YELLOW}🚀 Testando API...${NC}"

python3 << EOF
import sys
sys.path.insert(0, '.')

try:
    from api.index import app
    print("\033[92m✓ Aplicação Flask importada com sucesso\033[0m")
    
    # Testar com cliente de teste
    client = app.test_client()
    
    # Health check
    response = client.get('/health')
    if response.status_code == 200:
        print("\033[92m✓ Endpoint /health respondendo (200 OK)\033[0m")
    else:
        print(f"\033[91m✗ Endpoint /health retornou {response.status_code}\033[0m")
    
    # API endpoints
    response = client.get('/api/resumo')
    if response.status_code == 200:
        print("\033[92m✓ Endpoint /api/resumo respondendo (200 OK)\033[0m")
    else:
        print(f"\033[91m✗ Endpoint /api/resumo retornou {response.status_code}\033[0m")
    
    sys.exit(0)
except Exception as e:
    print(f"\033[91m✗ Erro ao testar API: {e}\033[0m")
    sys.exit(1)
EOF

TEST_API=$?

# ================================
# 8. VERIFICAÇÃO FINAL
# ================================

echo ""
echo -e "${YELLOW}📋 Resumo dos Testes${NC}"
echo ""

if [ $TEST_IMPORTS -eq 0 ] && [ $TEST_API -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ TODOS OS TESTES PASSOU!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Próximos passos:${NC}"
    echo "1. Executar: python api/index.py"
    echo "2. Acessar: http://localhost:5000"
    echo "3. Fazer upload de PDFs para testar"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ ALGUNS TESTES FALHARAM${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Corrija os problemas acima e tente novamente.${NC}"
    exit 1
fi
