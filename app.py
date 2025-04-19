import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit_authenticator as stauth

# --- Estilo personalizado ---
st.markdown("""
    <style>
        .sidebar .stRadio > div { background: #fff; border-radius: 10px; padding: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .sidebar .stRadio label { display: flex; align-items: center; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
        .sidebar .stRadio input:checked + label { background: #f0f4f8; font-weight: bold; }
        .sidebar .stRadio label:hover { background: #f5f7fa; }
        .footer { position: fixed; bottom: 0; left: 0; width: 100%; text-align: center; padding: 10px 0; color: grey; }
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
user_name, authenticated, username = authenticator.login("Login", "main")

# --- Helpers ---
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
    # converter colunas numéricas
    for col in ["Contagem Inicial","Compras","Vendas","Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')
    return df

# cores tabela
def get_color(value, col_name, linha_zero):
    if linha_zero: return "#ffffff"
    mapping = {"Contagem Inicial":"lightgreen","Compras":"lightgreen","Total":"lightgreen",
               "Desp. Completo":"salmon","Desp. Incompleto":"salmon","Vendas":"khaki",
               "Contagem Atual":"lightblue","Perda Operacional":"salmon","Valor da Perda (R$)":"salmon"}
    return mapping.get(col_name, "white")

# --- App ---
if authenticated:
    st.sidebar.success(f"Bem-vindo, {user_name}!")
    # Menu
    menu_items = ["Filtro de Dispersão","KPIs","Comparar Produtos","20 Maiores Perdas Operacionais","20 Maiores Perdas em Valor"]
    page = st.sidebar.radio("", menu_items)
    st.sidebar.markdown("---")
    authenticator.logout("🔒 Logout","sidebar")

    st.markdown("<h1 style='text-align:center;'>📦 Meu App de Dispersão</h1>", unsafe_allow_html=True)
    file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if not file:
        st.info("Faça upload da planilha para iniciar.")
    else:
        df = carregar_planilha(file)

        if page == "Filtro de Dispersão":
            st.markdown("<h2>Filtro de Dispersão de Produtos</h2>", unsafe_allow_html=True)
            with st.expander("🔍 Filtros"):
                ex_crit = st.checkbox("Exibir Itens Críticos")
                ex_mens = st.checkbox("Exibir Itens da Contagem Mensal")
                ex_all = st.checkbox("Exibir Todos os Itens")
                search = st.text_input("Pesquisar SKU ou Produto")
            sk_crit = ["P0035","P0018","11008874","P0043","11009087","P0044","P0051","11008864","P0045"]
            sk_mens = ["11008868","P0081","11008996","P0031","11008900","P0013","P0046","P0022","P0039"]
            df_f = pd.DataFrame()
            if ex_crit: df_f = pd.concat([df_f, df[df['SKU'].isin(sk_crit)]])
            if ex_mens: df_f = pd.concat([df_f, df[df['SKU'].isin(sk_mens)]])
            if ex_all: df_f = pd.concat([df_f, df])
            if search:
                s=search.lower(); df_f=pd.concat([df_f, df[df['SKU'].str.lower().str.contains(s)|df['Produto'].str.lower().str.contains(s)]])
            df_f.drop_duplicates(['SKU'],inplace=True)
            if df_f.empty:
                st.info("Nenhum filtro aplicado.")
            else:
                cols=["SKU","Produto","Contagem Inicial","Compras","Desp. Completo","Desp. Incompleto","Vendas","Total","Contagem Atual","Perda Operacional","Valor da Perda (R$)"]
                df_show=df_f[cols]
                st.dataframe(df_show)

        elif page == "KPIs":
            st.markdown("<h2 style='text-align:center;'>📈 Indicadores Chave (KPIs)</h2>", unsafe_allow_html=True)
            total_loss = df['Perda Operacional'].sum()
            total_value = df['Valor da Perda (R$)'].sum()
            mean_loss = df['Perda Operacional'].mean()
            perc_crit = len(df[df['SKU'].isin(sk_crit)])/len(df)*100
            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total de Perda (unid)", f"{total_loss:,.0f}")
            col2.metric("Total de Perda (R$)", f"R$ {total_value:,.2f}")
            col3.metric("Média de Perda (unid)", f"{mean_loss:,.2f}")
            col4.metric("% Itens Críticos", f"{perc_crit:.1f}%")

        elif page == "Comparar Produtos":
            st.markdown("<h2 style='text-align:center;'>🔍 Comparar Produtos</h2>", unsafe_allow_html=True)
            prods = df['Produto'].unique().tolist()
            p1 = st.selectbox("Produto 1", prods)
            p2 = st.selectbox("Produto 2", prods, index=1)
            m1 = df[df['Produto']==p1].iloc[0]
            m2 = df[df['Produto']==p2].iloc[0]
            metrics=['Perda Operacional','Valor da Perda (R$)','Vendas','Total']
            vals1=[m1[x] for x in metrics]; vals2=[m2[x] for x in metrics]
            x = range(len(metrics))
            fig, ax = plt.subplots(figsize=(8,4))
            ax.bar([i-0.2 for i in x], vals1, width=0.4, label=p1)
            ax.bar([i+0.2 for i in x], vals2, width=0.4, label=p2)
            ax.set_xticks(x); ax.set_xticklabels(metrics, rotation=45)
            ax.set_title('Comparativo de Métricas'); ax.legend(); ax.grid(axis='y', linestyle='--', alpha=0.5)
            plt.tight_layout(); st.pyplot(fig)

        elif page == "20 Maiores Perdas Operacionais":
            st.markdown("<h2 style='text-align:center;'>📊 Top 20 Perdas Operacionais</h2>", unsafe_allow_html=True)
            top20 = df.nlargest(20,'Perda Operacional')
            fig,ax=plt.subplots(figsize=(8,5))
            bars=ax.barh(top20['Produto'],top20['Perda Operacional'],color='salmon',edgecolor='darkred')
            ax.invert_yaxis(); ax.set_xlabel('Perda Operacional'); ax.grid(axis='x',linestyle='--',alpha=0.7)
            ax.bar_label(bars,labels=[f"{v:,.0f}" for v in top20['Perda Operacional']],padding=3)
            plt.tight_layout(); st.pyplot(fig)

        elif page == "20 Maiores Perdas em Valor":
            st.markdown("<h2 style='text-align:center;'>📊 Top 20 Perdas em Valor</h2>", unsafe_allow_html=True)
            top20v=df.nlargest(20,'Valor da Perda (R$)')
            fig,ax=plt.subplots(figsize=(8,5))
            bars=ax.barh(top20v['Produto'],top20v['Valor da Perda (R$)'],color='salmon',edgecolor='darkred')
            ax.invert_yaxis(); ax.set_xlabel('Valor da Perda (R$)'); ax.grid(axis='x',linestyle='--',alpha=0.7)
            ax.bar_label(bars,labels=[f"R$ {v:,.2f}" for v in top20v['Valor da Perda (R$)']],padding=3)
            plt.tight_layout(); st.pyplot(fig)

    st.markdown("<div class='footer'>By Gabriel Wendell Menezes Santos</div>", unsafe_allow_html=True)
elif authenticated is False:
    st.error("Usuário ou senha inválidos.")
elif authenticated is None:
    st.warning("Por favor, insira seu login.")
