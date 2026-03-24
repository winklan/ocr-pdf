import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from ocr_engine import validar_configuracao, obter_info_pdf, calcular_lotes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

for pasta in ['uploads', 'temp', 'output']:
    os.makedirs(pasta, exist_ok=True)


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
    caminho = os.path.join(app.config['OUTPUT_FOLDER'], session_id, nome_arquivo)
    if not os.path.exists(caminho):
        return jsonify({'erro': 'Arquivo não encontrado'}), 404
    return send_file(caminho, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
