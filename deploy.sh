#!/bin/bash

# Deploy script para PraiasSP Tools - Riviera Ingestor
# Deploy automático para Vercel e Render

echo "🚀 Iniciando processo de deploy..."

# Variáveis
VERCEL_DOMAIN="${VERCEL_DOMAIN:-praiassp-tools.vercel.app}"
RENDER_DOMAIN="${RENDER_DOMAIN:-praiassp-tools.onrender.com}"

echo "📍 Verificando configurações..."
echo "   Vercel: $VERCEL_DOMAIN"
echo "   Render: $RENDER_DOMAIN"

# Build
./build.sh

echo "✅ Deploy preparado! Próximos passos:"
echo "   1. Para Vercel: vercel deploy"
echo "   2. Para Render: git push (com webhook configurado)"
echo "   3. Verificar .env.example e configurar variáveis de ambiente"
