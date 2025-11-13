"""
PraiasSP Tools - Riviera Ingestor
API Principal para processamento de relatórios financeiros
"""

import os
import sys
import sqlite3
import signal
import time
import threading
from contextlib import contextmanager
from datetime import datetime

# ================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# ================================

def init_db():
    """Inicializar banco de dados com tabelas necessárias"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historico_riviera.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Tabela de movimentos financeiros
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competencia TEXT NOT NULL,
                codigo_obra TEXT NOT NULL,
                obra_nome TEXT,
                tipo TEXT NOT NULL,
                valor REAL NOT NULL,
                fonte TEXT,
                data_insercao DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(competencia, codigo_obra, tipo)
            )
        ''')
        
        # Tabela de uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_arquivo TEXT NOT NULL,
                competencia TEXT,
                data_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processado'
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE,
                modelo TEXT DEFAULT 'gpt-5',
                max_tokens INTEGER DEFAULT 6000,
                chunk_size INTEGER DEFAULT 8000,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de orçamentos previstos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orcamento_previsto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_obra TEXT UNIQUE NOT NULL,
                obra_nome TEXT,
                custo_previsto REAL,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

# Pool de conexões para SQLite
@contextmanager
def get_db_connection():
    """Context manager para gerenciar conexões com banco de dados"""
    conn = None
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historico_riviera.db')
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Erro na conexão com banco: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Inicializar banco
init_db()

# ================================
# IMPORTS FLASK
# ================================

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import gc
import json
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__, static_folder='../static', template_folder='../templates')

# Configurar CORS explicitamente
CORS(app, 
     origins=[
         "https://praias-sp-tools.vercel.app",
         "http://localhost:3000",
         "http://localhost:5173",
         "http://localhost:8080"
     ],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True,
     max_age=3600
)

# Configurações
REQUEST_TIMEOUT = 120
OPENAI_TIMEOUT = 90
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 52428800))  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar cliente OpenAI global
openai_client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    timeout=OPENAI_TIMEOUT
)

# ================================
# MIDDLEWARE E HANDLERS
# ================================

@app.before_request
def before_request():
    """Registrar tempo de início da requisição"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Registrar requisições longas e fazer limpeza + garantir CORS headers"""
    # Garantir headers CORS explícitos
    origin = request.headers.get('Origin')
    allowed_origins = [
        "https://praias-sp-tools.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    duration = time.time() - request.start_time
    if duration > 5:
        print(f"⚠️ Requisição lenta: {request.endpoint} - {duration:.2f}s")
    return response

@app.teardown_appcontext
def cleanup(exception):
    """Limpeza de memória após requisição"""
    gc.collect()

# Tratamento de sinais para graceful shutdown
def signal_handler(signum, frame):
    """Handler para sinais de encerramento"""
    print(f"\n🛑 Recebido sinal {signum}. Finalizando aplicação...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ================================
# ROTAS - INDEX
# ================================

@app.route('/', methods=['GET', 'HEAD'])
def index():
    """Rota raiz - verifica se API está online"""
    return "PraiasSP-Tools API online", 200

# ================================
# ROTAS - DADOS
# ================================

@app.route('/api/movimentos', methods=['GET'])
def get_movimentos():
    """Obter movimentos financeiros"""
    try:
        competencia = request.args.get('competencia')
        codigo_obra = request.args.get('codigo_obra')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM movimentos WHERE 1=1'
            params = []
            
            if competencia:
                query += ' AND competencia = ?'
                params.append(competencia)
            
            if codigo_obra:
                query += ' AND codigo_obra = ?'
                params.append(codigo_obra)
            
            query += ' ORDER BY competencia DESC, codigo_obra ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            movimentos = [dict(row) for row in rows]
            
            return jsonify({
                'status': 'success',
                'count': len(movimentos),
                'data': movimentos
            }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/resumo', methods=['GET'])
def get_resumo():
    """Obter resumo consolidado"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Resumo por obra
            cursor.execute('''
                SELECT 
                    codigo_obra,
                    obra_nome,
                    SUM(CASE WHEN tipo = 'Despesa' THEN valor ELSE 0 END) as despesas_totais,
                    SUM(CASE WHEN tipo = 'Aporte_Rateado' THEN valor ELSE 0 END) as aportes_rateados,
                    SUM(CASE WHEN tipo = 'Rentabilidade' THEN valor ELSE 0 END) as rentabilidade,
                    SUM(CASE WHEN tipo = 'Saldo_Final' THEN valor ELSE 0 END) as saldo_final
                FROM movimentos
                GROUP BY codigo_obra, obra_nome
                ORDER BY despesas_totais DESC
            ''')
            
            obras = [dict(row) for row in cursor.fetchall()]
            
            # Totais gerais
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN tipo = 'Despesa' THEN valor ELSE 0 END) as despesas_totais,
                    SUM(CASE WHEN tipo = 'Aporte_Rateado' THEN valor ELSE 0 END) as aportes_rateados,
                    SUM(CASE WHEN tipo = 'Rentabilidade' THEN valor ELSE 0 END) as rentabilidade
                FROM movimentos
            ''')
            
            totais = dict(cursor.fetchone())
            
            return jsonify({
                'status': 'success',
                'resumo': {
                    'obras': obras,
                    'totais': totais
                }
            }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ================================
# FUNÇÕES AUXILIARES - PROCESSAMENTO PARALELO
# ================================

def process_single_pdf(file_obj, model):
    """
    Processa um único PDF de forma independente (para parallelização)
    
    Args:
        file_obj: Objeto de arquivo
        model: Modelo a usar
    
    Returns:
        Dict com resultado ou erro
    """
    try:
        filename = file_obj.filename
        print(f"  🔄 Iniciando: {filename}")
        
        # Extrair texto
        pdf_text = extract_pdf_text(file_obj)
        
        if not pdf_text or len(pdf_text.strip()) < 10:
            return {
                'status': 'error',
                'filename': filename,
                'message': 'PDF sem texto extraível'
            }
        
        print(f"    ✅ Texto extraído: {filename}")
        
        # Analisar com OpenAI
        analysis = analyze_with_openai(pdf_text, document_type='relatório financeiro', model=model)
        
        print(f"    ✅ Análise concluída: {filename}")
        
        # Salvar no banco
        save_analysis_to_db(analysis)
        
        return {
            'status': 'success',
            'filename': filename,
            'codigo_obra': analysis.get('codigo_obra'),
            'competencia': analysis.get('competencia')
        }
    
    except Exception as e:
        print(f"    ❌ Erro em {file_obj.filename}: {str(e)[:100]}")
        return {
            'status': 'error',
            'filename': file_obj.filename,
            'message': str(e)[:200]
        }

# ================================
# ROTAS - UPLOAD E PROCESSAMENTO
# ================================

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Receber e processar múltiplos PDFs em paralelo"""
    start_time = time.time()
    
    try:
        if 'files' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({
                'status': 'error',
                'message': 'Lista de arquivos vazia'
            }), 400
        
        # Obter modelo
        model = request.form.get('model', 'gpt-5')
        modelos_suportados = ['gpt-5', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
        if model not in modelos_suportados:
            model = 'gpt-5'
        
        print(f"\n{'='*60}")
        print(f"📦 PROCESSAMENTO EM PARALELO DE {len(files)} PDFs")
        print(f"🤖 Modelo: {model}")
        print(f"⏱️ Início: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Validar e filtrar arquivos
        arquivos_validos = []
        erros_validacao = []
        
        for file in files:
            if file.filename == '':
                erros_validacao.append('Arquivo sem nome')
                continue
            
            if not file.filename.lower().endswith('.pdf'):
                erros_validacao.append(f'{file.filename} - tipo inválido')
                continue
            
            if file.content_length and file.content_length > MAX_FILE_SIZE:
                erros_validacao.append(f'{file.filename} - muito grande (>{MAX_FILE_SIZE/(1024*1024)}MB)')
                continue
            
            arquivos_validos.append(file)
        
        print(f"✅ {len(arquivos_validos)} arquivo(s) válido(s)")
        if erros_validacao:
            print(f"⚠️ {len(erros_validacao)} arquivo(s) descartado(s)")
        
        # ⭐ PROCESSAMENTO PARALELO com ThreadPoolExecutor
        resultados = []
        erros = erros_validacao.copy()
        
        if arquivos_validos:
            print(f"\n🔄 Iniciando processamento paralelo...")
            # Usar 3 workers (bom para 3 PDFs)
            max_workers = min(3, len(arquivos_validos))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submeter todos os PDFs para processamento
                futures = {
                    executor.submit(process_single_pdf, file, model): file.filename 
                    for file in arquivos_validos
                }
                
                # Coletar resultados conforme completam
                for future in as_completed(futures):
                    filename = futures[future]
                    try:
                        resultado = future.result(timeout=300)  # 5 minutos max por PDF
                        resultados.append(resultado)
                        
                        if resultado['status'] == 'error':
                            erros.append(f"{filename}: {resultado.get('message', 'Erro desconhecido')}")
                    except Exception as e:
                        erros.append(f"{filename}: {str(e)[:100]}")
        
        processing_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ Processamento completo!")
        print(f"📊 Resultados: {len([r for r in resultados if r['status'] == 'success'])} sucesso(s)")
        if erros:
            print(f"❌ Erros: {len(erros)}")
        print(f"⏱️ Tempo total: {processing_time:.2f}s")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success' if resultados else 'error',
            'message': f'Processados {len(resultados)} PDF(s)',
            'model': model,
            'processados': [r for r in resultados if r['status'] == 'success'],
            'erros': erros,
            'processing_time': round(processing_time, 2)
        }), 200 if resultados else 400
    
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ ERRO GERAL: {str(e)}")
        print(f"⏱️ Tempo até erro: {processing_time:.2f}s")
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar: {str(e)[:200]}',
            'processing_time': round(processing_time, 2)
        }), 500

# ================================
# ROTAS - CONFIGURAÇÃO
# ================================

@app.route('/api/configuracoes', methods=['GET'])
def get_configuracoes():
    """Obter configurações"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT chave, valor FROM configuracoes')
            configuracoes = {row[0]: row[1] for row in cursor.fetchall()}
            
            return jsonify({
                'status': 'success',
                'configuracoes': configuracoes
            }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/configuracoes', methods=['POST'])
def atualizar_configuracoes():
    """Atualizar configurações"""
    try:
        data = request.json
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for chave, valor in data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO configuracoes (chave, valor)
                    VALUES (?, ?)
                ''', (chave, str(valor)))
            
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Configurações atualizadas'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ================================
# ROTAS - ORÇAMENTO PREVISTO
# ================================

@app.route('/api/orcamento', methods=['GET'])
def get_orcamento():
    """Obter orçamentos previstos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT codigo_obra, obra_nome, custo_previsto
                FROM orcamento_previsto
                ORDER BY codigo_obra
            ''')
            
            orcamentos = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'status': 'success',
                'data': orcamentos
            }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/orcamento', methods=['POST'])
def atualizar_orcamento():
    """Atualizar orçamento previsto"""
    try:
        data = request.json
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for item in data:
                cursor.execute('''
                    INSERT OR REPLACE INTO orcamento_previsto 
                    (codigo_obra, obra_nome, custo_previsto)
                    VALUES (?, ?, ?)
                ''', (item['codigo_obra'], item.get('obra_nome'), item['custo_previsto']))
            
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Orçamento atualizado'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ================================
# FASE 2.1 - ANÁLISE COM OpenAI
# ================================

def extract_pdf_text(file):
    """Extrair texto de PDF usando PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"❌ Erro ao extrair PDF: {e}")
        raise

# ================================
# UTILITÁRIO - COMPATIBILIDADE COM RESPONSES API (GPT-5)
# ================================

class CompatResponse:
    """Classe para compatibilidade entre Responses API (GPT-5) e Chat Completions API"""
    class Choice:
        class Message:
            def __init__(self, content):
                self.content = content
        
        def __init__(self, content):
            self.message = self.Message(content)
            self.finish_reason = "stop"
    
    def __init__(self, content):
        self.choices = [self.Choice(content)]

def process_openai_request(messages, model, max_tokens):
    """
    Processa requisição OpenAI com suporte a GPT-5 (Responses API) e compatibilidade com outros modelos
    
    Args:
        messages: Lista de mensagens com roles 'system' e 'user'
        model: Nome do modelo ('gpt-5', 'gpt-4o', etc)
        max_tokens: Máximo de tokens na resposta
    
    Returns:
        Tuple (response, error_message)
    """
    try:
        print(f"🔄 Preparando requisição para {model}...")
        print(f"   Max Tokens: {max_tokens}")
        
        # ⭐ GPT-5 usa Responses API, não Chat Completions!
        if model.startswith('gpt-5'):
            print("🔄 Usando Responses API para GPT-5...")
            
            # Extrair system prompt e user message
            system_content = ""
            user_message = ""
            for msg in messages:
                if msg.get("role") == "system":
                    system_content = msg.get("content", "")
                elif msg.get("role") == "user":
                    user_message = msg.get("content", "")
            
            # Concatenar para Responses API (requer input único)
            combined_input = f"INSTRUÇÕES:\n{system_content}\n\nCONTEÚDO:\n{user_message}"
            
            print(f"📝 System prompt length: {len(system_content)} chars")
            print(f"📝 User message length: {len(user_message)} chars")
            print(f"📝 Combined input length: {len(combined_input)} chars")
            
            # ✅ Responses API com parâmetros corretos para GPT-5
            # IMPORTANTE: reasoning com effort LOW para economizar tempo e memória!
            response = openai_client.responses.create(
                model=model,
                input=combined_input,
                max_output_tokens=max_tokens,
                reasoning={"effort": "low"},  # ⭐ LOW, não HIGH (evita timeout/memória)
                text={"verbosity": "high"}
            )
            
            print(f"✅ Resposta GPT-5 recebida | Output tokens: {max_tokens}")
            return CompatResponse(response.output_text), None
        
        else:
            # Chat Completions API para outros modelos (GPT-4o, GPT-4, etc)
            print(f"🔄 Usando Chat Completions API para {model}...")
            
            try:
                # Tentar com max_completion_tokens (novo SDK)
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    temperature=0.7,
                    timeout=OPENAI_TIMEOUT
                )
                print(f"✅ Usando max_completion_tokens: {max_tokens}")
                return response, None
            except TypeError:
                # Fallback para max_tokens (SDK antigo ou modelos antigos)
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    timeout=OPENAI_TIMEOUT
                )
                print(f"✅ Usando max_tokens (compatibilidade): {max_tokens}")
                return response, None
    
    except Exception as e:
        print(f"❌ ERRO em process_openai_request: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, str(e)

def analyze_with_openai(pdf_text, document_type='relatório', model='gpt-4o'):
    """Analisar texto com OpenAI (GPT-5, GPT-4o, etc) - Lógica CEO Financeiro"""
    try:
        prompt = f"""🎯 VOCÊ É UM AUDITOR FINANCEIRO SÊNIOR - RIVIERA EMPREENDIMENTOS

MISSÃO CRÍTICA:
Processar PDFs mensais de Praias SP com PRECISÃO ABSOLUTA. Cada número errado custará MILHARES.
Você NÃO pode errar. Você NÃO pode ser vago. Você NÃO pode aproximar.

═══════════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO DO DOCUMENTO:
┌─ Procure nos títulos/cabeçalhos:
│  ├─ "POSIÇÃO FINANC" → Tipo: POSICAO_FINANCEIRA (balanço consolidado)
│  ├─ "DESPESAS" → Tipo: DETALHAMENTO_DESPESAS (nota fiscal a nota fiscal)
│  └─ Código da obra: 562, 601, 603, 604, 616, BCO, etc
└─ OBRIGATÓRIO extrair: CÓDIGO, TIPO, COMPETÊNCIA

EXTRAÇÃO OBRIGATÓRIA DE CAMPOS:
═════════════════════════════════════════════════════════════════════════════

1️⃣ COMPETÊNCIA (data do relatório)
   - Procure: "SETEMBRO 25", "SET 2025", "09/2025", "setembro/2025"
   - CONVERTA SEMPRE para: "09/2025"
   - SE NÃO ENCONTRAR: return erro "Competência não encontrada"

2️⃣ CÓDIGO DA OBRA (identificador único)
   - Procure no título: 562, 601, 603, 604, 616, BCO, etc
   - Se houver múltiplos codes (ex: "562 601 603 e 604"), SEPARE EM 4 EXTRAÇÕES
   - SE NÃO ENCONTRAR: return erro "Código não encontrado"

3️⃣ SALDO INICIAL (sempre em número com 2 decimais)
   - Procure: "Saldo em 31/08/2025", "Saldo Inicial", "Saldo Anterior"
   - Format: 1234567.89 (sem R$, sem separadores de milhar)
   - SE NÃO ENCONTRAR: "não_informado"

4️⃣ DESPESAS DETALHADAS (CRÍTICO - não aproxime)
   - Procure TODAS as linhas com valores negativos ou etiquetadas "Despesa"
   - PARA CADA DESPESA extrait:
     * descricao: "Fornecedor X - Serviço Y"
     * valor: 12345.67 (exato, sem aproximação)
     * categoria: "Material" | "MO" | "Servicos" | "Locacao" | "Outros"
     * fornecedor: "Nome Exato do Fornecedor"
   - TOTALIZE: despesas_total = SUM(todas despesas)
   - VALIDAR: Se há tabelas, leia TODA a coluna de valores
   - SE HOUVER DÚVIDA: indique com "⚠️" no JSON

5️⃣ RECEITAS (tudo que entra)
   - Aportes do pool: valor_exato
   - Rentabilidade: valor_exato
   - Reembolsos: valor_exato
   - TOTAL DE RECEITAS: receitas_total = SUM(todas receitas)

6️⃣ SALDO FINAL (obrigatório e preciso)
   - Procure: "Saldo em 30/09/2025", "Saldo Disponível", "Saldo Final"
   - Format: 1234567.89
   - VALIDAR: Saldo_Final ≈ Saldo_Inicial + Receitas - Despesas (±R$1,00)
   - SE DIVERGÊNCIA > R$1,00: adicione flag "saldo_auditoria_necessaria"

7️⃣ RATEIO DE APORTES (CÁLCULO AUTOMÁTICO)
   - Se "POSIÇÃO FINANCEIRA": extraia aportes_recebidos_total
   - CALCULE taxa_rateio = despesas_esta_obra / total_despesas_mes
   - CALCULE aporte_rateado = aportes_recebidos_total × taxa_rateio
   - Exemplo:
     * Despesas Obra 616: R$ 82,60
     * Despesas Shopping: R$ 7.319.079,56
     * Total: R$ 7.319.162,16
     * Taxa Obra 616: 82,60 / 7.319.162,16 = 0.001129%
     * Aporte recebido: R$ 5.483.433,37
     * Aporte rateado Obra 616: R$ 5.483.433,37 × 0.001129% = R$ XXX,XX

8️⃣ CONCILIAÇÃO BANCÁRIA (bandeira vermelha)
   - Procure: "Bradesco", "Saldo Banco", "Conciliado com"
   - EXTRAIA: saldo_banco_oficial, diferenca_conciliacao
   - SE diferenca > R$ 100: flag "diferenca_relevante_investigar"

═════════════════════════════════════════════════════════════════════════════

REGRAS NÃO-NEGOCIÁVEIS:
❌ NÃO retorne narrativa, APENAS JSON
❌ NÃO aproxime valores (use valores exatos do PDF)
❌ NÃO agregue obras diferentes (cada código é uma extração separada)
❌ NÃO ignore tabelas (leia cada linha)
❌ NÃO esqueça decimais (sempre XX,XX)
❌ SE NÃO ENCONTRAR CAMPO: use "não_informado" COM FLAG DE ALERTA

═════════════════════════════════════════════════════════════════════════════

RETORNE ESTE JSON (sem markdown, sem explicações):

[
  {{
    "competencia": "09/2025",
    "codigo_obra": "616",
    "nome_obra": "Extra Contratual - Fiação Enterrada Av. Riviera Mod. 17 e 18",
    "tipo_documento": "POSICAO_FINANCEIRA",
    "saldo_inicial": 282995.57,
    "saldo_final": 355854.25,
    "despesas": [
      {{"descricao": "Descrição exata", "valor": 123.45, "categoria": "Servicos", "fornecedor": "Nome Fornecedor"}}
    ],
    "despesas_total": 82.60,
    "receitas": [
      {{"tipo": "Aporte", "valor": 1000.00}},
      {{"tipo": "Rentabilidade", "valor": 72941.28}}
    ],
    "receitas_total": 72941.28,
    "aportes_pool": {{
      "valor_total_pool": 5483433.37,
      "despesas_todas_obras": 7319162.16,
      "taxa_rateio_esta_obra": 0.00001129,
      "valor_rateado_esta_obra": 61.87,
      "metodo_calculo": "Proporcional às despesas do mês"
    }},
    "rentabilidade_mensal": 72941.28,
    "conciliacao_bancaria": {{
      "saldo_banco": 355854.25,
      "saldo_sistema": 355854.25,
      "diferenca": 0.00,
      "status": "conciliado"
    }},
    "validacoes": {{
      "saldo_auditoria": {{"status": "OK", "diferenca_permitida": 0.00}},
      "alertas": []
    }},
    "observacoes": "Texto se houver algo relevante",
    "qualidade_extracao": "✅ Completa" | "⚠️ Parcial - campos faltantes" | "❌ Erro - campo crítico ausente"
  }}
]

═════════════════════════════════════════════════════════════════════════════

DOCUMENTO A PROCESSAR:
{pdf_text}"""
        
        messages = [
            {
                "role": "system",
                "content": "VOCÊ DEVE RETORNAR APENAS JSON VÁLIDO. NÃO RETORNE MARKDOWN, NÃO RETORNE NARRATIVA, NÃO RETORNE EXPLICAÇÕES. APENAS JSON PURO E VÁLIDO."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Usar função unificada com suporte a GPT-5
        print(f"🤖 Analisando com {model}...")
        response, error = process_openai_request(messages, model, max_tokens=6000)
        
        if error:
            print(f"❌ Erro ao chamar OpenAI: {error}")
            raise ValueError(f"Erro na API OpenAI: {error}")
        
        # Extrair conteúdo
        response_text = response.choices[0].message.content.strip()
        
        # ⭐ AGRESSIVAMENTE remover markdown e narrativa
        print(f"📝 Resposta bruta ({len(response_text)} chars): {response_text[:100]}...")
        
        # Remover markdown code blocks
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            elif response_text.startswith('\n'):
                response_text = response_text[1:]
        
        # Remover trailing markdown
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Procurar por [ ou { para começar o JSON
        start_idx = response_text.find('[')
        if start_idx == -1:
            start_idx = response_text.find('{')
        
        if start_idx > 0:
            print(f"⚠️ Encontrou narrativa antes do JSON. Removendo primeiros {start_idx} chars...")
            response_text = response_text[start_idx:]
        
        # Procurar pelo final do JSON
        end_idx = max(response_text.rfind(']'), response_text.rfind('}'))
        if end_idx > 0 and end_idx < len(response_text) - 1:
            print(f"⚠️ Encontrou narrativa após JSON. Removendo últimos {len(response_text) - end_idx - 1} chars...")
            response_text = response_text[:end_idx + 1]
        
        # Tentar parse JSON com retry
        try:
            result = json.loads(response_text)
            print(f"✅ JSON parseado com sucesso!")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao fazer parse JSON na primeira tentativa: {e}")
            print(f"📄 Conteúdo: {response_text[:200]}...")
            
            # RETRY: Se for array, tentar extrair primeiro elemento
            try:
                result = json.loads(response_text)
                return result
            except:
                raise ValueError(f"Resposta não é JSON válido. Resposta: {response_text[:500]}")
    
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao fazer parse JSON da resposta OpenAI: {e}")
        raise ValueError(f"Resposta inválida do OpenAI: {str(e)}")
    except Exception as e:
        print(f"❌ Erro ao analisar com OpenAI: {e}")
        raise

def save_analysis_to_db(analysis):
    """Salvar análise no banco de dados"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            competencia = analysis.get('competencia', 'Não informado')
            codigo_obra = analysis.get('codigo_obra', 'Não informado')
            obra_nome = analysis.get('obra_nome', 'Sem nome')
            
            # Salvar movimentos
            movimentos = analysis.get('movimentos', [])
            for mov in movimentos:
                cursor.execute('''
                    INSERT OR REPLACE INTO movimentos 
                    (competencia, codigo_obra, obra_nome, tipo, valor, fonte)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    competencia,
                    codigo_obra,
                    obra_nome,
                    mov.get('tipo', 'Outro'),
                    float(mov.get('valor', 0)),
                    mov.get('fonte', 'Não especificada')
                ))
            
            # Salvar arquivo processado
            cursor.execute('''
                INSERT INTO uploads (nome_arquivo, competencia, status)
                VALUES (?, ?, ?)
            ''', (f"analyzed_{codigo_obra}_{competencia}", competencia, 'processado'))
            
            conn.commit()
        
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar análise no banco: {e}")
        raise

@app.route('/api/analyze-pdf', methods=['POST'])
def analyze_pdf_endpoint():
    """
    Endpoint para análise automática de PDF com OpenAI (suporta GPT-5, GPT-4o, etc)
    
    Request:
        - file: PDF file (multipart/form-data)
        - model: Modelo OpenAI (opcional, padrão: 'gpt-4o')
               Suportados: 'gpt-5', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo'
    
    Response:
        {
            "status": "success|error",
            "data": {...análise extraída...},
            "model": "modelo usado",
            "message": "..."
        }
    """
    try:
        # Validar arquivo
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Arquivo sem nome'
            }), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'status': 'error',
                'message': 'Apenas arquivos PDF são aceitos'
            }), 400
        
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': 'Arquivo muito grande (máximo 50MB)'
            }), 400
        
        # Obter modelo do parâmetro ou usar padrão
        model = request.form.get('model', 'gpt-4o')
        
        # Validar modelo
        modelos_suportados = ['gpt-5', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
        if model not in modelos_suportados:
            print(f"⚠️ Modelo '{model}' não suportado. Usando gpt-4o.")
            model = 'gpt-4o'
        
        print(f"🔧 Modelo selecionado: {model}")
        
        # 1. Extrair texto do PDF
        print(f"📄 Extraindo texto de: {file.filename}")
        pdf_text = extract_pdf_text(file)
        
        if not pdf_text or len(pdf_text.strip()) < 10:
            return jsonify({
                'status': 'error',
                'message': 'PDF não contém texto extraível'
            }), 400
        
        print(f"✅ Texto extraído ({len(pdf_text)} caracteres)")
        
        # 2. Analisar com OpenAI (usando modelo selecionado)
        print(f"🤖 Analisando com {model}...")
        analysis = analyze_with_openai(pdf_text, document_type='relatório financeiro', model=model)
        
        print(f"✅ Análise concluída: {analysis.get('codigo_obra')} - {analysis.get('competencia')}")
        
        # 3. Salvar no banco de dados
        print("💾 Salvando no banco de dados...")
        save_analysis_to_db(analysis)
        
        print("✅ Análise salva com sucesso!")
        
        return jsonify({
            'status': 'success',
            'message': f'PDF analisado com sucesso usando {model}',
            'model': model,
            'data': analysis
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"❌ Erro ao processar PDF: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar PDF: {str(e)}'
        }), 500

# ================================
# ENDPOINT - CHAT COM IA (COMPATÍVEL COM FRONTEND)
# ================================

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_endpoint():
    """
    Endpoint de chat unificado com suporte a múltiplos modelos (GPT-5, GPT-4o, etc)
    
    Request (JSON):
        {
            "model": "gpt-5" (ou "gpt-4o", "gpt-4", "gpt-3.5-turbo"),
            "messages": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."}
            ],
            "max_tokens": 6000
        }
    
    Response:
        {
            "choices": [{
                "message": {
                    "content": "resposta da IA"
                }
            }],
            "model": "modelo usado",
            "processing_time": 1.23
        }
    """
    
    # Responder às requisições OPTIONS (preflight CORS)
    if request.method == 'OPTIONS':
        return '', 204
    
    start_time = time.time()
    
    try:
        data = request.json
        
        # Validação 1: Requisição vazia
        if not data:
            return jsonify({
                'error': 'Requisição vazia'
            }), 400
        
        model = data.get('model', 'gpt-5')
        messages = data.get('messages', [])
        
        # Validação 2: Mensagens vazias
        if not messages:
            return jsonify({
                'error': 'Nenhuma mensagem fornecida'
            }), 400
        
        # Validação 3: Limitar tamanho do prompt
        messages_str = str(messages)
        if len(messages_str) > 50000:
            return jsonify({
                'error': 'Prompt muito longo. Máximo 50k caracteres.'
            }), 400
        
        # Validação 4: Modelo suportado
        modelos_suportados = ['gpt-5', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
        if model not in modelos_suportados:
            print(f"⚠️ Modelo '{model}' não suportado. Usando padrão: gpt-5")
            model = 'gpt-5'
        
        # CRÍTICO: Limites por modelo (copiar exatamente da referência)
        if model.startswith('gpt-5'):
            max_tokens = min(data.get('max_tokens', 6000), 12000)  # GPT-5: até 12k tokens
        else:
            max_tokens = min(data.get('max_tokens', 2000), 4000)   # Outros: até 4k tokens
        
        # Logging estruturado
        print("\n" + "="*60)
        print("🚀 === NOVA REQUISIÇÃO DE ANÁLISE ===")
        print(f"📧 Modelo: {model}")
        print(f"🔢 Max Tokens: {max_tokens}")
        print(f"📝 Total de mensagens: {len(messages)}")
        print(f"📄 Tamanho do prompt: {len(messages_str)} caracteres")
        print("="*60)
        
        # Chamar process_openai_request
        response, error = process_openai_request(messages, model, max_tokens)
        
        # Validação 5: Erro na API OpenAI
        if error:
            print(f"❌ ERRO na API OpenAI: {error}")
            return jsonify({
                'error': f'Erro na API OpenAI: {error}'
            }), 500
        
        # Validação 6: Response nulo
        if not response:
            print("❌ Response é None!")
            return jsonify({
                'error': 'Resposta nula da OpenAI'
            }), 500
        
        # Validação 7: Choices vazio
        if not response.choices:
            print("❌ Response.choices vazio!")
            return jsonify({
                'error': 'Resposta vazia da OpenAI (choices vazio)'
            }), 500
        
        # Validação 8: Content vazio ou None
        content = response.choices[0].message.content
        if not content:
            print("⚠️ WARNING: Content é None ou vazio!")
            print(f"   Finish reason: {response.choices[0].finish_reason}")
            content = "(Resposta vazia recebida da OpenAI)"
        
        processing_time = time.time() - start_time
        
        # Logging de sucesso
        print("✅ Resposta da OpenAI recebida com sucesso!")
        print(f"📄 Tamanho da resposta: {len(content)} caracteres")
        print(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
        print("="*60 + "\n")
        
        return jsonify({
            'choices': [{
                'message': {
                    'content': content
                }
            }],
            'model': model,
            'processing_time': round(processing_time, 2)
        }), 200
    
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Erro interno: {str(e)}"
        print(f"❌ ERRO GERAL: {error_msg}")
        print(f"⏱️ Tempo até erro: {processing_time:.2f}s")
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': error_msg
        }), 500

# ================================
# ROTAS - HEALTH & STATUS
# ================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint com informações detalhadas"""
    try:
        # Testar conexão com banco
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM movimentos')
            total_movimentos = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM uploads')
            total_uploads = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'ok',
            'service': 'PraiasSP-Tools API',
            'timestamp': datetime.now().isoformat(),
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'database': {
                'status': 'working',
                'total_movimentos': total_movimentos,
                'total_uploads': total_uploads
            },
            'configuration': {
                'request_timeout_seconds': REQUEST_TIMEOUT,
                'openai_timeout_seconds': OPENAI_TIMEOUT,
                'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024)
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'PraiasSP-Tools API',
            'timestamp': datetime.now().isoformat(),
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'database': {
                'status': 'error',
                'error': str(e)
            }
        }), 500

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    """Tratamento de rota não encontrada"""
    return jsonify({
        'status': 'error',
        'message': 'Rota não encontrada'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erro interno"""
    return jsonify({
        'status': 'error',
        'message': 'Erro interno do servidor'
    }), 500

# ================================
# ENDPOINTS DE CONFIGURAÇÕES (idêntico à referência)
# ================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Endpoint para recuperar configurações do usuário"""
    try:
        # Tentar obter API Key do header
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key', 'default')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT modelo, max_tokens, chunk_size FROM configuracoes WHERE api_key = ?',
                (api_key,)
            )
            row = cursor.fetchone()
        
        if row:
            return jsonify({
                'modelo': row[0],
                'max_tokens': row[1],
                'chunk_size': row[2],
                'cached': False
            })
        else:
            # Retornar valores padrão se não encontrado
            return jsonify({
                'modelo': 'gpt-5',
                'max_tokens': 6000,
                'chunk_size': 8000,
                'cached': True
            })
    except Exception as e:
        print(f"❌ Erro ao buscar configurações: {e}")
        return jsonify({
            'modelo': 'gpt-5',
            'max_tokens': 6000,
            'chunk_size': 8000,
            'error': str(e),
            'cached': True
        }), 200  # Retornar 200 mesmo com erro para fallback

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Endpoint para salvar configurações do usuário"""
    try:
        data = request.json
        api_key = data.get('api_key', 'default')
        modelo = data.get('modelo', 'gpt-5')
        max_tokens = data.get('max_tokens', 6000)
        chunk_size = data.get('chunk_size', 8000)
        
        # Validações básicas
        if max_tokens < 100 or max_tokens > 128000:
            return jsonify({'error': 'max_tokens deve estar entre 100 e 128000'}), 400
        
        if chunk_size < 100 or chunk_size > 128000:
            return jsonify({'error': 'chunk_size deve estar entre 100 e 128000'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Tentar atualizar, senão inserir (UPSERT)
            cursor.execute('''
                INSERT INTO configuracoes (api_key, modelo, max_tokens, chunk_size)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(api_key) 
                DO UPDATE SET 
                    modelo = excluded.modelo,
                    max_tokens = excluded.max_tokens,
                    chunk_size = excluded.chunk_size,
                    data_atualizacao = CURRENT_TIMESTAMP
            ''', (api_key, modelo, max_tokens, chunk_size))
            conn.commit()
        
        print(f"✅ Configurações salvas para API Key: {api_key[:10]}...")
        return jsonify({
            'success': True,
            'message': 'Configurações salvas com sucesso',
            'modelo': modelo,
            'max_tokens': max_tokens,
            'chunk_size': chunk_size
        })
    except Exception as e:
        print(f"❌ Erro ao salvar configurações: {e}")
        return jsonify({'error': str(e)}), 500

# ================================
# INICIALIZAÇÃO
# ================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )
