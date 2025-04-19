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
        "admin": {"name": "Gabriel Wendell", "password": stauth.Hasher(["1234"]).generate()[0]},
        "usuario": {"name": "Usuário",        "password": stauth.Hasher(["senha"]).generate()[0]}
    }
}
authenticator = stauth.Authenticate(credentials, "meu_app", "chave_super_secreta", cookie_expiry_days=1)
name, authenticated, username = authenticator.login("Login", "main")

# --- Funções auxiliares ---
def get_color(value, col_name, linha_zerada):
    if linha_zerada:
        return "#ffffff"
    if col_name in ["Contagem Inicial", "Compras", "Total"]:
        return "lightgreen"
    if col_name in ["Desp. Completo", "Desp. Incompleto"]:
        return "salmon"
    if col_name == "Vendas":
        return "khaki"
    if col_name == "Contagem Atual":
        return "lightblue"
    if col_name == "Perda Operacional":
        return "salmon" if value > 0 else "lightgreen"
    if col_name == "Valor da Perda (R$)":
        return "salmon" if value > 0 else "lightgreen"
    return "white"

# --- Função de carregamento ---
def carregar_planilha(file):
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
    # converter colunas numéricas
    for col in ['Contagem Inicial','Compras','Vendas','Total','Contagem Atual','Perda Operacional','Valor da Perda (R$)']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')
    return df

# --- Conteúdo principal ---
if authenticated:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name}!")
    
    # Menu lateral com três opções
    page = st.sidebar.radio("Navegação", [
        "Filtros de Dispersão",
        "20 Maiores Perdas Operacionais",
        "20 Maiores Perdas em Valor",
    ])

    # Upload de arquivo na sidebar
    file = st.sidebar.file_uploader("📁 Envie a planilha (Excel)", type=["xlsx"])

    # Se não enviou arquivo, mostrar imagem motivacional
    if not file:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2015/12/08/00/32/business-1081802_960_720.jpg", width=600)
        st.markdown(
            "<h3>Ser dono do seu próprio negócio é ter o controle da sua jornada. Não é sobre ter um emprego, é sobre construir um legado.</h3>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Carregar dados
        df = carregar_planilha(file)
        
        if page == "Filtros de Dispersão":
            st.markdown("<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>", unsafe_allow_html=True)
            # Filtros expander
            with st.expander("🔍 Filtros de visualização"):
                exibir_criticos = st.checkbox("Exibir Itens Críticos")
                exibir_contagem_mensal = st.checkbox("Exibir Itens da Contagem Mensal")
                exibir_todos_itens = st.checkbox("Exibir Todos os Itens da Planilha")
                pesquisa = st.text_input("Pesquisar por SKU ou Nome do Produto")

            # SKUs fixos
            skus_criticos = ["P0035","P0018","11008874","P0043","11009087","P0044","P0051","11008864","P0045"]
            skus_mensal = ["11008868","P0081","11008996","P0031","11008900","P0013","P0046","P0022","P0039"]

            df_filtrado = pd.DataFrame()
            if exibir_criticos:
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
            if exibir_contagem_mensal:
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_mensal)]])
            if exibir_todos_itens:
                df_filtrado = pd.concat([df_filtrado, df])
            if pesquisa:
                lower = pesquisa.lower()
                df_filtrado = pd.concat([
                    df_filtrado,
                    df[df['SKU'].str.lower().str.contains(lower) | df['Produto'].str.lower().str.contains(lower)]
                ])
            df_filtrado.drop_duplicates(subset=["SKU"], inplace=True)

            # Se vazio, imagem motivacional
            if df_filtrado.empty:
                st.info("Nenhum filtro aplicado.")
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                st.image("https://cdn.pixabay.com/photo/2015/12/08/00/32/business-1081802_960_720.jpg", width=600)
                st.markdown(
                    "<h3>Ser dono do seu próprio negócio é ter o controle da sua jornada. Não é sobre ter um emprego, é sobre construir um legado.</h3>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Exibir tabela e downloads
                colunas = ["SKU","Produto","Contagem Inicial","Compras","Desp. Completo","Desp. Incompleto","Vendas","Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"]
                df_final = df_filtrado[colunas].copy()
                st.success("✅ Tabela filtrada com sucesso!")
                st.dataframe(df_final)

                fig, ax = plt.subplots(figsize=(12,4))
                ax.axis('off')
                table = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')
                for (i,j), cell in table.get_celld().items():
                    if j < len(df_final.columns):
                        color = get_color(df_final.iloc[i-1, j], df_final.columns[j], all(v==0 or pd.isna(v) for v in df_final.iloc[i-1,2:]))
                        cell.set_facecolor(color)
                table.auto_set_font_size(False); table.set_fontsize(9); table.scale(1.2,1.5)
                st.pyplot(fig)

                buf = io.BytesIO()
                df_final.to_excel(buf, index=False)
                st.download_button("⬇️ Baixar Excel", buf.getvalue(), file_name="dispersao_filtrada.xlsx")
                img_buf = io.BytesIO(); fig.savefig(img_buf, format='png', dpi=200)
                st.download_button("⬇️ Baixar Imagem", img_buf.getvalue(), file_name="tabela_destaque.png")

        elif page == "20 Maiores Perdas Operacionais":
            st.markdown("<h1 style='text-align: center;'>📊 Top 20 Maiores Perdas Operacionais</h1>", unsafe_allow_html=True)
            top20 = df.nlargest(20, 'Perda Operacional')
            fig, ax = plt.subplots(figsize=(8,6))
            ax.barh(top20['Produto'], top20['Perda Operacional'], color='salmon')
            ax.invert_yaxis(); ax.set_xlabel('Perda Operacional'); ax.set_title('Top 20 Maiores Perdas Operacionais')
            st.pyplot(fig)

        elif page == "20 Maiores Perdas em Valor":
            st.markdown("<h1 style='text-align: center;'>📊 Top 20 Maiores Perdas em Valor</h1>", unsafe_allow_html=True)
            top20v = df.nlargest(20, 'Valor da Perda (R$)')
            fig, ax = plt.subplots(figsize=(8,6))
            ax.barh(top20v['Produto'], top20v['Valor da Perda (R$)'], color='salmon')
            ax.invert_yaxis(); ax.set_xlabel('Valor da Perda (R$)'); ax.set_title('Top 20 Maiores Perdas em Valor')
            st.pyplot(fig)

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)
elif authenticated is False:
    st.error("Usuário ou senha inválidos.")
elif authenticated is None:
    st.warning("Por favor, insira seu login.")
