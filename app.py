import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo da página ---
st.markdown("""
    <style>
        body { background-color: #f5f7fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .main .block-container { padding: 2rem 3rem; background-color: white; border-radius: 15px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); }
        h1 { font-weight: 700; color: #2c3e50; }
        .stButton>button { border-radius: 12px; background-color: #2c3e50; color: white; border: none; padding: 0.6rem 1.2rem; transition: background-color 0.3s; }
        .stButton>button:hover { background-color: #34495e; }
        .stDownloadButton>button { border-radius: 8px; background-color: #16a085; color: white; border: none; padding: 0.5rem 1rem; margin-right: 10px; }
        .stDownloadButton>button:hover { background-color: #138d75; }
        .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: none; text-align: center; padding: 10px 0; }
        .footer span { font-size: 14px; color: grey; }
    </style>
""", unsafe_allow_html=True)

# --- Funções de autenticação ---
def autenticar_usuario():
    credentials = {
        "usernames": {
            "admin": { "name": "Gabriel Wendell", "password": stauth.Hasher(["1234"]).generate()[0] },
            "usuario": { "name": "Usuário", "password": stauth.Hasher(["senha"]).generate()[0] }
        }
    }

    autenticador = stauth.Authenticate(
        credentials,
        "meu_app",
        "chave_super_secreta",
        cookie_expiry_days=1
    )

    return autenticador.login("Login", "main")

# --- Funções auxiliares ---
def get_color(value, col_name, linha_zerada):
    if linha_zerada:
        return "#ffffff"
    color_map = {
        "Contagem Inicial": "lightgreen", "Compras": "lightgreen", "Total": "lightgreen",
        "Desp. Completo": "salmon", "Desp. Incompleto": "salmon", "Vendas": "khaki",
        "Contagem Atual": "lightblue", "Perda Operacional": "salmon", "Valor da Perda (R$)": "salmon"
    }
    if col_name in color_map:
        return color_map[col_name]
    return "white"

def carregar_arquivo(file):
    df = pd.read_excel(file, sheet_name="Relatório")
    df.rename(columns={
        "Nome": "Produto", "Cont. Inicial": "Contagem Inicial", "Compras": "Compras", "Vendas": "Vendas",
        "Total": "Total", "Cont. Atual": "Contagem Atual", "Perda Operac.": "Perda Operacional",
        "Valor Perda (R$)": "Valor da Perda (R$)", "Desp. Comp.": "Desp. Completo", "Desp. Incom.": "Desp. Incompleto"
    }, inplace=True)
    df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")
    return df

def aplicar_filtros(df, filtros, skus_criticos, skus_todos):
    df_filtrado = pd.DataFrame()

    if filtros.get("criticos"):
        df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
    if filtros.get("mensal"):
        df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])
    if filtros.get("todos"):
        df_filtrado = pd.concat([df_filtrado, df])
    if filtros.get("pesquisa"):
        pesquisa = filtros.get("pesquisa").lower()
        df_filtrado = pd.concat([df_filtrado, df[
            df['SKU'].str.lower().str.contains(pesquisa) | df['Produto'].str.lower().str.contains(pesquisa)
        ]])

    df_filtrado.drop_duplicates(subset=["SKU"], inplace=True)
    return df_filtrado

# --- Conteúdo principal ---
nome, autenticado, usuario = autenticar_usuario()

if autenticado:
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    st.markdown("<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>", unsafe_allow_html=True)

    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if file:
        df = carregar_arquivo(file)

        # Skus críticos e outros
        skus_criticos = ["P0035", "P0018", "11008874", "P0043", "11009087", "P0044", "P0051", "11008864", "P0045"]
        skus_todos = ["11008868", "P0081", "11008996", "P0031", "11008900", "P0013", "P0046", "P0022", "P0039", "P0056", "P0088", "P0087"]

        with st.expander("🔍 Filtros de visualização"):
            filtros = {
                "criticos": st.checkbox("Exibir Itens Críticos"),
                "mensal": st.checkbox("Exibir Itens da Contagem Mensal"),
                "todos": st.checkbox("Exibir Todos os Itens da Planilha"),
                "pesquisa": st.text_input("Pesquisar por SKU ou Nome do Produto")
            }

        df_filtrado = aplicar_filtros(df, filtros, skus_criticos, skus_todos)

        if not df_filtrado.empty:
            colunas_desejadas = ["SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo", "Desp. Incompleto", "Vendas", "Total", "Contagem Atual", "Perda Operacional", "Valor da Perda (R$)"]
            df_final = df_filtrado[colunas_desejadas].copy()
            df_final = df_final.apply(pd.to_numeric, errors='coerce')

            st.success("✅ Tabela filtrada com sucesso!")
            st.dataframe(df_final)

            # Gerar gráfico e tabelas
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.axis('off')
            table = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9.0)
            table.scale(1.2, 1.5)
            st.pyplot(fig)

            # Download buttons
            output_excel = io.BytesIO()
            df_final.to_excel(output_excel, index=False)
            st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name="dispersao_filtrada.xlsx")
            output_img = io.BytesIO()
            fig.savefig(output_img, format='png', dpi=200)
            st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)

else:
    st.error("Usuário ou senha inválidos." if autenticado is False else "Por favor, insira seu login.")
