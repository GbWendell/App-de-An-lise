import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo ---
st.markdown("""
    <style>
        .main .block-container {
            padding: 2rem 3rem;
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- Autenticação ---
credentials = {
    "usernames": {
        "admin": {"name": "Gabriel Wendell", "password": stauth.Hasher(["1234"]).generate()[0]},
        "usuario": {"name": "Usuário", "password": stauth.Hasher(["senha"]).generate()[0]},
    }
}

authenticator = stauth.Authenticate(credentials, "meu_app", "chave_super_secreta", cookie_expiry_days=1)
nome, autenticado, usuario = authenticator.login("Login", "main")

if autenticado:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    st.markdown("<h1 style='text-align: center;'>📦 Filtro de Dispersão de Produtos</h1>", unsafe_allow_html=True)

    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])
    if file:
        df_raw = pd.read_excel(file, header=None)
        colunas_validas = ["SKU", "Nome", "Cont. Inicial", "Compra s", "Desp. Comp.", "Desp. Incom.", "Vendas", "Total", "Cont. Atual", "Perda Opera c.", "Valor Perda (R$)"]
        header_index = df_raw[df_raw.iloc[:, 0].astype(str).str.contains("SKU", na=False)].index.min()
        
        if pd.isna(header_index):
            st.error("❌ Cabeçalho com colunas como 'SKU' não foi encontrado na planilha.")
        else:
            df = pd.read_excel(file, header=header_index)
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
            
            # --- Filtros ---
            skus_criticos = ["P0035", "P0018", "11008874", "P0043", "11009087", "P0044", "P0051", "11008864", "P0045"]
            skus_todos = ["11008868", "P0081", "11008996", "P0031", "11008900", "P0013", "P0046", "P0022", "P0039", "P0056",
                          "P0088", "P0087", "P0067", "P0070", "P0068", "P0069", "P0062", "12000104", "12002708", "12000437",
                          "12000105", "12003040", "P0059", "P0060", "P0061", "P0063", "P0064", "12002606", "12002608",
                          "P0079", "P0007", "P0025", "11008881", "P0003", "P0040", "P0042", "85", "109", "P0001", "11008998",
                          "11008997", "P0010", "11009221", "11008888", "22005345", "P0015", "P0014", "P0002", "22005135",
                          "22005346", "P0047", "P0048", "P0019", "P0008", "P0005", "P0028", "22004844", "P0020", "P0053",
                          "P0037", "P0075", "P0036", "P0004", "P0026", "22004900", "22005122", "22004939", "P0013", "P0021",
                          "11009721", "11009722", "P0012", "P0024", "P0033", "P0011", "P0032", "P0030", "P0055",
                          "11009773", "11009960", "P0038", "11010051", "22005426", "22005427"]

            exibir_criticos = st.checkbox("Exibir Itens Críticos")
            exibir_todos = st.checkbox("Exibir Todos os Itens")
            pesquisa = st.text_input("🔍 Pesquisar por SKU ou Nome do Produto")

            df_filtrado = pd.DataFrame()
            if exibir_criticos:
                df_filtrado = df[df['SKU'].isin(skus_criticos)]
            if exibir_todos:
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])
            if pesquisa:
                pesquisa = pesquisa.lower()
                resultado = df[df['SKU'].str.lower().str.contains(pesquisa) | df['Produto'].str.lower().str.contains(pesquisa)]
                df_filtrado = pd.concat([df_filtrado, resultado])

            if not df_filtrado.empty:
                colunas_desejadas = [
                    "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo",
                    "Desp. Incompleto", "Vendas", "Total", "Contagem Atual",
                    "Perda Operacional", "Valor da Perda (R$)"
                ]

                try:
                    df_final = df_filtrado[colunas_desejadas].copy()
                    for col in df_final.columns[2:]:
                        df_final[col] = pd.to_numeric(df_final[col].astype(str).str.replace(",", "."), errors='coerce')
                    
                    st.success("✅ Tabela filtrada com sucesso!")
                    st.dataframe(df_final)

                    # Tabela como imagem
                    fig, ax = plt.subplots(figsize=(15, 4))
                    ax.axis('off')
                    tabela = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')
                    tabela.auto_set_font_size(False)
                    tabela.set_fontsize(9.0)
                    tabela.scale(1.2, 1.5)
                    st.pyplot(fig)

                    # Downloads
                    output_excel = io.BytesIO()
                    df_final.to_excel(output_excel, index=False)
                    st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name="dispersao_filtrada.xlsx")

                    output_img = io.BytesIO()
                    fig.savefig(output_img, format='png', dpi=200)
                    st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")

                except KeyError as e:
                    st.error(f"❌ Erro ao acessar colunas: {e}")
            else:
                st.info("🔍 Nenhum dado para exibir com os filtros aplicados.")

elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
