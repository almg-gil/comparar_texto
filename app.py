import os
import re
from pathlib import Path
from difflib import SequenceMatcher
from html import escape

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# 1. Configuração da página
# ============================================================

st.set_page_config(
    page_title="Comparador de Textos",
    layout="wide"
)

st.title("Comparador de Textos")
st.caption("Comparação entre texto1.txt e texto2.txt")
st.caption("Exemplo retirado do PL 2470/2024 (Substitutivos 1 e 2)")


# ============================================================
# 2. Caminhos dos arquivos no repositório
# ============================================================

PASTA_APP = Path(__file__).parent

arquivo1 = PASTA_APP / "texto1.txt"
arquivo2 = PASTA_APP / "texto2.txt"


# ============================================================
# 3. Leitura dos arquivos
# ============================================================

def ler_arquivo_txt(caminho):
    if not caminho.exists():
        raise FileNotFoundError(f"O arquivo {caminho.name} não foi encontrado no repositório.")

    with open(caminho, "r", encoding="utf-8-sig") as f:
        return f.read()


try:
    texto1 = ler_arquivo_txt(arquivo1)
    texto2 = ler_arquivo_txt(arquivo2)
except FileNotFoundError as erro:
    st.error(str(erro))
    st.stop()


# ============================================================
# 4. Funções auxiliares de renderização
# ============================================================

def renderizar_texto(texto):
    return escape(texto, quote=False)


def renderizar_diferenca(texto):
    if texto.isspace():
        return "&nbsp;" * len(texto)
    return escape(texto, quote=False)


def bloco_omissao(texto):
    """
    Cria um bloco vermelho vazio no Texto 2 para indicar
    conteúdo existente no Texto 1 que foi omitido no Texto 2.
    """
    tamanho = max(len(texto), 1)
    return f'<span class="omissao-texto2">{"&nbsp;" * tamanho}</span>'


# ============================================================
# 5. Função principal de comparação
# ============================================================

def gerar_comparacao_html(texto1, texto2):
    linhas1 = texto1.splitlines()
    linhas2 = texto2.splitlines()

    html_coluna_esquerda = []
    html_coluna_direita = []

    def adicionar_linha_igual(l1, l2):
        html_coluna_esquerda.append(
            f'<p class="linha-lei">{renderizar_texto(l1)}</p>'
        )
        html_coluna_direita.append(
            f'<p class="linha-lei">{renderizar_texto(l2)}</p>'
        )

    def adicionar_linha_removida(l1):
        html_coluna_esquerda.append(
            f'<p class="linha-lei removido">{renderizar_texto(l1)}</p>'
        )
        html_coluna_direita.append(
            '<p class="linha-lei omissao-linha-texto2">&nbsp;</p>'
        )

    def adicionar_linha_adicionada(l2):
        html_coluna_esquerda.append(
            '<p class="linha-lei espaco-vazio">&nbsp;</p>'
        )
        html_coluna_direita.append(
            f'<p class="linha-lei adicionado">{renderizar_texto(l2)}</p>'
        )

    def comparar_linhas_com_destaque(l1, l2):
        """
        Compara duas linhas pareadas e destaca:
        - remoções no Texto 1 em vermelho;
        - acréscimos no Texto 2 em verde;
        - omissões no Texto 2 com espaço vermelho vazio.
        """

        p1 = [token for token in re.split(r'(\s+)', l1) if token]
        p2 = [token for token in re.split(r'(\s+)', l2) if token]

        sub_matcher = SequenceMatcher(None, p1, p2)

        sub_esq = []
        sub_dir = []

        for sub_tag, si1, si2, sj1, sj2 in sub_matcher.get_opcodes():
            t1_original = "".join(p1[si1:si2])
            t2_original = "".join(p2[sj1:sj2])

            t1 = renderizar_diferenca(t1_original)
            t2 = renderizar_diferenca(t2_original)

            if sub_tag == "equal":
                sub_esq.append(renderizar_texto(t1_original))
                sub_dir.append(renderizar_texto(t2_original))

            elif sub_tag == "delete":
                sub_esq.append(f'<span class="removido">{t1}</span>')
                sub_dir.append(bloco_omissao(t1_original))

            elif sub_tag == "insert":
                sub_dir.append(f'<span class="adicionado">{t2}</span>')

            elif sub_tag == "replace":
                sub_esq.append(f'<span class="removido">{t1}</span>')
                sub_dir.append(f'<span class="adicionado">{t2}</span>')

        html_coluna_esquerda.append(
            f'<p class="linha-lei">{"".join(sub_esq)}</p>'
        )
        html_coluna_direita.append(
            f'<p class="linha-lei">{"".join(sub_dir)}</p>'
        )

    def processar_bloco_replace(bloco1, bloco2):
        """
        Trata blocos de substituição que podem conter:
        - linha alterada;
        - linha omitida;
        - linha acrescentada;
        - tudo isso no mesmo bloco.
        """

        matcher_linhas = SequenceMatcher(None, bloco1, bloco2)

        for tag, i1, i2, j1, j2 in matcher_linhas.get_opcodes():
            if tag == "equal":
                for l1, l2 in zip(bloco1[i1:i2], bloco2[j1:j2]):
                    adicionar_linha_igual(l1, l2)

            elif tag == "delete":
                for l1 in bloco1[i1:i2]:
                    adicionar_linha_removida(l1)

            elif tag == "insert":
                for l2 in bloco2[j1:j2]:
                    adicionar_linha_adicionada(l2)

            elif tag == "replace":
                qtd_pares = min(i2 - i1, j2 - j1)

                for k in range(qtd_pares):
                    l1 = bloco1[i1 + k]
                    l2 = bloco2[j1 + k]
                    comparar_linhas_com_destaque(l1, l2)

                for l1 in bloco1[i1 + qtd_pares:i2]:
                    adicionar_linha_removida(l1)

                for l2 in bloco2[j1 + qtd_pares:j2]:
                    adicionar_linha_adicionada(l2)

    matcher = SequenceMatcher(None, linhas1, linhas2)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for l1, l2 in zip(linhas1[i1:i2], linhas2[j1:j2]):
                adicionar_linha_igual(l1, l2)

        elif tag == "delete":
            for l1 in linhas1[i1:i2]:
                adicionar_linha_removida(l1)

        elif tag == "insert":
            for l2 in linhas2[j1:j2]:
                adicionar_linha_adicionada(l2)

        elif tag == "replace":
            bloco1 = linhas1[i1:i2]
            bloco2 = linhas2[j1:j2]
            processar_bloco_replace(bloco1, bloco2)

    resultado_esquerda = "\n".join(html_coluna_esquerda)
    resultado_direita = "\n".join(html_coluna_direita)

    html_final = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Comparador de Textos</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f4f6f9;
                padding: 20px;
                margin: 0;
            }}

            .wrapper {{
                width: 100%;
                box-sizing: border-box;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}

            h2 {{
                color: #333;
                margin-bottom: 20px;
                border-bottom: 2px solid #eef2f5;
                padding-bottom: 12px;
            }}

            .comparador {{
                display: flex;
                gap: 20px;
                align-items: flex-start;
            }}

            .coluna {{
                flex: 1;
                padding: 15px;
                background-color: #fafbfc;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                overflow-x: auto;
            }}

            .coluna-titulo {{
                font-weight: bold;
                color: #586069;
                margin-bottom: 15px;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #e1e4e8;
                padding-bottom: 5px;
            }}

            .linha-lei {{
                font-size: 15px;
                line-height: 1.8;
                margin: 0;
                padding: 4px 6px;
                border-bottom: 1px dashed #f0f2f5;
                min-height: 27px;
                white-space: pre-wrap;
            }}

            .espaco-vazio {{
                background-color: #f1f3f5;
                border-radius: 4px;
            }}

            .removido {{
                color: #d73a49;
                background-color: #ffeef0;
                border-radius: 4px;
                font-weight: 500;
                display: inline-block;
            }}

            .adicionado {{
                color: #28a745;
                background-color: #e6ffed;
                border-radius: 4px;
                font-weight: 500;
                display: inline-block;
            }}

            .omissao-texto2 {{
                background-color: #ffeef0;
                border: 1px solid #d73a49;
                border-radius: 4px;
                display: inline-block;
                min-width: 1ch;
                vertical-align: baseline;
            }}

            .omissao-linha-texto2 {{
                background-color: #ffeef0;
                border: 1px solid #d73a49;
                border-radius: 4px;
                min-height: 27px;
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <h2>Comparação de Texto</h2>

            <div class="comparador">
                <div class="coluna">
                    <div class="coluna-titulo">Texto 1</div>
                    {resultado_esquerda}
                </div>

                <div class="coluna">
                    <div class="coluna-titulo">Texto 2</div>
                    {resultado_direita}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html_final


# ============================================================
# 6. Interface Streamlit
# ============================================================

with st.sidebar:
    st.header("Arquivos comparados")
    st.write(f"**Texto 1:** `{arquivo1.name}`")
    st.write(f"**Texto 2:** `{arquivo2.name}`")

    st.divider()

    st.write("Os arquivos devem estar no mesmo repositório do GitHub que o `app.py`.")

    mostrar_textos = st.checkbox("Mostrar textos originais", value=False)


if mostrar_textos:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Texto 1")
        st.text_area("Conteúdo do texto1.txt", texto1, height=300)

    with col2:
        st.subheader("Texto 2")
        st.text_area("Conteúdo do texto2.txt", texto2, height=300)


html_comparacao = gerar_comparacao_html(texto1, texto2)

components.html(
    html_comparacao,
    height=900,
    scrolling=True
)
