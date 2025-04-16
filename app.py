import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

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

    # --- Estilo ---
    st.markdown("""
        <style>
            .main { background-color: #f5f7fa; }
            .stButton>button { background-color: #008CBA; color: white; }
            .stDownloadButton>button { background-color: #4CAF50; color: white; }
            .footer {
                position: fixed;
                left: 10px;
                bottom: 10px;
                font-size: 12px;
                color: #888;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Título ---
    st.title("📦 Filtro de Dispersão de Produtos")

    def get_color(value, col_name):
        if col_name in ["Contagem Inicial", "Compras", "Total"]:
            return "lightgreen"
        elif col_name in ["Desp. Completo", "Desp. Incompleto"]:
            return "salmon"
        elif col_name == "Vendas":
            return "khaki"
        elif col_name == "Contagem Atual":
            return "lightblue"
        elif col_name in ["Perda Operacional", "Valor da Perda (R$)"]:
            return "salmon" if value > 0 else "lightgreen"
        else:
            return "white"

    # --- Upload ---
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

        exibir_criticos = st.checkbox("Exibir Itens Críticos")
        exibir_todos = st.checkbox("Exibir Todos os Itens")

        skus_selecionados = set()
        if exibir_criticos:
            skus_selecionados.update(skus_criticos)
        if exibir_todos:
            skus_selecionados.update(skus_todos)

        if skus_selecionados:
            colunas_desejadas = [
                "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo",
                "Desp. Incompleto", "Vendas", "Total", "Contagem Atual",
                "Perda Operacional", "Valor da Perda (R$)"
            ]
            df_final = df[df['SKU'].isin(skus_selecionados)][colunas_desejadas].copy()

            for col in df_final.columns[2:]:
                df_final[col] = pd.to_numeric(
                    df_final[col].astype(str).str.replace(",", ".", regex=False),
                    errors='coerce'
                )

            st.success("✅ Tabela filtrada com sucesso!")
            st.dataframe(df_final)

            # --- Gráfico ---
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
            st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")

    # --- Rodapé ---
    st.markdown('<div class="footer">By Gabriel Wendell Menezes Santos</div>', unsafe_allow_html=True)

elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
