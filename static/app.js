let sessionId = null;
let eventoSource = null;
let nomeDocumento = '';

const areaDrop = document.getElementById('area-drop');
const inputArquivo = document.getElementById('input-arquivo');
const nomeArquivo = document.getElementById('nome-arquivo');
const infoPdf = document.getElementById('info-pdf');
const btnIniciar = document.getElementById('btn-iniciar');
const btnCancelar = document.getElementById('btn-cancelar');
const secaoProgresso = document.getElementById('secao-progresso');
const secaoDownloads = document.getElementById('secao-downloads');
const textoProgresso = document.getElementById('texto-progresso');
const barraFill = document.getElementById('barra-fill');
const textoPercentual = document.getElementById('texto-percentual');
const listaDownloads = document.getElementById('lista-downloads');
const documentoAtual = document.getElementById('documento-atual');

// Drag & drop
areaDrop.addEventListener('dragover', e => { e.preventDefault(); areaDrop.classList.add('drag-over'); });
areaDrop.addEventListener('dragleave', () => areaDrop.classList.remove('drag-over'));
areaDrop.addEventListener('drop', e => {
    e.preventDefault();
    areaDrop.classList.remove('drag-over');
    const arquivo = e.dataTransfer.files[0];
    if (arquivo) processarArquivoSelecionado(arquivo);
});
inputArquivo.addEventListener('change', e => {
    if (e.target.files[0]) processarArquivoSelecionado(e.target.files[0]);
});

async function processarArquivoSelecionado(arquivo) {
    if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
        alert('Por favor, selecione um arquivo PDF.');
        return;
    }

    nomeDocumento = arquivo.name;
    nomeArquivo.textContent = `📄 ${arquivo.name}`;
    btnIniciar.disabled = true;
    infoPdf.textContent = 'Carregando informações do PDF...';
    infoPdf.classList.remove('hidden');

    const formData = new FormData();
    formData.append('arquivo', arquivo);
    formData.append('tamanho_lote', document.getElementById('tamanho-lote').value);

    try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const dados = await resp.json();

        if (dados.erro) { infoPdf.textContent = `Erro: ${dados.erro}`; return; }

        sessionId = dados.session_id;
        infoPdf.innerHTML = `
            <strong>${dados.paginas.toLocaleString('pt-BR')} páginas</strong> detectadas.
            Serão processados <strong>${dados.total_lotes} lote(s)</strong>
            de até ${document.getElementById('tamanho-lote').value} páginas cada.
        `;
        btnIniciar.disabled = false;
    } catch (e) {
        infoPdf.textContent = `Erro de comunicação: ${e.message}`;
    }
}

btnIniciar.addEventListener('click', async () => {
    if (!sessionId) return;

    const formatos = {
        pesquisavel: document.getElementById('opt-pesquisavel').checked,
        limpo: document.getElementById('opt-limpo').checked,
        txt: document.getElementById('opt-txt').checked
    };

    if (!formatos.pesquisavel && !formatos.limpo && !formatos.txt) {
        alert('Selecione pelo menos um formato de saída.');
        return;
    }

    document.getElementById('secao-upload').classList.add('hidden');
    documentoAtual.textContent = `📄 ${nomeDocumento}`;
    secaoProgresso.classList.remove('hidden');
    secaoDownloads.classList.remove('hidden');

    await fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            formatos,
            tamanho_lote: parseInt(document.getElementById('tamanho-lote').value)
        })
    });

    iniciarSSE();
});

function iniciarSSE() {
    eventoSource = new EventSource(`/progress/${sessionId}`);
    eventoSource.onmessage = e => {
        const dados = JSON.parse(e.data);
        atualizarProgresso(dados);

        if (['concluido', 'erro', 'cancelado'].includes(dados.status)) {
            eventoSource.close();
        }
    };
}

function atualizarProgresso(dados) {
    const totalLotes = dados.total_lotes || 1;
    const loteAtual = dados.lote_atual || 0;
    const pagAtual = dados.pagina_atual || 0;
    const totalPagLote = dados.total_paginas_lote || 1;

    const progGlobal = ((loteAtual - 1 + pagAtual / totalPagLote) / totalLotes) * 100;
    const pct = Math.min(Math.round(progGlobal), 100);

    barraFill.style.width = `${pct}%`;
    textoPercentual.textContent = `${pct}%`;

    if (dados.status === 'processando') {
        textoProgresso.textContent = `Lote ${loteAtual} de ${totalLotes} — Página ${pagAtual}/${totalPagLote}`;
    } else if (dados.status === 'concluido') {
        textoProgresso.textContent = `✅ Concluído: ${nomeDocumento}`;
        barraFill.style.width = '100%';
        textoPercentual.textContent = '100%';
        btnCancelar.disabled = true;
    } else if (dados.status === 'erro') {
        textoProgresso.textContent = `❌ Erro: ${dados.erro}`;
    } else if (dados.status === 'cancelado') {
        textoProgresso.textContent = '⚠️ Processamento cancelado.';
    }

    // Atualizar lista de downloads
    listaDownloads.innerHTML = '';
    for (const lote of (dados.lotes_concluidos || [])) {
        const div = document.createElement('div');
        div.className = 'lote-concluido';
        div.innerHTML = `<strong>Lote ${lote.numero}</strong>`;
        for (const [tipo, nome] of Object.entries(lote.arquivos)) {
            const label = { pesquisavel: 'PDF Pesquisável', limpo: 'PDF Limpo', txt: 'TXT' }[tipo] || tipo;
            div.innerHTML += ` <a href="/download/${sessionId}/${nome}" class="btn-download" download>${label}</a>`;
        }
        listaDownloads.appendChild(div);
    }
}

btnCancelar.addEventListener('click', async () => {
    if (!sessionId) return;
    await fetch(`/cancel/${sessionId}`, { method: 'POST' });
    btnCancelar.disabled = true;
});
