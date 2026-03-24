import streamlit as st
import zipfile
import tempfile
import os

from app import *

st.set_page_config(layout="wide")
st.title("📦 Renomeador de Imagens")

# =========================
# CONFIGURAÇÃO DAS REGRAS
# =========================

rules = {
    "Zero após _": AddZeroAfterUnderscore(),
    "Remover _1": RemoveUnderscoreOne(),
    "Incrementar +2": IncrementSuffixByTwo(),
    "Sequência 00,01,02": SequenceZeroPadding(),
    "Prefixo EXT + letras": PrefixExtWithLetters(),
    "Diminuir -1": DecrementSuffix(),
    "Trocar _ por .": ReplaceUnderscoreWithDot(),
    "Remover último caractere": RemoveLastCharBeforeSeparator(),
    "Número → Letra": ReplaceUnderscoreNumberWithLetter(),
    "Número → _Letra": ReplaceNumberWithUnderscoreLetter(),
    "Galeria _gNN": AddZeroPrefixAndGallerySuffix(),
    "Adicionar P": AddPAfterProductNumber(),
    "Incrementar +1": IncrementSuffixByOne()
}

# =========================
# UI
# =========================

uploaded_file = st.file_uploader("Envie um .zip", type=["zip"])

rule_name = st.selectbox("Escolha a regra", list(rules.keys()))
suffix = st.text_input("Separador", value="_")

# =========================
# PROCESSAMENTO
# =========================

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

    st.subheader("🔍 Preview")

    st.dataframe(
        [{"Antes": a, "Depois": b} for a, b in changes],
        use_container_width=True
    )

    # ⚠️ VALIDAÇÃO
    new_names = [new for _, new in changes]
    if len(new_names) != len(set(new_names)):
        st.error("⚠️ Conflito de nomes detectado!")
        st.stop()

    # EXECUTAR
    if st.button("🚀 Executar"):
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
                file_name="resultado.zip"
            )