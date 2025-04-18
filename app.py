import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo personalizado ---
st.markdown("""
    <style>
        /* Sidebar menu styling */
        .sidebar .stRadio > div {
            background: #fff;
            border-radius: 10px;
            padding: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .sidebar .stRadio label {
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .sidebar .stRadio input:checked + label {
            background: #f0f4f8;
            font-weight: bold;
        }
        .sidebar .stRadio label:hover {
            background: #f5f7fa;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            padding: 10px 0;
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
authenticator = stauth.Authenticate(credentials, "meu_app", "chave_super_secreta", cookie_expiry_days=1)
name, authenticated, username = authenticator.login("Login", "main")

# --- Funções auxiliares ---
def get_color(value, col_name, linha_zerada):
    if linha_zerada: return "#ffffff"
    mapping = {
        "Contagem Inicial": "lightgreen", "Compras": "lightgreen", "Total": "lightgreen",
        "Desp. Completo": "salmon", "Desp. Incompleto": "salmon", "Vendas": "khaki",
        "Contagem Atual": "lightblue", "Perda Operacional": "salmon", "Valor da Perda (R$)": "salmon"
    }
    return mapping.get(col_name, "white")

@st.cache_data
def carregar_planilha(file):
    df = pd.read_excel(file, sheet_name="Relatório")
    df.rename(columns={
        "Nome": "Produto", "Cont. Inicial": "Contagem Inicial", "Compras": "Compras",
        "Vendas": "Vendas", "Total": "Total", "Cont. Atual": "Contagem Atual",
        "Perda Operac.": "Perda Operacional", "Valor Perda (R$)": "Valor da Perda (R$)",
        "Desp. Comp.": "Desp. Completo", "Desp. Incom.": "Desp. Incompleto"
    }, inplace=True)
    df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")
    for col in ["Contagem Inicial","Compras","Vendas","Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')
    return df

# --- App principal ---
if authenticated:
    # Logout colocado ao final do menu
    st.sidebar.success(f"Bem-vindo, {name}!")

    # Menu lateral com estilo customizado e ícones
    options = {
        "Filtro de Dispersão": "📋 Filtro de Dispersão",
        "20 Maiores Perdas Operacionais": "📊 Maiores Perdas Operacionais",
        "20 Maiores Perdas em Valor": "💰 Maiores Perdas em Valor"
    }
    page = st.sidebar.radio("", list(options.values()))

    # Espaço antes do logout
    st.sidebar.markdown("---")
    authenticator.logout("🔒 Logout", "sidebar")

    st.markdown("<h1 style='text-align: center;'>📦 Meu App de Dispersão</h1>", unsafe_allow_html=True)

    # Envio de planilha no centro da página
    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if file:
        df = carregar_planilha(file)

        # Página de filtros
        if page == options["Filtro de Dispersão"]:
            st.markdown("<h2 style='text-align: center;'>📋 Filtro de Dispersão de Produtos</h2>", unsafe_allow_html=True)
            with st.expander("🔍 Filtros de visualização"):
                ex_crit = st.checkbox("Exibir Itens Críticos")
                ex_mensal = st.checkbox("Exibir Itens da Contagem Mensal")
                ex_todos = st.checkbox("Exibir Todos os Itens da Planilha")
                pesquisa = st.text_input("Pesquisar SKU ou Nome do Produto")

            skus_crit = ["P0035","P0018","11008874","P0043","11009087","P0044","P0051","11008864","P0045"]
            skus_mens = ["11008868","P0081","11008996","P0031","11008900","P0013","P0046","P0022","P0039"]

            df_filt = pd.DataFrame()
            if ex_crit: df_filt = pd.concat([df_filt, df[df['SKU'].isin(skus_crit)]])
            if ex_mensal: df_filt = pd.concat([df_filt, df[df['SKU'].isin(skus_mens)]])
            if ex_todos: df_filt = pd.concat([df_filt, df])
            if pesquisa:
                p = pesquisa.lower()
                df_filt = pd.concat([
                    df_filt,
                    df[df['SKU'].str.lower().str.contains(p) | df['Produto'].str.lower().str.contains(p)]
                ])
            df_filt.drop_duplicates(subset=["SKU"], inplace=True)

            if df_filt.empty:
                st.info("Nenhum filtro aplicado. Selecione uma opção ou pesquise.")
            else:
                cols = ["SKU","Produto","Contagem Inicial","Compras","Desp. Completo","Desp. Incompleto","Vendas","Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"]
                df_fin = df_filt[cols].copy()
                st.success("✅ Tabela filtrada com sucesso!")
                st.dataframe(df_fin)
                fig, ax = plt.subplots(figsize=(12,4))
                ax.axis('off')
                tbl = ax.table(cellText=df_fin.values, colLabels=df_fin.columns, loc='center', cellLoc='center')
                tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1.2,1.5)
                for (i,j), cell in tbl.get_celld().items():
                    if j < len(df_fin.columns) and i>0:
                        val = df_fin.iloc[i-1, j]
                        is_zero = all(v==0 or pd.isna(v) for v in df_fin.iloc[i-1,2:])
                        cell.set_facecolor(get_color(val, df_fin.columns[j], is_zero))
                st.pyplot(fig)
                buf = io.BytesIO(); df_fin.to_excel(buf, index=False)
                st.download_button("⬇️ Baixar Excel", buf.getvalue(), file_name="dispersao_filtrada.xlsx")
                img_buf = io.BytesIO(); fig.savefig(img_buf, format='png', dpi=200)
                st.download_button("⬇️ Baixar Imagem", img_buf.getvalue(), file_name="tabela_destaque.png")

        # Top 20 perdas operacionais
        elif page == options["20 Maiores Perdas Operacionais"]:
            st.markdown("<h2 style='text-align: center;'>📊 Top 20 Maiores Perdas Operacionais</h2>", unsafe_allow_html=True)
            top20 = df.nlargest(20, 'Perda Operacional')
            fig, ax = plt.subplots(figsize=(10,6))
            bars = ax.barh(top20['Produto'], top20['Perda Operacional'], color='salmon', edgecolor='darkred')
            ax.invert_yaxis(); ax.set_xlabel('Perda Operacional (unidades)', fontsize=12)
            ax.set_title('Top 20 Maiores Perdas Operacionais', fontsize=14)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            ax.bar_label(bars, labels=[f"{v:,.0f}" for v in top20['Perda Operacional']], padding=4, fontsize=10)
            plt.tight_layout(); st.pyplot(fig)

        # Top 20 perdas em valor
        elif page == options["20 Maiores Perdas em Valor"]:
            st.markdown("<h2 style='text-align: center;'>📊 Top 20 Maiores Perdas em Valor</h2>", unsafe_allow_html=True)
            top20v = df.nlargest(20, 'Valor da Perda (R$)')
            fig, ax = plt.subplots(figsize=(10,6))
            bars = ax.barh(top20v['Produto'], top20v['Valor da Perda (R$)'], color='salmon', edgecolor='darkred')
            ax.invert_yaxis(); ax.set_xlabel('Valor da Perda (R$)', fontsize=12)
            ax.set_title('Top 20 Maiores Perdas em Valor', fontsize=14)
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            ax.bar_label(bars, labels=[f"R$ {v:,.2f}" for v in top20v['Valor da Perda (R$)']], padding=4, fontsize=10)
            plt.tight_layout(); st.pyplot(fig)

    # Rodapé
    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)
elif authenticated is False:
    st.error("Usuário ou senha inválidos.")
elif authenticated is None:
    st.warning("Por favor, insira seu login.")
