# 📊 Estrutura de Dados - Riviera Ingestor

## Exemplo de Dados no Banco

### Tabela: `movimentos`

```
id | competencia | codigo_obra | obra_nome                    | tipo               | valor        | fonte
---|-------------|-------------|-----------------------------|-------------------|--------------|--------
1  | 2025-05     | 603         | Ampliação Shopping Riviera  | Despesa           | 2154037.89   | PDF
2  | 2025-05     | 603         | Ampliação Shopping Riviera  | Aporte_Rateado    | 850000.00    | Calc
3  | 2025-05     | 603         | Ampliação Shopping Riviera  | Rentabilidade     | 6545.49      | PDF
4  | 2025-05     | 603         | Ampliação Shopping Riviera  | Saldo_Final       | 962170.12    | PDF
...
```

### Tabela: `orcamento_previsto`

```
id | codigo_obra | obra_nome                   | custo_previsto | data_atualizacao
---|-------------|-----------------------------|-----------------|-----------------
1  | 603         | Ampliação Shopping Riviera  | 20000000.00     | 2025-09-09
2  | 616         | Fiação Enterrada Av. Riviera| 1500000.00      | 2025-09-09
3  | 637         | Retrofit Shopping Riviera   | 5000000.00      | 2025-09-09
```

### Tabela: `configuracoes`

```
id | chave                  | valor
---|------------------------|----------------------------------------------
1  | metodo_rateio_aporte   | proporcional_despesa_mes
2  | dias_retencao_pdf      | 7
3  | versao_schema          | 1.0.0
```

---

## 📋 Exemplo de Requisição/Resposta API

### GET /api/resumo

**Request:**

```bash
curl -X GET http://localhost:5000/api/resumo
```

**Response:**

```json
{
  "status": "success",
  "resumo": {
    "obras": [
      {
        "codigo_obra": "603",
        "obra_nome": "Ampliação Shopping Riviera",
        "despesas_totais": 19586870.16,
        "aportes_rateados": 13047296.45,
        "rentabilidade": 184112.15,
        "saldo_final": -6355461.56
      },
      {
        "codigo_obra": "637",
        "obra_nome": "Retrofit Shopping Riviera",
        "despesas_totais": 1776106.16,
        "aportes_rateados": 1876000.0,
        "rentabilidade": 0.0,
        "saldo_final": 99893.84
      },
      {
        "codigo_obra": "616",
        "obra_nome": "Fiação Enterrada Av. Riviera",
        "despesas_totais": 22664.42,
        "aportes_rateados": 54406.11,
        "rentabilidade": 0.0,
        "saldo_final": 31741.69
      }
    ],
    "totais": {
      "despesas_totais": 21386747.26,
      "aportes_rateados": 21877149.46,
      "rentabilidade": 184112.15
    }
  }
}
```

### GET /api/movimentos?competencia=2025-09&codigo_obra=603

**Request:**

```bash
curl -X GET "http://localhost:5000/api/movimentos?competencia=2025-09&codigo_obra=603"
```

**Response:**

```json
{
  "status": "success",
  "count": 4,
  "data": [
    {
      "id": 1,
      "competencia": "2025-09",
      "codigo_obra": "603",
      "obra_nome": "Ampliação Shopping Riviera",
      "tipo": "Despesa",
      "valor": 6306220.27,
      "fonte": "SHOPP_562_601_603_e_604_DESPESA_SETEMBRO_2025.pdf",
      "data_insercao": "2025-09-09T18:30:45"
    },
    {
      "id": 2,
      "competencia": "2025-09",
      "codigo_obra": "603",
      "obra_nome": "Ampliação Shopping Riviera",
      "tipo": "Aporte_Rateado",
      "valor": 3721203.28,
      "fonte": "Rateio proporcional",
      "data_insercao": "2025-09-09T18:30:45"
    }
  ]
}
```

### POST /api/upload

**Request:**

```bash
curl -X POST http://localhost:5000/api/upload \
  -F "files=@SHOPP_562_601_603_e_604_POSIÇÃO_FINANC_SETEMBRO_2025.pdf" \
  -F "files=@SHOPP_562_601_603_e_604_DESPESAS_SETEMBRO_2025.pdf"
```

**Response:**

```json
{
  "status": "success",
  "processados": [
    {
      "arquivo": "20250909_180530_SHOPP_562_601_603_e_604_POSIÇÃO_FINANC_SETEMBRO_2025.pdf",
      "tamanho": 1245870,
      "status": "recebido"
    },
    {
      "arquivo": "20250909_180531_SHOPP_562_601_603_e_604_DESPESAS_SETEMBRO_2025.pdf",
      "tamanho": 987654,
      "status": "recebido"
    }
  ],
  "erros": [],
  "total": 2
}
```

### GET /api/orcamento

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "codigo_obra": "603",
      "obra_nome": "Ampliação Shopping Riviera",
      "custo_previsto": 20000000.0,
      "data_atualizacao": "2025-09-09T15:20:30"
    },
    {
      "id": 2,
      "codigo_obra": "616",
      "obra_nome": "Fiação Enterrada Av. Riviera",
      "custo_previsto": 1500000.0,
      "data_atualizacao": "2025-09-09T15:20:30"
    },
    {
      "id": 3,
      "codigo_obra": "637",
      "obra_nome": "Retrofit Shopping Riviera",
      "custo_previsto": 5000000.0,
      "data_atualizacao": "2025-09-09T15:20:30"
    }
  ]
}
```

---

## 💾 Script de Exemplo para Carregar Dados Iniciais

```python
"""
Script para popular banco de dados com dados de exemplo
Executar apenas em desenvolvimento!
"""

import sqlite3
from api.index import get_db_connection

# Dados de exemplo
MOVIMENTOS_EXEMPLO = [
    # Maio 2025 - Obra 603
    ('2025-05', '603', 'Ampliação Shopping Riviera', 'Despesa', 2154037.89, 'PDF'),
    ('2025-05', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 850000.00, 'Calc'),
    ('2025-05', '603', 'Ampliação Shopping Riviera', 'Rentabilidade', 6545.49, 'PDF'),

    # Junho 2025 - Obra 603
    ('2025-06', '603', 'Ampliação Shopping Riviera', 'Despesa', 2865325.00, 'PDF'),
    ('2025-06', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 12775186.79, 'Calc'),

    # Julho 2025 - Obra 603
    ('2025-07', '603', 'Ampliação Shopping Riviera', 'Despesa', 4368473.70, 'PDF'),
    ('2025-07', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 649800.00, 'Calc'),
    ('2025-07', '603', 'Ampliação Shopping Riviera', 'Rentabilidade', 100351.12, 'PDF'),

    # Agosto 2025 - Obra 603
    ('2025-08', '603', 'Ampliação Shopping Riviera', 'Despesa', 3892813.30, 'PDF'),
    ('2025-08', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 948729.30, 'Calc'),

    # Setembro 2025 - Obra 603
    ('2025-09', '603', 'Ampliação Shopping Riviera', 'Despesa', 6306220.27, 'PDF'),
    ('2025-09', '603', 'Ampliação Shopping Riviera', 'Aporte_Rateado', 5483433.37, 'Calc'),
    ('2025-09', '603', 'Ampliação Shopping Riviera', 'Rentabilidade', 29071.12, 'PDF'),

    # Obra 616 - Fiação Enterrada
    ('2025-05', '616', 'Fiação Enterrada Av. Riviera', 'Despesa', 30779.76, 'PDF'),
    ('2025-06', '616', 'Fiação Enterrada Av. Riviera', 'Despesa', 82.60, 'PDF'),
    ('2025-07', '616', 'Fiação Enterrada Av. Riviera', 'Despesa', 22416.62, 'PDF'),
    ('2025-08', '616', 'Fiação Enterrada Av. Riviera', 'Despesa', 82.60, 'PDF'),
    ('2025-09', '616', 'Fiação Enterrada Av. Riviera', 'Despesa', 82.60, 'PDF'),

    # Obra 637 - Retrofit
    ('2025-06', '637', 'Retrofit Shopping Riviera', 'Despesa', 6064.72, 'PDF'),
    ('2025-07', '637', 'Retrofit Shopping Riviera', 'Despesa', 216975.97, 'PDF'),
    ('2025-08', '637', 'Retrofit Shopping Riviera', 'Despesa', 540686.68, 'PDF'),
    ('2025-09', '637', 'Retrofit Shopping Riviera', 'Despesa', 1012378.79, 'PDF'),
]

ORCAMENTOS_EXEMPLO = [
    ('603', 'Ampliação Shopping Riviera', 20000000.00),
    ('616', 'Fiação Enterrada Av. Riviera', 1500000.00),
    ('637', 'Retrofit Shopping Riviera', 5000000.00),
]

def carregar_dados_exemplo():
    """Carregar dados de exemplo no banco"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Limpar dados existentes (apenas em dev!)
            cursor.execute('DELETE FROM movimentos')
            cursor.execute('DELETE FROM orcamento_previsto')

            # Inserir movimentos
            for mov in MOVIMENTOS_EXEMPLO:
                cursor.execute('''
                    INSERT INTO movimentos
                    (competencia, codigo_obra, obra_nome, tipo, valor, fonte)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', mov)

            # Inserir orçamentos
            for orc in ORCAMENTOS_EXEMPLO:
                cursor.execute('''
                    INSERT INTO orcamento_previsto
                    (codigo_obra, obra_nome, custo_previsto)
                    VALUES (?, ?, ?)
                ''', orc)

            conn.commit()
            print(f"✅ {len(MOVIMENTOS_EXEMPLO)} movimentos carregados")
            print(f"✅ {len(ORCAMENTOS_EXEMPLO)} orçamentos carregados")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    carregar_dados_exemplo()
```

**Executar:**

```bash
python scripts/carregar_exemplo.py
```

---

## 📊 Visualização em Excel (Simulação)

### Aba: base_movimentos

| competencia | codigo_obra | obra_nome                  | tipo           | valor      | fonte |
| ----------- | ----------- | -------------------------- | -------------- | ---------- | ----- |
| 2025-05     | 603         | Ampliação Shopping Riviera | Despesa        | 2154037.89 | PDF   |
| 2025-05     | 603         | Ampliação Shopping Riviera | Aporte_Rateado | 850000.00  | Calc  |
| 2025-05     | 616         | Fiação Enterrada           | Despesa        | 30779.76   | PDF   |

### Aba: consolidado_resumo

| codigo_obra | obra_nome                  | mes_2025_05_despesa | mes_2025_05_aporte | mes_2025_06_despesa | mes_2025_06_aporte |
| ----------- | -------------------------- | ------------------- | ------------------ | ------------------- | ------------------ |
| 603         | Ampliação Shopping Riviera | 2154037.89          | 850000.00          | 2865325.00          | 12775186.79        |
| 616         | Fiação Enterrada           | 30779.76            | 0                  | 82.60               | 0                  |
| 637         | Retrofit Shopping Riviera  | 0                   | 0                  | 6064.72             | 0                  |

### Aba: custo_vs_previsto

| codigo_obra | obra_nome                  | custo_previsto | custo_acumulado | % realizado | desvio_r$   | status   |
| ----------- | -------------------------- | -------------- | --------------- | ----------- | ----------- | -------- |
| 603         | Ampliação Shopping Riviera | 20000000.00    | 19586870.16     | 97.93%      | -413129.84  | ✓ Dentro |
| 616         | Fiação Enterrada           | 1500000.00     | 22664.42        | 1.51%       | -1477335.58 | ✓ Dentro |
| 637         | Retrofit Shopping Riviera  | 5000000.00     | 1776106.16      | 35.52%      | -3223893.84 | ✓ Dentro |

---

**Pronto!** Estrutura de dados configurada e validada.
