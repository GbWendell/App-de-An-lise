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
        "usuario": {"name": "Usuário", "password": stauth.Hasher(["senha"]).generate()[0]}
    }
}
autenticador = stauth.Authenticate(credentials, "meu_app", "chave_super_secreta", cookie_expiry_days=1)
nome, autenticado, usuario = autenticador.login("Login", "main")

# --- Função para colorir a tabela ---
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

# --- Conteúdo principal ---
if autenticado:
    # Logout e boas-vindas
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    # Menu de navegação
    st.sidebar.markdown("## Menu")
    opcao = st.sidebar.radio("", ["Filtro de Dispersão", "Maiores Perdas Operacionais"] )

    # Upload da planilha
    file = st.sidebar.file_uploader("📁 Envie a planilha (Excel)", type=["xlsx"])

    # Carregar e preparar dataframe se houver arquivo
    df = None
    if file:
        df = pd.read_excel(file, sheet_name="Relatório")
        df.rename(columns={
            "Nome": "Produto", "Cont. Inicial": "Contagem Inicial", "Compras": "Compras",
            "Vendas": "Vendas", "Total": "Total", "Cont. Atual": "Contagem Atual",
            "Perda Operac.": "Perda Operacional", "Valor Perda (R$)": "Valor da Perda (R$)",
            "Desp. Comp.": "Desp. Completo", "Desp. Incom.": "Desp. Incompleto"
        }, inplace=True)
        df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")

    # Título principal
    st.markdown("<h1 style='text-align: center;'>📦 Aplicativo de Dispersão de Produtos</h1>", unsafe_allow_html=True)

    # --- Filtro de Dispersão ---
    if opcao == "Filtro de Dispersão":
        if not df:
            st.info("Envie a planilha para começar a análise.")
        else:
            # Seleção de filtros
            with st.expander("🔍 Filtros de visualização"):
                exibir_criticos = st.checkbox("Exibir Itens Críticos")
                exibir_contagem = st.checkbox("Exibir Itens da Contagem Mensal")
                exibir_todos = st.checkbox("Exibir Todos os Itens da Planilha")
                pesquisa = st.text_input("🔎 Pesquisar SKU ou Nome")

            # Listas de SKU
            skus_criticos = ["P0035","P0018","11008874","P0043","11009087","P0044","P0051","11008864","P0045"]
            skus_contagem = ["11008868","P0081","11008996","P0031","11008900","P0013","P0046","P0022","P0039"]

            # Filtragem dos dados
            df_filtrado = pd.DataFrame()
            if exibir_criticos: df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
            if exibir_contagem: df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_contagem)]])
            if exibir_todos: df_filtrado = pd.concat([df_filtrado, df])
            if pesquisa:
                pesquisa_lower = pesquisa.lower()
                df_filtrado = pd.concat([
                    df_filtrado,
                    df[df['SKU'].str.lower().str.contains(pesquisa_lower) |
                       df['Produto'].str.lower().str.contains(pesquisa_lower)]
                ])
            df_filtrado.drop_duplicates(subset=["SKU"], inplace=True)

            # Se não filtrou nada, mostrar imagem motivacional
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
                # Exibir tabela e download
                colunas = ["SKU","Produto","Contagem Inicial","Compras","Desp. Completo",
                           "Desp. Incompleto","Vendas","Total","Contagem Atual",
                           "Perda Operacional","Valor da Perda (R$)"]
                df_final = df_filtrado[colunas].copy()
                for c in df_final.columns[2:]:
                    df_final[c] = pd.to_numeric(df_final[c].astype(str).str.replace(",","."), errors='coerce')
                st.dataframe(df_final)
                # Geração da tabela colorida
                fig, ax = plt.subplots(figsize=(12,4))
                ax.axis('off')
                tab = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')
                for (r, c), cell in tab.get_celld().items():
                    if c < len(df_final.columns):
                        label = df_final.columns[c]
                        cor = get_color(df_final.iloc[r-1][label], label, all(val==0 or pd.isna(val) for val in df_final.iloc[r-1,2:]))
                        cell.set_facecolor(cor)
                tab.auto_set_font_size(False)
                tab.set_fontsize(9)
                tab.scale(1.2,1.5)
                st.pyplot(fig)

                # Download
                buf = io.BytesIO()
                df_final.to_excel(buf, index=False)
                st.download_button("⬇️ Baixar Excel", buf.getvalue(), file_name="dispersao_filtrada.xlsx")
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', dpi=200)
                st.download_button("⬇️ Baixar Imagem", img_buf.getvalue(), file_name="tabela_destaque.png")

    # --- Maiores Perdas Operacionais ---
    elif opcao == "Maiores Perdas Operacionais":
        if not df:
            st.info("Envie a planilha para visualizar as maiores perdas.")
        else:
            # Selecionar top 9 perdas
            df_plot = df.copy()
            df_plot['Perda Operacional'] = pd.to_numeric(df_plot['Perda Operacional'].astype(str).str.replace(",","."), errors='coerce')
            top9 = df_plot.nlargest(9, 'Perda Operacional')

            # Gráfico de barras horizontais
            fig, ax = plt.subplots(figsize=(8,6))
            ax.barh(top9['Produto'], top9['Perda Operacional'])
            ax.invert_yaxis()
            ax.set_xlabel('Perda Operacional')
            ax.set_title('Top 9 Maiores Perdas Operacionais')
            st.pyplot(fig)

    # Rodapé
    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)
elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
