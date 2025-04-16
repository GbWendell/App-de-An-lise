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

    # Lista de SKUs para excluir
    skus_excluir = [
        "11002224"
    ]

    # Lista de SKUs para "itens críticos"
    skus_criticos = [
        "P0035"
    ]

    # Remover SKUs excluídos
    df['SKU'] = df['SKU'].astype(str).str.replace(" ", "")  # Remover espaços dos SKUs
    df = df[~df['SKU'].isin(skus_excluir)]  # Excluir os SKUs indesejados

    # Filtrar SKUs disponíveis
    skus = sorted(df['SKU'].dropna().unique())

    # Adicionar "itens críticos" no filtro
    itens_criticos = df[df['SKU'].isin(skus_criticos)]
    skus_criticos = sorted(itens_criticos['SKU'].dropna().unique())

    # Checkbox para selecionar "itens críticos"
    exibir_criticos = st.checkbox("Exibir apenas Itens Críticos", value=False)

    if exibir_criticos:
        # Se marcar, mostra apenas os itens críticos
        skus_selecionados = skus_criticos
    else:
        # Caso contrário, mostra todos os SKUs
        skus_selecionados = st.multiselect(
            "🔍 Selecione os SKUs que deseja filtrar",
            skus,
            default=skus_criticos  # Iniciar com os itens críticos
        )

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

        fig, ax = plt.subplots(figsize=(15, 4))
        ax.axis('off')

        table = ax.table(
            cellText=df_final.values,
