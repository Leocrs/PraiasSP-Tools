#!/bin/bash

# Build script para PraiasSP Tools - Riviera Ingestor
# Preparação para deploy no Vercel/Render

echo "🔨 Iniciando build..."

# Criar diretórios necessários
mkdir -p data uploads

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Inicializar banco de dados
echo "🗄️ Inicializando banco de dados..."
python -c "from api.index import init_db; init_db()"

echo "✅ Build concluído com sucesso!"
