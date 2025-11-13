# 📋 ROADMAP DETALHADO - RIVIERA (17 Nov - 1 Dez / 3 Semanas)

**Período**: Segunda 17 Nov → Domingo 1 Dez 2025 (21 dias)  
**Projeto**: Automatização de Prestações de Contas - Riviera de São Lourenço  
**Status**: Sistema 60% pronto, faltam outputs e consolidação

---

## 🎯 VISÃO GERAL

| Semana                   | Foco                  | Horas   | Status     |
| ------------------------ | --------------------- | ------- | ---------- |
| **Semana 1** (17-23 Nov) | Validação + Excel     | 25h     | 📅 Próximo |
| **Semana 2** (24-30 Nov) | HTML + Consolidação   | 28h     | 📅 Próximo |
| **Semana 3** (1 Dez)     | Testes + Refinamentos | 15h     | 📅 Próximo |
| **TOTAL**                | -                     | **68h** | -          |

---

## 📋 TAREFAS DETALHADAS

### SEMANA 1: VALIDAÇÃO + EXCEL (17-23 Nov) - 25h

#### Dia 1-2 (Segunda-Terça) - VALIDAÇÃO DO RATEIO (4h)

**O que**: Confirmar que rateio de aportes funciona corretamente em produção

**Tarefas técnicas**:

- Deploy commit atual em Render
- Testar com 3 PDFs reais (Praias SP) via Vercel
- Verificar logs Render: "DEBUG: aportes_pool found"
- Se funciona: avançar. Se não: debug de 2-3h

**Entregável**: Confirmação que JSON retorna 6 campos de rateio

**Notas técnicas que o usuário não entendeu**:

- GPT-5 pode não retornar JSON estruturado se prompt não for claro
- Debug logging está no código (linhas 925-960) para verificar presença
- Se falhar, pode ser limitação do modelo ou parsing JSON

---

#### Dia 2-5 (Terça-Sexta) - GERAR EXCEL CONSOLIDADO (10h)

**O que**: Criar endpoint que retorna `Riviera_Consolidado_Base.xlsx` pronto para download

**Tarefas técnicas**:

1. **Criar função generate_excel_report()** (3h)

   - Usar openpyxl (já em requirements.txt)
   - Aba 1: `base_movimentos` - todos os movimentos extraídos
     - Colunas: competencia, obra, tipo (saldo/despesa/aporte), valor, data
   - Aba 2: `consolidado_resumo` - agregado por obra
     - Colunas: Obra, Saldo Final, Total Despesas, Total Aportes, Rentabilidade %
   - Aba 3: `orcamento_previsto` - dados da tabela orcamento_previsto do BD
     - Colunas: Obra, Orçamento Previsto, % Gasto
   - Aba 4: `custo_vs_previsto` - comparativo
     - Colunas: Obra, Orçado, Realizado, Desvio, Desvio %
   - Formatação: cabeçalhos com cor, bordas, alinhamento
   - Somas automáticas nas linhas finais

2. **Criar endpoint POST /api/export-excel** (2h)

   - Recebe parâmetros: competencia (Ex: "2024-11"), obras (lista ou all)
   - Chama generate_excel_report()
   - Retorna arquivo .xlsx com headers corretos para download

3. **Adicionar botão Download no frontend** (2h)

   - HTML: botão "Download Excel"
   - JavaScript: POST para /api/export-excel
   - Captura arquivo e faz download automático

4. **Testar com 3 PDFs** (3h)
   - Fazer upload
   - Clicar botão Download
   - Verificar Excel gerado
   - Validar formatação e dados

**Detalhes técnicos (o usuário pode não saber)**:

- openpyxl permite criar abas, formatação, somas com formulas
- response com `mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'` faz download
- Importante: converter Decimal do SQLite para float antes de openpyxl

**Entregável**: Arquivo .xlsx formatado pronto para entregar

---

#### Dia 5-7 (Sexta-Domingo) - CONSOLIDAÇÃO CUMULATIVA NO EXCEL (7h)

**O que**: Excel não é só do mês, mas histórico acumulado (tipo SIM_PLUS)

**Tarefas técnicas**:

- Revisar modelo `Riviera_Consolidado_Base_SIM_PLUS.xlsx` existente
- Modificar função generate_excel_report():
  - base_movimentos deve ter TODOS os movimentos históricos (não só do mês)
  - consolidado_resumo: saldos são FINAIS acumulados
  - custo_vs_previsto: comparar acumulado vs orçamento total
- Implementar lógica de "mês de referência" vs "histórico"
- Atualizar documentação no código

**Detalhes técnicos**:

- SQLite tem competencia em movimentos, usar para filtrar período
- Se competencia = NULL, considerar como histórico completo
- Estrutura de pasta: uploads/relatorios/Riviera_Consolidado_Base_YYYY-MM.xlsx

**Entregável**: Excel com histórico cumulativo funcionando

---

#### Dia 7-8 (Domingo-Segunda) - INTERFACE DE PARÂMETROS (4h)

**O que**: Dashboard com formulário para ajustar configurações

**Tarefas**:

- Criar form HTML simples:
  - Campo: Modelo IA (dropdown: GPT-4o / GPT-5)
  - Campo: max_tokens (número, 1000-12000)
  - Campo: Taxa rateio padrão (se não proporcional)
  - Campo: Obras ativas (checkboxes)
- Salvar em SQLite tabela configuracoes
- Carregar configurações ao iniciar

**Detalhes**:

- Backend: GET /api/configuracoes, POST /api/configuracoes
- Validar valores antes de salvar
- Aplicar na próxima análise

**Entregável**: Formulário funcional no dashboard

---

### SEMANA 2: HTML EXECUTIVO + CONSOLIDAÇÃO (24-30 Nov) - 28h

#### Dia 1-3 (Seg-Qua) - GERAR HTML EXECUTIVO (12h)

**O que**: Criar relatório profissional `Riviera_Relatorio_YYYY-MM.html` pronto para imprimir

**Tarefas técnicas**:

1. **Criar template HTML profissional** (5h)

   - Cabeçalho: Logo, mês/período, data geração
   - Seção 1: Cards resumo
     - Card Verde: "Saldo Total" (número grande)
     - Card Azul: "Despesas Total" (número grande)
     - Card Laranja: "Aportes Total" (número grande)
   - Seção 2: Tabela detalhada obra a obra
     - Obra | Saldo | Despesa | Aporte | Rateio (%) | Rentabilidade
   - Seção 3: Gráfico ou destaque de desvios
     - Se alguma obra tem desvio > 10%, destacar em vermelho
   - Rodapé: Data, assinado por, data processamento
   - Responsivo: quebra bem em A4 para imprimir

2. **Criar função generate_html_report()** (4h)

   - Ler dados do BD
   - Montar string HTML com dados dinâmicos
   - Retornar HTML completo

3. **Criar endpoint POST /api/export-html** (2h)

   - Recebe parâmetros: competencia
   - Chama generate_html_report()
   - Retorna arquivo .html para download
   - Salva em pasta uploads/relatorios/

4. **Adicionar botão Download HTML no frontend** (1h)
   - Similar ao Excel

**Detalhes técnicos**:

- Usar template string ou Jinja2 para gerar HTML
- CSS inline para garantir funcionamento em qualquer navegador
- Media query @print para formato A4
- Cores: Verde (#2ecc71), Azul (#3498db), Laranja (#f39c12), Vermelho (#e74c3c)

**Entregável**: HTML executivo pronto para imprimir

---

#### Dia 3-5 (Qua-Sexta) - MELHORAR VISUAL DO DASHBOARD (10h)

**O que**: Dashboard deixou de ser tabelas simples e virou executivo

**Tarefas técnicas**:

1. **Refazer layout frontend** (5h)

   - Remover tabelas simples
   - Adicionar 4 cards grandes no topo:
     - Card 1: Saldo Total (verde)
     - Card 2: Despesas Mês (azul)
     - Card 3: Aportes (laranja)
     - Card 4: Desvios (vermelho se > 10%)
   - Adicionar mini gráfico ou visual de distribuição
   - Layout: CSS Grid ou Flexbox, responsivo

2. **Adicionar gráfico (opcional mas recomendado)** (3h)

   - Usar Chart.js (leve, sem dependências pesadas)
   - Gráfico de pizza: distribuição de aportes por obra
   - Gráfico de barras: saldo x despesa x aporte

3. **Testar responsividade** (2h)
   - Desktop, tablet, mobile
   - Imprimir em A4

**Detalhes técnicos**:

- CSS modern: Grid + Flexbox
- Chart.js: npm install chart.js (ou CDN)
- Cuidado: tabelas muito longas ficam ruins em mobile

**Entregável**: Dashboard que parece "relatório executivo"

---

#### Dia 5-7 (Sexta-Domingo) - MIGRAR PARA POSTGRESQL (6h)

**O que**: Dados persistem em nuvem, não se perdem em redeploy

**Tarefas técnicas**:

1. **Criar BD PostgreSQL no Render** (1h)

   - Render Dashboard → Create Resource → Database
   - Criar database, user, password
   - Copiar connection string

2. **Atualizar código para PostgreSQL** (2h)

   - Trocar `sqlite3` por `psycopg2` (já em requirements.txt)
   - Atualizar todas as queries (SQL é similar)
   - Atualizar `init_db()` para PostgreSQL
   - Testar conexão

3. **Migrar dados SQLite → PostgreSQL** (2h)

   - Exportar dados do SQLite
   - Importar em PostgreSQL
   - Verificar integridade

4. **Deploy e testar persistência** (1h)
   - Deploy em Render
   - Redeploy novamente
   - Verificar que dados continuam lá

**Detalhes técnicos**:

- psycopg2 é o driver Python para PostgreSQL
- Connection string: postgresql://user:pass@host/database
- Estrutura SQL é praticamente idêntica

**Entregável**: Histórico persistente em nuvem

---

### SEMANA 3: TESTES + REFINAMENTOS (1-3 Dez) - 15h

#### Dia 1-2 (Domingo-Segunda) - TESTES E2E (8h)

**O que**: Sistema funcionando do início ao fim com dados reais

**Tarefas**:

- Preparar 10 PDFs diferentes (Praias SP reais ou simulados)
- Fazer upload sequencial
- Verificar:
  - JSON extraído está correto
  - Rateio calculado está correto
  - Excel consolidado tem todos os dados
  - HTML executivo tem formatação
  - Histórico acumulado
  - Desvios detectados corretamente
- Tomar nota de bugs
- Documentar tempo de processamento

**Detalhes**:

- Testar com diferentes tipos de PDF (POSIÇÃO FINANC + DESPESAS)
- Testar com múltiplos uploads do mesmo período (deve consolidar)
- Testar com períodos diferentes (deve manter histórico)

**Entregável**: Relatório de testes com bugs encontrados

---

#### Dia 2-4 (Segunda-Quarta) - BUGS + REFINAMENTOS (7h)

**O que**: Corrigir tudo que não funcionou nos testes

**Tarefas**:

- Listar bugs do relatório anterior
- Priorizar: críticos (bloqueia uso), altos (ruim UX), baixos (cosmético)
- Corrigir cada um
- Retesta
- Documentar

**Exemplos comuns**:

- Erro no cálculo de rateio
- Excel não gera formatação certa
- HTML cortado em imprimir
- Dados não salvam em PostgreSQL

**Entregável**: Sistema sem bugs conhecidos

---

## 📊 DETALHES TÉCNICOS QUE O USUÁRIO PODE NÃO SABER

### 1. Diferença entre Chat Completions vs Responses API (GPT-5)

- **Chat Completions**: Retorna `choices[0].message.content` (texto simples)
- **Responses API**: Retorna `input`, `reasoning.content`, `text.content` (estruturado)
- Sistema usa Responses API porque precisa de reasoning e estrutura

### 2. Problema JSON com GPT-5

- Às vezes GPT-5 adiciona markdown (`json ... `) antes do JSON
- Código já faz limpeza, mas pode falhar se markdown estiver em lugar errado
- Solution: validar e fazer try/except em json.loads()

### 3. SQLite vs PostgreSQL

- SQLite: arquivo local, perfeito para começar, perde dados em redeploy
- PostgreSQL: servidor, persist dados, melhor para produção
- Migration é relativamente simples (SQL é compatível)

### 4. Performance de Análise

- Cada PDF leva ~20-30 segundos (GPT-5 é lento)
- Se tiver 10 PDFs: 200-300 segundos
- Solução futura: processamento em background com fila

### 5. Limites Render Free Tier

- SQLite tem 100MB limite
- PostgreSQL tem limite maior
- Depois de ~1000 análises, considerar upgrade

### 6. Desvio > 10% (Alerta)

- Sistema precisa comparar: (Realizado - Previsto) / Previsto \* 100
- Se > 10% ou < -10%: destacar em vermelho
- Importante para o usuário ver riscos

---

## ⏰ CRONOGRAMA RESUMIDO

```
SEMANA 1 (17-23 Nov) - 25h
├─ Seg-Ter: Validação Rateio (4h)
├─ Ter-Sex: Excel Consolidado (10h)
├─ Sex-Dom: Consolidação Cumulativa (7h)
└─ Dom-Seg: Interface Parâmetros (4h)

SEMANA 2 (24-30 Nov) - 28h
├─ Seg-Qua: HTML Executivo (12h)
├─ Qua-Sex: Visual Dashboard (10h)
└─ Sex-Dom: PostgreSQL Persistência (6h)

SEMANA 3 (1-3 Dez) - 15h
├─ Dom-Seg: Testes E2E (8h)
└─ Seg-Qua: Bugs + Refinamentos (7h)

TEMPO TOTAL: 68h (pouco mais de 2 semanas full-time)
```

---

## 📦 ARQUIVOS QUE SERÃO GERADOS

```
Após conclusão:
├─ Riviera_Consolidado_Base.xlsx (Excel)
├─ Riviera_Relatorio_YYYY-MM.html (HTML)
├─ Dashboard melhorado (UI com cards)
├─ PostgreSQL online (BD persistente)
└─ Sistema 100% funcional conforme especificação
```

---

## ✅ CRITÉRIO DE SUCESSO

- Excel com 4 abas e todos os dados
- HTML executivo imprimível
- Dashboard com cards e visual profissional
- Histórico persistente em nuvem
- 10 testes E2E passados
- 0 bugs críticos
- Sistema pronto para usar
