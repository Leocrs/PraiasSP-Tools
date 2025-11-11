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
                chave TEXT UNIQUE NOT NULL,
                valor TEXT,
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

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__, static_folder='../static', template_folder='../templates')
CORS(app)

# Configurações
REQUEST_TIMEOUT = 120
OPENAI_TIMEOUT = 90
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 52428800))  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================================
# MIDDLEWARE E HANDLERS
# ================================

@app.before_request
def before_request():
    """Registrar tempo de início da requisição"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Registrar requisições longas e fazer limpeza"""
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
# ROTAS - HEALTH CHECK
# ================================

@app.route('/health', methods=['GET'])
def health():
    """Health check da API"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'Riviera Ingestor'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Servir página inicial"""
    try:
        return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'templates'), 'index.html')
    except Exception as e:
        print(f"❌ Erro ao servir index.html: {e}")
        return jsonify({'error': 'Página não encontrada', 'details': str(e)}), 404

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
# ROTAS - UPLOAD E PROCESSAMENTO
# ================================

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Receber e processar PDFs"""
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
        
        processados = []
        erros = []
        
        for file in files:
            if file.filename == '':
                erros.append('Arquivo sem nome')
                continue
            
            if not file.filename.lower().endswith('.pdf'):
                erros.append(f'{file.filename} - tipo de arquivo inválido')
                continue
            
            if file.content_length and file.content_length > MAX_FILE_SIZE:
                erros.append(f'{file.filename} - arquivo muito grande')
                continue
            
            try:
                # Salvar arquivo
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Registrar no banco
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO uploads (nome_arquivo, status)
                        VALUES (?, ?)
                    ''', (filename, 'processando'))
                    conn.commit()
                
                processados.append({
                    'arquivo': filename,
                    'tamanho': file.content_length,
                    'status': 'recebido'
                })
            
            except Exception as e:
                erros.append(f'{file.filename} - {str(e)}')
        
        return jsonify({
            'status': 'success' if processados else 'error',
            'processados': processados,
            'erros': erros,
            'total': len(processados)
        }), 200 if processados else 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
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

def analyze_with_openai(pdf_text, document_type='relatório'):
    """Analisar texto com OpenAI GPT-4o"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no .env")
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Você é especialista em análise de relatórios financeiros de construção (Riviera Empreendimentos).
        
Analise o seguinte {document_type} e extraia os dados estruturados:
- Competência (mês/ano no formato MM/YYYY)
- Código da obra (identificador)
- Nome da obra
- Tipo de movimentos (Despesa, Aporte_Rateado, Rentabilidade, Saldo_Final)
- Valores (números em reais)
- Fonte do movimento
- Observações importantes

Se houver tabelas, preserve todos os dados e valores. Se algo não estiver claro, indique como "Não informado".

Retorne APENAS um JSON válido (sem markdown, sem explicações) com esta estrutura:
{{
    "competencia": "MM/YYYY",
    "codigo_obra": "ABC123",
    "obra_nome": "Nome da Obra",
    "movimentos": [
        {{"tipo": "Despesa", "valor": 1000.00, "fonte": "Fornecedor X", "descricao": "..."}},
        {{"tipo": "Aporte_Rateado", "valor": 5000.00, "fonte": "Rateio", "descricao": "..."}}
    ],
    "observacoes": "..."
}}

DOCUMENTO:
{pdf_text}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Retorne APENAS JSON válido, sem markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Extrair conteúdo e fazer parse JSON
        response_text = response.choices[0].message.content.strip()
        
        # Remover markdown code blocks se existirem
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        return result
    
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao fazer parse JSON da resposta OpenAI: {e}")
        raise ValueError(f"Resposta inválida do OpenAI: {str(e)}")
    except Exception as e:
        print(f"❌ Erro ao chamar OpenAI: {e}")
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
    Endpoint para análise automática de PDF com OpenAI
    
    Request:
        - file: PDF file (multipart/form-data)
    
    Response:
        {
            "status": "success|error",
            "data": {...análise extraída...},
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
        
        # 1. Extrair texto do PDF
        print(f"📄 Extraindo texto de: {file.filename}")
        pdf_text = extract_pdf_text(file)
        
        if not pdf_text or len(pdf_text.strip()) < 10:
            return jsonify({
                'status': 'error',
                'message': 'PDF não contém texto extraível'
            }), 400
        
        print(f"✅ Texto extraído ({len(pdf_text)} caracteres)")
        
        # 2. Analisar com OpenAI
        print("🤖 Analisando com OpenAI GPT-4o...")
        analysis = analyze_with_openai(pdf_text, document_type='relatório financeiro')
        
        print(f"✅ Análise concluída: {analysis.get('codigo_obra')} - {analysis.get('competencia')}")
        
        # 3. Salvar no banco de dados
        print("💾 Salvando no banco de dados...")
        save_analysis_to_db(analysis)
        
        print("✅ Análise salva com sucesso!")
        
        return jsonify({
            'status': 'success',
            'message': 'PDF analisado e salvo com sucesso',
            'data': analysis
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"❌ Erro ao analisar PDF: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar PDF: {str(e)}'
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
