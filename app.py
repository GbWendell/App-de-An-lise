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
    df['Perda Operacional'] = pd.to_numeric(df['Perda Operacional'].astype(str).str.replace(",", "."), errors='coerce')
    df['Valor da Perda (R$)'] = pd.to_numeric(df['Valor da Perda (R$)'].astype(str).str.replace(",", "."), errors='coerce')
    return df

# --- Aplicação principal ---
if authenticated:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Bem-vindo, {name}!")

    # Menu lateral
    st.sidebar.markdown("## Navegação")
    page = st.sidebar.radio("", ["20 Maiores Perdas Operacionais", "20 Maiores Perdas em Valor"])

    file = st.sidebar.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

    if not file:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2015/12/08/00/32/business-1081802_960_720.jpg", width=600)
        st.markdown(
            "<h3>Ser dono do seu próprio negócio é ter o controle da sua jornada. Não é sobre ter um emprego, é sobre construir um legado.</h3>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        df = carregar_planilha(file)

        st.markdown("<h1 style='text-align: center;'>📊 Análise de Perdas</h1>", unsafe_allow_html=True)

        if page == "20 Maiores Perdas Operacionais":
            top20 = df.nlargest(20, 'Perda Operacional')
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(top20['Produto'], top20['Perda Operacional'])
            ax.invert_yaxis()
            ax.set_xlabel('Perda Operacional')
            ax.set_title('Top 20 Maiores Perdas Operacionais')
            st.pyplot(fig)

        elif page == "20 Maiores Perdas em Valor":
            top20v = df.nlargest(20, 'Valor da Perda (R$)')
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(top20v['Produto'], top20v['Valor da Perda (R$)'])
            ax.invert_yaxis()
            ax.set_xlabel('Valor da Perda (R$)')
            ax.set_title('Top 20 Maiores Perdas em Valor')
            st.pyplot(fig)

    st.markdown("<div class='footer'><span>By Gabriel Wendell Menezes Santos</span></div>", unsafe_allow_html=True)
elif authenticated is False:
    st.error("Usuário ou senha inválidos.")
elif authenticated is None:
    st.warning("Por favor, insira seu login.")
