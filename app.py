import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo da página ---
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

# --- Funções auxiliares ---
def get_color(value, col_name, linha_zerada):
    if linha_zerada:
        return "#ffffff"
    elif col_name in ["Contagem Inicial", "Compras", "Total"]:
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
    return "white"

def plot_loss_operational(df):
    # Calculando as 20 maiores perdas operacionais
    df_sorted = df.sort_values(by="Perda Operacional", ascending=False).head(20)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df_sorted["Produto"], df_sorted["Perda Operacional"], color="salmon")
    ax.set_xlabel("Perda Operacional (R$)")
    ax.set_title("Top 20 Itens com Maiores Perdas Operacionais")
    st.pyplot(fig)

def plot_stock_difference(df):
    # Calculando as 20 maiores diferenças de estoque
    df['Diferenca Estoque'] = df['Total'] - df['Contagem Atual']
    df_sorted = df.sort_values(by="Diferenca Estoque", ascending=False).head(20)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df_sorted["Produto"], df_sorted["Diferenca Estoque"], color="lightblue")
    ax.set_xlabel("Diferença de Estoque")
    ax.set_title("Top 20 Maiores Diferenças de Estoque")
    st.pyplot(fig)

# --- Conteúdo principal ---
if autenticado:
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    st.markdown("<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>", unsafe_allow_html=True)

    # --- Menu lateral ---
    menu = st.sidebar.selectbox("Escolha uma opção", 
                               ["Filtros de Visualização", "Maiores Perdas Operacionais", "Maiores Diferenças de Estoque"])

    # --- Carregar a planilha e processar os dados ---
    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if file:
        df = pd.read_excel(file, sheet_name="Relatório")
        df.rename(columns={
            "Nome": "Produto",
            "Cont. Inicial": "Contagem Inicial",
            "Compras": "Compras",
            "Vendas": "Vendas",
            "Total": "Total",
            "Cont. Atual": "Contagem Atual",
            "Perda Operac.": "Perda Operacional",
            "Valor Perda (R$)": "Valor da Perda (R$)",
            "Desp. Comp.": "Desp. Completo",
            "Desp. Incom.": "Desp. Incompleto"
        }, inplace=True)
        df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")

        # --- Filtros de Visualização ---
        if menu == "Filtros de Visualização":
            with st.expander("🔍 Filtros de visualização"):
                exibir_criticos = st.checkbox("Exibir Itens Críticos")
                exibir_contagem_mensal = st.checkbox("Exibir Itens da Contagem Mensal")
                exibir_todos_itens = st.checkbox("Exibir Todos os Itens da Planilha")
                pesquisa = st.text_input("Pesquisar por SKU ou Nome do Produto")

            df_filtrado = pd.DataFrame()

            # Filtros
            if exibir_criticos:
                skus_criticos = ["P0035", "P0018", "11008874", "P0043", "11009087", "P0044", "P0051", "11008864", "P0045"]
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
            if exibir_contagem_mensal:
                skus_todos = ["11008868", "P0081", "11008996", "P0031", "11008900", "P0013", "P0046", "P0022", "P0039", "P0056", "P0088", "P0087", "P0067"]
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])
            if exibir_todos_itens:
                df_filtrado = pd.concat([df_filtrado, df])
            if pesquisa:
                pesquisa = pesquisa.lower()
                resultado_pesquisa = df[
                    df['SKU'].str.lower().str.contains(pesquisa) |
                    df['Produto'].str.lower().str.contains(pesquisa)
                ]
                df_filtrado = pd.concat([df_filtrado, resultado_pesquisa])

            df_filtrado.drop_duplicates(subset=["SKU"], inplace=True)

            if not df_filtrado.empty:
                colunas_desejadas = [
                    "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo", "Desp. Incompleto", 
                    "Vendas", "Total", "Contagem Atual", "Perda Operacional", "Valor da Perda (R$)"
                ]

                df_final = df_filtrado[colunas_desejadas].copy()

                for col in df_final.columns[2:]:
                    df_final[col] = pd.to_numeric(df_final[col].astype(str).str.replace(",", "."), errors='coerce')

                st.success("✅ Tabela filtrada com sucesso!")
                st.dataframe(df_final)

        elif menu == "Maiores Perdas Operacionais":
            plot_loss_operational(df)

        elif menu == "Maiores Diferenças de Estoque":
            plot_stock_difference(df)

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)

elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
