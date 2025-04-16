import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo do topo ---
st.markdown("""
    <style>
        .main {background-color: #f5f7fa;}
        .block-container {padding-top: 2rem;}
        h1 {color: #2c3e50;}
        .stCheckbox {margin-top: 0.5rem;}
        .css-1v3fvcr, .stTextInput, .stButton > button {
            font-size: 16px;
        }
        .stButton > button {
            background-color: #2ecc71;
            color: white;
            font-weight: bold;
            border-radius: 8px;
        }
        .stButton > button:hover {
            background-color: #27ae60;
        }
        /* Estilo para centralizar o conteúdo */
        .centralizado {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 80vh;  /* Ajuste para centralizar no meio da tela */
            text-align: center;
            flex-direction: column;
        }
        .footer {
            position: absolute;
            bottom: 10px;
            width: 100%;
            text-align: center;
            color: #888888;
            font-size: 14px;
            background-color: #f5f7fa;
            padding: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Autenticação ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Gabriel Wendell",  # Nome personalizado
            "password": stauth.Hasher(["1234"]).generate()[0]
        },
        "usuario": {
            "name": "Usuário",
            "password": stauth.Hasher(["senha"]).generate()[0]
        }
    }
}

autenticador = stauth.Authenticate(
    credentials,
    "meu_app",
    "chave_super_secreta",
    cookie_expiry_days=1
)

nome, autenticado, usuario = autenticador.login("🔐 Login", "main")

if autenticado:
    autenticador.logout("🚪 Logout", "sidebar")
    st.sidebar.markdown("## 👤 Usuário")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    # --- App principal ---
    st.markdown("## 📦 Filtro de Dispersão de Produtos")
    st.markdown("---")

    def get_color(value, col_name):
        if col_name in ["Contagem Inicial", "Compras", "Total"]:
            return "lightgreen"
        elif col_name in ["Desp. Completo", "Desp. Incompleto"]:
            return "salmon"
        elif col_name == "Vendas":
            return "khaki"
        elif col_name == "Contagem Atual":
            return "lightblue"
        elif col_name == "Perda Operacional":
            return "salmon" if value > 0 else "lightgreen"
        elif col_name == "Valor da Perda (R$)":
            return "salmon" if value > 0 else "lightgreen"
        else:
            return "white"

    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if file:
        df = pd.read_excel(file, header=2)
        df.rename(columns={
            "Nome": "Produto",
            "Cont. Inicial": "Contagem Inicial",
            "Compra s": "Compras",
            "Desp. Comp.": "Desp. Completo",
            "Desp. Incom.": "Desp. Incompleto",
            "Vendas": "Vendas",
            "Total": "Total",
            "Cont. Atual": "Contagem Atual",
            "Perda Opera c.": "Perda Operacional",
            "Valor Perda (R$)": "Valor da Perda (R$)"
        }, inplace=True)

        df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")

        skus_criticos = ["P0035", "P0018", "11008874", "P0043", "11009087", "P0044", "P0051", "11008864", "P0045"]
        skus_todos = ["11009706"]

        col1, col2 = st.columns(2)
        with col1:
            exibir_criticos = st.checkbox("🚨 Exibir Itens Críticos")
        with col2:
            exibir_todos = st.checkbox("📋 Exibir Todos os Itens")

        if exibir_criticos or exibir_todos:
            skus_filtrados = set()
            if exibir_criticos:
                skus_filtrados.update(skus_criticos)
            if exibir_todos:
                skus_filtrados.update(skus_todos)
            df_filtrado = df[df['SKU'].isin(skus_filtrados)]
        else:
            termo_busca = st.text_input("🔍 Buscar por SKU ou Nome do Produto").strip().lower()
            if termo_busca:
                df_filtrado = df[
                    df['SKU'].str.lower().str.contains(termo_busca) |
                    df['Produto'].str.lower().str.contains(termo_busca)
                ]
            else:
                df_filtrado = pd.DataFrame()

        if not df_filtrado.empty:
            colunas_desejadas = [
                "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo",
                "Desp. Incompleto", "Vendas", "Total", "Contagem Atual",
                "Perda Operacional", "Valor da Perda (R$)"
            ]
            df_final = df_filtrado[colunas_desejadas].copy()

            for col in df_final.columns[2:]:
                df_final[col] = df_final[col].astype(str).str.replace(",", ".").astype(float)

            st.success("✅ Tabela filtrada com sucesso!")
            st.dataframe(df_final)

            fig, ax = plt.subplots(figsize=(15, 4))
            ax.axis('off')

            table = ax.table(
                cellText=df_final.values,
                colLabels=df_final.columns,
                loc='center',
                cellLoc='center'
            )

            col_widths = {1: 0.3}
            for (row, col), cell in table.get_celld().items():
                if col in col_widths:
                    cell.set_width(col_widths[col])

            for i in range(len(df_final)):
                for j, col_name in enumerate(df_final.columns):
                    valor = df_final.iloc[i][col_name]
                    cor = get_color(valor, col_name)
                    table[(i + 1, j)].set_facecolor(cor)

            table.auto_set_font_size(False)
            table.set_fontsize(9.0)
            table.scale(1.2, 1.5)

            st.pyplot(fig)

            output_excel = io.BytesIO()
            df_final.to_excel(output_excel, index=False)
            st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name="dispersao_filtrada.xlsx")

            output_img = io.BytesIO()
            fig.savefig(output_img, format='png', dpi=200)
            st.download_button("🖼️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")
        else:
            st.info("🔎 Nenhum item encontrado. Marque um filtro ou digite algo para buscar.")

elif autenticado is False:
    st.error("❌ Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("🕵️ Por favor, insira seu login.")

# --- Rodapé fixado no meio da tela ---
st.markdown("""
    <div class="footer">
        ⓘ By <strong>Gabriel Wendell Menezes Santos</strong> — Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)
