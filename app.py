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

# --- Função de cores ---
def get_color(value, col_name, linha_zerada):
    if linha_zerada:
        return '#ffffff'
    if col_name in ['Contagem Inicial', 'Compras', 'Total']:
        return 'lightgreen'
    if col_name in ['Desp. Completo', 'Desp. Incompleto']:
        return 'salmon'
    if col_name == 'Vendas':
        return 'khaki'
    if col_name == 'Contagem Atual':
        return 'lightblue'
    if col_name == 'Perda Operacional':
        return 'salmon' if value > 0 else 'lightgreen'
    if col_name == 'Valor da Perda (R$)':
        return 'salmon' if value > 0 else 'lightgreen'
    return 'white'

# --- Conteúdo principal ---
if autenticado:
    autenticador.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {nome}!")

    # Menu de navegação
    page = st.sidebar.selectbox(
        "Navegação",
        ["Filtro Principal", "Maiores Perdas Operacionais"]
    )

    st.markdown("<h1 style='text-align: center;'>📦 Dispersão de Produtos</h1>", unsafe_allow_html=True)

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

        # Seção de acordo com a página selecionada
        if page == "Filtro Principal":
            # Filtros
            with st.expander("🔍 Filtros de visualização"):
                exibir_criticos = st.checkbox("Exibir Itens Críticos")
                exibir_contagem_mensal = st.checkbox("Exibir Itens da Contagem Mensal")
                exibir_todos = st.checkbox("Exibir Todos os Itens da Planilha")
                pesquisa = st.text_input("Pesquisar por SKU ou Nome do Produto")

            skus_criticos = ["P0035","P0018","11008874","P0043","11009087","P0044","P0051","11008864","P0045"]
            skus_todos = ["11008868","P0081","11008996","P0031","11008900","P0013","P0046","P0022","P0039","P0056","P0088","P0087"]

            df_filtrado = pd.DataFrame()
            if exibir_criticos:
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_criticos)]])
            if exibir_contagem_mensal:
                df_filtrado = pd.concat([df_filtrado, df[df['SKU'].isin(skus_todos)]])
            if exibir_todos:
                df_filtrado = pd.concat([df_filtrado, df])
            if pesquisa:
                query = pesquisa.lower()
                resultado = df[df['SKU'].str.lower().str.contains(query) | df['Produto'].str.lower().str.contains(query)]
                df_filtrado = pd.concat([df_filtrado, resultado])
            df_filtrado.drop_duplicates(subset=['SKU'], inplace=True)

            if df_filtrado.empty:
                st.info("Nenhum filtro aplicado. Selecione uma opção acima ou pesquise.")
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                st.image("https://cdn.pixabay.com/photo/2015/12/08/00/32/business-1081802_960_720.jpg", width=600)
                st.markdown("<h3>Ser dono do seu próprio negócio é ter o controle da sua jornada.</h3>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Exibe tabela e gráfico
                colunas = [
                    "SKU","Produto","Contagem Inicial","Compras",
                    "Desp. Completo","Desp. Incompleto","Vendas",
                    "Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"
                ]
                df_final = df_filtrado[colunas].copy()
                for c in df_final.columns[2:]:
                    df_final[c] = pd.to_numeric(df_final[c].astype(str).str.replace(",","."), errors='coerce')
                st.success("✅ Tabela filtrada com sucesso!")
                st.dataframe(df_final)

                fig, ax = plt.subplots(figsize=(12,4))
                ax.axis('off')
                tbl = ax.table(cellText=df_final.values, colLabels=df_final.columns, loc='center', cellLoc='center')
                widths = {col:0.1 for col in df_final.columns}
                widths['Produto']=0.2; widths['Valor da Perda (R$)']=0.15
                for (i,j), cell in tbl.get_celld().items():
                    if j < len(df_final.columns):
                        lbl = df_final.columns[j]
                        cell.set_width(widths.get(lbl,0.1))
                for i in range(len(df_final)):
                    z = all(v==0.0 or pd.isna(v) for v in df_final.iloc[i,2:])
                    for j, col in enumerate(df_final.columns):
                        cval = df_final.iloc[i][col]
                        tbl[(i+1,j)].set_facecolor(get_color(cval, col, z))
                tbl.auto_set_font_size(False); tbl.set_fontsize(9.0); tbl.scale(1.2,1.5)
                st.pyplot(fig)

                # Downloads
                buf_xl = io.BytesIO(); df_final.to_excel(buf_xl, index=False)
                st.download_button("⬇️ Baixar Excel", buf_xl.getvalue(), file_name="dispersao_filtrada.xlsx")
                buf_img = io.BytesIO(); fig.savefig(buf_img, format='png', dpi=200)
                st.download_button("⬇️ Baixar Imagem da Tabela", buf_img.getvalue(), file_name="tabela_destaque.png")

        elif page == "Maiores Perdas Operacionais":
            # Calcula as 9 maiores perdas e exibe gráfico
            df_num = df.copy()
            df_num['Perda Operacional'] = pd.to_numeric(df_num['Perda Operacional'].astype(str).str.replace(',','.'), errors='coerce')
            top9 = df_num.nlargest(9, 'Perda Operacional')[['SKU','Produto','Perda Operacional']]
            st.subheader("🛠️ Top 9 Maiores Perdas Operacionais")
            if top9.empty:
                st.info("Sem dados para exibir.")
            else:
                fig2, ax2 = plt.subplots()
                ax2.bar(top9['Produto'], top9['Perda Operacional'])
                ax2.set_xticklabels(top9['Produto'], rotation=45, ha='right')
                ax2.set_ylabel('Perda Operacional')
                st.pyplot(fig2)

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)
elif autenticado is False:
    st.error("Usuário ou senha inválidos.")
elif autenticado is None:
    st.warning("Por favor, insira seu login.")
