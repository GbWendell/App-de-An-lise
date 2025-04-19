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
    """Define a cor da célula com base no valor da coluna"""
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

# --- Conteúdo principal ---
if autenticado:
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    st.markdown("<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>", unsafe_allow_html=True)

    # --- Filtros ---
    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    exibir_criticos = st.checkbox("Exibir Itens Críticos")
    exibir_todos = st.checkbox("Exibir Itens da Contagem Mensal")
    pesquisa = st.text_input("🔍 Pesquisar por SKU ou Nome do Produto")

    # --- Carregamento da planilha e filtragem ---
    if file:
        df = pd.read_excel(file, sheet_name="Relatório")

        # Renomeando as colunas para maior clareza
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

        # Filtrando os dados com base nos checkboxes e na pesquisa
        skus_criticos = ["P0035", "P0018", "11008874", "P0043", "11009087", "P0044", "P0051", "11008864", "P0045"]
        skus_todos = ["11008868", "P0081", "11008996", "P0031", "11008900", "P0013", "P0046", "P0022", "P0039", "P0056", "P0088", "P0087"]

        df_filtrado = pd.DataFrame()

        if exibir_criticos:
            df_filtrado = df[df['SKU'].isin(skus_criticos)]

        if exibir_todos:
            df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])

        if pesquisa:
            pesquisa = pesquisa.lower()
            resultado_pesquisa = df[df['SKU'].str.lower().str.contains(pesquisa) | df['Produto'].str.lower().str.contains(pesquisa)]
            df_filtrado = pd.concat([df_filtrado, resultado_pesquisa])

        # --- Exibindo a imagem de motivação caso não tenha filtro aplicado
        if df_filtrado.empty:
            st.info("Nenhum filtro foi aplicado. Escolha uma opção acima ou faça uma pesquisa.")
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            
            # Usando URL direta para garantir que a imagem seja carregada corretamente
            st.image("https://cdn.pixabay.com/photo/2015/12/08/00/32/business-1081802_960_720.jpg", width=600)
            
            st.markdown("<h3>Ser dono do seu próprio negócio é ter o controle da sua jornada. Não é sobre ter um emprego, é sobre construir um legado.</h3>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Exibindo a tabela filtrada e opções de download
        if not df_filtrado.empty:
            colunas_desejadas = [
                "SKU", "Produto", "Contagem Inicial", "Compras",
                "Desp. Completo", "Desp. Incompleto", "Vendas",
                "Total", "Contagem Atual", "Perda Operacional", "Valor da Perda (R$)"
            ]

            df_final = df_filtrado[colunas_desejadas].copy()

            # Convertendo valores para numéricos
            for col in df_final.columns[2:]:
                df_final[col] = pd.to_numeric(df_final[col].astype(str).str.replace(",", "."), errors='coerce')

            st.success("✅ Tabela filtrada com sucesso!")
            st.dataframe(df_final)

            # --- Exibindo a tabela em formato de gráfico
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.axis('off')
            table = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')

            # Ajustando a largura das colunas
            col_widths = {
                "SKU": 0.1,
                "Produto": 0.2,
                "Contagem Inicial": 0.1,
                "Compras": 0.1,
                "Desp. Completo": 0.1,
                "Desp. Incompleto": 0.1,
                "Vendas": 0.1,
                "Total": 0.1,
                "Contagem Atual": 0.1,
                "Perda Operacional": 0.1,
                "Valor da Perda (R$)": 0.15
            }

            for (row, col), cell in table.get_celld().items():
                if col < len(df_final.columns):
                    label = df_final.columns[col]
                    if label in col_widths:
                        cell.set_width(col_widths[label])

            # Ajustando as cores das células
            for i in range(len(df_final)):
                valores = df_final.iloc[i, 2:]
                linha_zerada = all(v == 0.0 or pd.isna(v) for v in valores)
                for j, col_name in enumerate(df_final.columns):
                    valor = df_final.iloc[i][col_name]
                    cor = get_color(valor, col_name, linha_zerada)
                    table[(i + 1, j)].set_facecolor(cor)

            table.auto_set_font_size(False)
            table.set_fontsize(9.0)
            table.scale(1.2, 1.5)

            st.pyplot(fig)

            # --- Opções de download
            output_excel = io.BytesIO()
            df_final.to_excel(output_excel, index=False)
            st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name="dispersao_filtrada.xlsx")

            output_img = io.BytesIO()
            fig.savefig(output_img, format='png', dpi=200)
            st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)

elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
