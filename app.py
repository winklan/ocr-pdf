import os
import uuid
import threading
import json
import time
from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
from ocr_engine import validar_configuracao, obter_info_pdf, calcular_lotes, processar_lote

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

for pasta in ['uploads', 'temp', 'output']:
    os.makedirs(pasta, exist_ok=True)


# Estado das sessões em memória
sessoes = {}  # session_id -> dict com progresso e arquivos


def processar_em_background(session_id, caminho_pdf, lotes, formatos, pasta_saida):
    sessao = sessoes[session_id]
    os.makedirs(pasta_saida, exist_ok=True)

    for i, (inicio, fim) in enumerate(lotes):
        numero_lote = i + 1
        sessao['lote_atual'] = numero_lote
        sessao['pagina_atual'] = 0
        sessao['total_paginas_lote'] = fim - inicio + 1

        def progresso(pag_atual, total, _sessao=sessao):
            _sessao['pagina_atual'] = pag_atual

        try:
            arquivos = processar_lote(
                caminho_pdf, numero_lote, inicio, fim,
                pasta_saida, formatos, progresso,
                cancelar_fn=lambda _s=sessao: _s.get('cancelar', False)
            )
            if arquivos is None:
                sessao['status'] = 'cancelado'
                return
            sessao['lotes_concluidos'].append({
                'numero': numero_lote,
                'arquivos': {k: os.path.basename(v) for k, v in arquivos.items()}
            })
        except Exception as e:
            sessao['erro'] = str(e)
            sessao['status'] = 'erro'
            return

        if sessao.get('cancelar'):
            sessao['status'] = 'cancelado'
            return

    sessao['status'] = 'concluido'


@app.route('/')
def index():
    config = validar_configuracao()
    return render_template('index.html', config=config)


@app.route('/upload', methods=['POST'])
def upload():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    arquivo = request.files['arquivo']
    if not arquivo.filename.lower().endswith('.pdf'):
        return jsonify({'erro': 'Apenas arquivos PDF são aceitos'}), 400

    session_id = str(uuid.uuid4())
    nome_arquivo = f'{session_id}.pdf'
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    arquivo.save(caminho)

    try:
        info = obter_info_pdf(caminho)
        tamanho_lote = int(request.form.get('tamanho_lote', 500))
        lotes = calcular_lotes(info['paginas'], tamanho_lote)
        return jsonify({
            'session_id': session_id,
            'paginas': info['paginas'],
            'total_lotes': len(lotes),
            'lotes': [{'numero': i+1, 'inicio': l[0], 'fim': l[1]} for i, l in enumerate(lotes)]
        })
    except Exception as e:
        os.remove(caminho)
        return jsonify({'erro': str(e)}), 500


@app.route('/download/<session_id>/<nome_arquivo>')
def download(session_id, nome_arquivo):
    nome_arquivo = os.path.basename(nome_arquivo)  # evita path traversal
    caminho = os.path.join(app.config['OUTPUT_FOLDER'], session_id, nome_arquivo)
    if not os.path.exists(caminho):
        return jsonify({'erro': 'Arquivo não encontrado'}), 404
    return send_file(caminho, as_attachment=True)


@app.route('/process', methods=['POST'])
def process():
    dados = request.get_json()
    session_id = dados.get('session_id')
    formatos = dados.get('formatos', {'pesquisavel': True, 'limpo': True, 'txt': True})
    tamanho_lote = int(dados.get('tamanho_lote', 500))

    caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.pdf')
    if not os.path.exists(caminho_pdf):
        return jsonify({'erro': 'Sessão não encontrada'}), 404

    info = obter_info_pdf(caminho_pdf)
    lotes = calcular_lotes(info['paginas'], tamanho_lote)
    pasta_saida = os.path.join(app.config['OUTPUT_FOLDER'], session_id)

    sessoes[session_id] = {
        'status': 'processando',
        'total_lotes': len(lotes),
        'lote_atual': 0,
        'pagina_atual': 0,
        'total_paginas_lote': 0,
        'lotes_concluidos': [],
        'cancelar': False
    }

    thread = threading.Thread(
        target=processar_em_background,
        args=(session_id, caminho_pdf, lotes, formatos, pasta_saida)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'ok': True})


@app.route('/progress/<session_id>')
def progress(session_id):
    def gerar_eventos():
        while True:
            if session_id not in sessoes:
                yield f"data: {json.dumps({'erro': 'sessão não encontrada'})}\n\n"
                break

            sessao = sessoes[session_id]
            yield f"data: {json.dumps(sessao)}\n\n"

            if sessao['status'] in ('concluido', 'erro', 'cancelado'):
                break

            time.sleep(1)

    return Response(
        stream_with_context(gerar_eventos()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/cancel/<session_id>', methods=['POST'])
def cancel(session_id):
    if session_id in sessoes:
        sessoes[session_id]['cancelar'] = True
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
