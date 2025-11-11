# 📋 ROADMAP PRODUÇÃO - O Que Falta Implementar

Data: 11 Nov 2025
Status: **PRODUÇÃO ATIVA (Fase 2.1 ✅)**

---

## ✅ IMEDIATO (Deploys e Testes)

- [x] Preencher `.env` com chaves reais (OpenAI, Render, Vercel)
- [x] Push para GitHub
- [x] Deploy Render (backend)
- [x] Deploy Vercel (frontend)
- [x] Teste end-to-end: Vercel → Render → OpenAI → SQLite
- [x] Upload PDF real via frontend
- [x] Validação de análise e banco

---

## 📊 PRÓXIMA SEMANA (Fase 2.2)

- [ ] Relatórios em Excel/HTML/CSV
  - Endpoint `/api/generate-report` (POST)
  - Parâmetros: `format` (excel|html|csv), `filters` (competência, obra)
  - Gerar Excel com formatação (pandas + openpyxl)
  - Gerar HTML responsivo (Jinja2)
  - Gerar CSV para integração
  - Testes com dados reais
  - Botão frontend para relatórios
  - Integração e download automático

---

## 🤖 PRÓXIMAS 2 SEMANAS (Fase 2.3)

- [ ] Automação com processamento em background
  - Tabela `analises_pendentes` (status, timestamp, erro)
  - Fila de PDFs com `threading.Queue`
  - Worker thread para processar em background
- [ ] Endpoint `/api/status/{id}` para verificar progresso
- [ ] Webhook/Email de notificação (opcional inicialmente)
- **Tempo**: ~10-15h
- **Arquivo**: `api/index.py` (adicionar ~200 linhas) + `api/worker.py` (novo)

---

## 🔐 PRÓXIMAS 3 SEMANAS (Fase 2.4)

### [ ] 6. Autenticação & Multi-tenancy

- [ ] Criar tabelas: `usuarios`, `organizacoes`, `tokens_revogados`
- [ ] Endpoint `/api/auth/login` (JWT)
- [ ] Endpoint `/api/auth/logout`
- [ ] Middleware `@jwt_required()` em todos endpoints
- [ ] Isolamento de dados: usuário vê apenas seus dados
- [ ] Suporte a múltiplas obras por organização
- **Tempo**: ~12-15h
- **Arquivo**: `api/index.py` + `api/auth.py` (novo)

---

## 🧪 PRÓXIMAS 4 SEMANAS (Fase 2.5)

### [ ] 7. Testes & Otimizações

- [ ] Testes E2E com PDFs reais (Mac Vidros, Marvidros, etc)
- [ ] Performance test (1000+ movimentos)
- [ ] Teste de segurança (SQL injection, XSS)
- [ ] Backup automático do banco
- [ ] Monitoramento de errors (Sentry ou similar)
- **Tempo**: ~10-12h

---

## 🚨 CRÍTICO (Anytime)

### [ ] 8. Bugs/Fixes Descobertos

- Listar aqui conforme descobrir na produção
- Priorizar por impacto × urgência

---

## 📊 Progresso Geral

```
FASE 1: MVP Base                    ✅ 100%
FASE 2.1: OpenAI Integration        ✅ 100%
FASE 2.2: Relatórios               📅 Próxima semana
FASE 2.3: Automação                📅 Próximas 2 semanas
FASE 2.4: Segurança/Auth           📅 Próximas 3 semanas
FASE 2.5: Testes & Otimizações     📅 Próximas 4 semanas
```

---

## 💼 Estimativa Total

| Fase      | Horas         | Data Estimada |
| --------- | ------------- | ------------- |
| 2.1       | ✅ 0 (pronto) | ✅ Nov 11     |
| 2.2       | 10-15h        | Nov 18        |
| 2.3       | 12-18h        | Nov 25        |
| 2.4       | 12-18h        | Dec 2         |
| 2.5       | 10-12h        | Dec 9         |
| **Total** | **44-63h**    | **~1 mês**    |

---

## 🔗 Dependências Entre Tarefas

```
Deploy Produção (imediato)
    ↓
Fase 2.2 (Relatórios) ← requer dados em produção
    ↓
Fase 2.3 (Automação) ← requer relatórios prontos
    ↓
Fase 2.4 (Auth) ← pode ser paralelo
    ↓
Fase 2.5 (Testes)
```

---

## 📌 Notas Importantes

1. **Banco SQLite em Render (Free tier)**

   - ⚠️ Dados não persistem após redeploy
   - Solução: Migrar para PostgreSQL se precisar dados permanentes

2. **OpenAI Costs**

   - GPT-4o: ~$0.01-0.02 por request
   - Estimativa: ~$5-20/mês com uso normal
   - Defina limites de taxa no Render

3. **Vercel + Render (Free tiers)**
   - Vercel: 100GB bandwidth/mês (suficiente)
   - Render: 750h/mês (suficiente para aplicação leve)
   - Upgrade se precisar de mais

---

## ✅ Checklist Pre-Deployment

- [ ] `.env` preenchido com chaves reais
- [ ] `api/index.py` testado localmente
- [ ] SQLite tem dados de teste
- [ ] Vercel domain configurado
- [ ] Render domain configurado
- [ ] CORS_ORIGINS atualizado em `.env`
- [ ] `requirements.txt` tem todas dependências
- [ ] `gunicorn.conf.py` está correto
- [ ] `Procfile` aponta para arquivo certo
- [ ] `runtime.txt` com Python 3.11

---

**Próximo Passo**: Execute as tarefas de "IMEDIATO" para ter em produção hoje!

Qualquer bloqueador, me avisa! 🚀
