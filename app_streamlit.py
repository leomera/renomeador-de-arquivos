import streamlit as st
import zipfile
import tempfile
import os

from logic import *

st.title("📦 Gerenciador de Imagens")

modo = st.radio(
    "Escolha a ação:",
    ["Renomear Imagens", "Remover Imagens"]
)

st.set_page_config(layout="wide")

# =========================
# CONFIGURAÇÃO DAS REGRAS
# =========================

if modo == "Renomear Imagens":
    st.header("🔤 Renomear Imagens")

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
    if st.button("🚀 Renomear arquivos"):
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

elif modo == "Remover Imagens":
    st.header("🗑️ Remover Imagens")

    uploaded_file = st.file_uploader("Envie um ZIP", type=["zip"])

    if uploaded_file:
        import zipfile
        import tempfile
        import os

        tmp = tempfile.mkdtemp()
        zip_path = os.path.join(tmp, uploaded_file.name)

        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())

        extract_dir = os.path.join(tmp, "files")
        os.mkdir(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        files = sorted(os.listdir(extract_dir))

        st.subheader("Arquivos encontrados:")
        st.write(files)

        # 👉 ESCOLHER A PARTIR DE QUAL REMOVER
        index = st.number_input(
            "Remover a partir de qual número?",
            min_value=1,
            step=1
        )

        # 🔍 PREVIEW
        files_to_remove = []
        for f in files:
            name, ext = os.path.splitext(f)

            if "_" in name:
                num_part = name.split("_")[-1]
                if num_part.isdigit() and int(num_part) >= index:
                    files_to_remove.append(f)

        st.subheader("🧾 Arquivos que serão removidos:")
        st.write(files_to_remove)

        # 🚀 EXECUTAR
        if st.button("🚀 Remover arquivos"):
            for f in files_to_remove:
                os.remove(os.path.join(extract_dir, f))

            output_zip = os.path.join(tmp, "resultado.zip")

            with zipfile.ZipFile(output_zip, 'w') as zipf:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        path = os.path.join(root, file)
                        zipf.write(path, os.path.relpath(path, extract_dir))

            with open(output_zip, "rb") as f:
                st.download_button(
                    "⬇️ Baixar resultado",
                    f,
                    file_name="Imagens removidas.zip"
                )