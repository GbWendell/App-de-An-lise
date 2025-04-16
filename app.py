import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth
from datetime import datetime

# --- Estilo customizado ---
st.markdown("""
    <style>
        body {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main .block-container {
            padding: 2rem 3rem;
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }
        h1 {
            font-weight: 700;
            color: #2c3e50;
        }
        .stButton>button {
            border-radius: 12px;
            background-color: #2c3e50;
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #34495e;
        }
        .stDownloadButton>button {
            border-radius: 8px;
            background-color: #16a085;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            margin-right: 10px;
        }
        .stDownloadButton>button:hover {
            background-color: #138d75;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: none;
            text-align: center;
            padding: 10px 0;
        }
        .footer span {
            font-size: 14px;
            color: grey;
        }
    </style>
""", unsafe_allow_html=True)

# --- Autenticação ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Gabriel Wendell",
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

nome, autenticado, usuario = autenticador.login("Login", "main")

if autenticado:
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    st.markdown("""<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>""", unsafe_allow_html=True)

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
        skus_todos = [ ... ]  # mesma lista de antes (mantida para brevidade)

        exibir_criticos = st.checkbox("Exibir Itens Críticos")
        exibir_todos = st.checkbox("Exibir Todos os Itens")

        pesquisa = st.text_input("🔍 Pesquisar por SKU ou Nome do Produto")

        df_filtrado = pd.DataFrame()

        if exibir_criticos:
            df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
        if exibir_todos:
            df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])
        if pesquisa:
            pesquisa = pesquisa.lower()
            resultado_pesquisa = df[df['SKU'].str.lower().str.contains(pesquisa) | df['Produto'].str.lower().str.contains(pesquisa)]
            df_filtrado = pd.concat([df_filtrado, resultado_pesquisa])

        df_filtrado = df_filtrado.drop_duplicates(subset=["SKU"])

        if df_filtrado.empty and not pesquisa:
            st.info("👈 Selecione ao menos um filtro ou faça uma pesquisa para visualizar os dados.")

        if not df_filtrado.empty:
            colunas_desejadas = [
                "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo",
                "Desp. Incompleto", "Vendas", "Total", "Contagem Atual",
                "Perda Operacional", "Valor da Perda (R$)"
            ]
            df_final = df_filtrado[colunas_desejadas].copy()

            for col in df_final.columns[2:]:
                df_final[col] = pd.to_numeric(df_final[col].astype(str).str.replace(",", "."), errors='coerce')

            st.success("✅ Tabela filtrada com sucesso!")
            st.dataframe(df_final)

            linhas = len(df_final)
            altura = 1 + linhas * 0.5
            fig, ax = plt.subplots(figsize=(15, altura))
            ax.axis('off')

            table = ax.table(
                cellText=df_final.values,
                colLabels=df_final.columns,
                loc='center',
                cellLoc='center'
            )

            for i in range(len(df_final)):
                for j, col_name in enumerate(df_final.columns):
                    valor = df_final.iloc[i][col_name]
                    cor = get_color(valor, col_name)
                    table[(i + 1, j)].set_facecolor(cor)

            table.auto_set_font_size(False)
            table.set_fontsize(9.0)
            table.scale(1.2, 1.5)

            plt.tight_layout(pad=2)

            # Nome do arquivo com data
            hoje = datetime.today().strftime("%Y-%m-%d")

            # Excel
            output_excel = io.BytesIO()
            df_final.to_excel(output_excel, index=False)
            st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name=f"dispersao_filtrada_{hoje}.xlsx")

            # Imagem
            output_img = io.BytesIO()
            fig.savefig(output_img, format='png', dpi=200, bbox_inches='tight')
            st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name=f"tabela_destaque_{hoje}.png")

    st.markdown("""<div class="footer"><span>By Gabriel Wendell Menezes Santos</span></div>""", unsafe_allow_html=True)

elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
