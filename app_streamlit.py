import streamlit as st
import zipfile
import tempfile
import os

from logic import *

# CONFIG DA PÁGINA
st.set_page_config(layout="wide")

col1, col2, col3 = st.columns([1,2,1])

with col1:
    st.image("logo.png", width=100)

with col2:
    st.markdown("<h2 style='text-align: center;'>Gerenciador de Imagens</h2>", unsafe_allow_html=True)

# TABS (ESSA É A NAVEGAÇÃO CORRETA)

tab1, tab2 = st.tabs(["Renomear imagens", "Remover imagens"])

# =========================
# REGRAS
# =========================

rules = {
        "Adiciona '0' após '_' (ex.: exemplo_1.jpg -> exemplo_01.jpg)": AddZeroAfterUnderscore(),
        "Remover '_1' do nome (ex.: exemplo_1.jpg -> exemplo.jpg)": RemoveUnderscoreOne(),
        "Incrementa sufixo numérico em +2 (ex.: exemplo_1.jpg -> exemplo_3.jpg)": IncrementSuffixByTwo(),
        "Converte sufixo para sequência 00, 01, 02... (ex.: exemplo_1.jpg -> exemplo_00.jpg)": SequenceZeroPadding(),
        "Prefixo EXT + letras (ex.: 773827336223_1.jpg -> EXT_773827336223_A.jpg)": PrefixExtWithLetters(),
        "Diminui sufixo numérico em 1 (ex.: 73683297483_2.jpg -> 73683297483_1.jpg)": DecrementSuffix(),
        "Substitui '_' por '.' (ex.: exemplo_1.jpg -> exemplo.1.jpg)": ReplaceUnderscoreWithDot(),
        "Remove o último caractere antes de '_' ou '.' (ex.: exemplo_1.jpg -> exempl_1.jpg)": RemoveLastCharBeforeSeparator(),
        "Substitui '_numero' por letra do alfabeto (ex.: 12345_1.jpg -> 12345A.jpg)": ReplaceUnderscoreNumberWithLetter(),
        "Substitui 'numero' após underscore por '_letra' (ex.: 12345_1.jpg -> 12345_A.jpg)": ReplaceNumberWithUnderscoreLetter(),
        "Adiciona '00' ao prefixo e renomeia sufixos: _1 remove _1, _2+ adiciona _gNN (ex.: 12345_1.jpg -> 0012345.jpg, 12345_2.jpg -> 0012345_g01.jpg)": AddZeroPrefixAndGallerySuffix(),
        "Adiciona 'P' após o número do produto (ex.: 12345_1.jpg -> 12345P_1.jpg)": AddPAfterProductNumber(),
        "Incrementa sufixo numérico em +1 (ex.: 12345_1.jpg -> 12345_2.jpg)": IncrementSuffixByOne()
        }

    # =========================
    # UI
    # =========================

# =========================
# 🔤 RENOMEAR
# =========================

with tab1:

    col_esq, col_centro, col_dir = st.columns([1,2,1])

    with col_centro:
        st.subheader("🔤 Renomear Imagens")

    with col_centro:
        uploaded_file = st.file_uploader("📁 ZIP", type=["zip"])
        suffix = st.text_input("Separador", "_")
        rule_name = st.selectbox("Regra", list(rules.keys()))

    if uploaded_file:
        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, uploaded_file.name)

        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())

        extract_dir = os.path.join(tmp_dir, "files")
        os.mkdir(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        files = sorted(os.listdir(extract_dir))
        option = rules[rule_name]

        # PREVIEW
        changes = option.preview(files, suffix)

        def highlight_changes(val_before, val_after):
            if val_before != val_after:
                return "background-color: #d4edda; color: black;"  # verde
            return ""

        preview_data = [{"Antes": a, "Depois": b} for a, b in changes]

        col_esq, col_centro, col_dir = st.columns([1,2,1])

        with col_centro:

            import pandas as pd

            preview_data = []

            for antes, depois in changes:
                preview_data.append({
                    "Antes": antes,
                    "Depois": f"<span style='color:#22c55e; font-weight:bold'>{depois}</span>"
                })

            df = pd.DataFrame(preview_data)

            st.subheader("🔍 Preview")

            st.markdown(
                df.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )

        # VALIDAÇÃO
        new_names = [new for _, new in changes]
        if len(new_names) != len(set(new_names)):
            st.error("⚠️ Conflito de nomes detectado!")
            st.stop()

        # BOTÃO CENTRALIZADO
        col_esq, col_centro, col_dir = st.columns([1,2,1])

        with col_centro:
            executar = st.button("🚀 Renomear arquivos")

        if executar:
            for old, new in changes:
                os.rename(
                    os.path.join(extract_dir, old),
                    os.path.join(extract_dir, new)
                )

            output_zip = os.path.join(tmp_dir, "resultado.zip")

            with zipfile.ZipFile(output_zip, 'w') as zipf:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        path = os.path.join(root, file)
                        zipf.write(path, os.path.relpath(path, extract_dir))

            with open(output_zip, "rb") as f:
                st.download_button(
                    "⬇️ Baixar resultado",
                    f,
                    file_name="Imagens renomeadas.zip"
                )

# =========================
# 🗑️ REMOVER
# =========================

with tab2:

    col_esq, col_centro, col_dir = st.columns([1,2,1])

    with col_centro:
        st.subheader("🗑️ Remover Imagens")

    with col_centro:
        uploaded_file = st.file_uploader("📁 ZIP", type=["zip"], key="remove")

    if uploaded_file:
        tmp = tempfile.mkdtemp()
        zip_path = os.path.join(tmp, uploaded_file.name)

        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())

        extract_dir = os.path.join(tmp, "files")
        os.mkdir(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        files = sorted(os.listdir(extract_dir))

        valid_ext = (".jpg", ".png", ".jpeg", ".webp")
        files = [f for f in files if f.lower().endswith(valid_ext)]

        col_esq, col_centro, col_dir = st.columns([1,2,1])

        with col_centro:
            index = st.number_input("Remover a partir de:", min_value=1, step=1)

        with col_centro:
            st.info("Arquivos com número >= serão removidos")

        files_to_remove = []

        for f in files:
            name, ext = os.path.splitext(f)

            if "_" in name:
                num = name.split("_")[-1]
                if num.isdigit() and int(num) >= index:
                    files_to_remove.append(f)

        st.divider()

        st.subheader("🧾 Preview")
        st.write(files_to_remove)

        if st.button("🗑️ Remover"):
            for f in files_to_remove:
                os.remove(os.path.join(extract_dir, f))

            output_zip = os.path.join(tmp, "resultado.zip")

            with zipfile.ZipFile(output_zip, 'w') as zipf:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        path = os.path.join(root, file)
                        zipf.write(path, os.path.relpath(path, extract_dir))

            with open(output_zip, "rb") as f:
                st.download_button("⬇️ Baixar resultado", f, "resultado.zip")