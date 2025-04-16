import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Filtro de Dispersão", layout="wide")
st.title("📦 Filtro de Dispersão de Produtos")

def get_color(value, col_name):
    if col_name in ["Contagem Inicial", "Compras", "Total"]:
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
    else:
        return "white"

file = st.file_uploader("📁 Envie a planilha de Dispersão (Excel)", type=["xlsx"])

if file:
    df = pd.read_excel(file, header=2)
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

    df['SKU'] = df['SKU'].astype(str)
    skus = sorted(df['SKU'].dropna().unique())

    skus_selecionados = st.multiselect("🔍 Selecione os SKUs que deseja filtrar", skus)

    if skus_selecionados:
        colunas_desejadas = [
            "SKU", "Produto", "Contagem Inicial", "Compras", "Desp. Completo",
            "Desp. Incompleto", "Vendas", "Total", "Contagem Atual",
            "Perda Operacional", "Valor da Perda (R$)"
        ]
        df_final = df[df['SKU'].isin(skus_selecionados)][colunas_desejadas].copy()

        for col in df_final.columns[2:]:
            df_final[col] = df_final[col].astype(str).str.replace(",", ".").astype(float)

        st.success("✅ Tabela filtrada com sucesso!")
        st.dataframe(df_final)

        fig, ax = plt.subplots(figsize=(14, 4))
        ax.axis('off')

        table = ax.table(
            cellText=df_final.values,
            colLabels=df_final.columns,
            loc='center',
            cellLoc='center'
        )

        for i in range(len(df_final)):
            for j, col_name in enumerate(df_final.columns):
                valor = df_final.iloc[i][col_name]
                cor = get_color(valor, col_name)
                table[(i + 1, j)].set_facecolor(cor)

        table.auto_set_font_size(False)
        table.set_fontsize(9.5)
        table.scale(1.2, 1.5)

        st.pyplot(fig)

        output_excel = io.BytesIO()
        df_final.to_excel(output_excel, index=False)
        st.download_button("⬇️ Baixar Excel", output_excel.getvalue(), file_name="dispersao_filtrada.xlsx")

        output_img = io.BytesIO()
        fig.savefig(output_img, format='png', dpi=200)
        st.download_button("⬇️ Baixar Imagem da Tabela", output_img.getvalue(), file_name="tabela_destaque.png")
