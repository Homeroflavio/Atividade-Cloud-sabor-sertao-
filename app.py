"""Painel de Vendas: Sabor do Sertão.

Rodar com:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# Configuração geral
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Sabor do Sertão", page_icon="🌵", layout="wide")
st.title("🌵 Painel de Vendas: Sabor do Sertão")

ARQUIVO_LOCAL = Path("vendas_sabor_do_sertao.csv")
COLUNAS_ESPERADAS = {
    "data", "hora", "cidade", "categoria", "produto",
    "preco_unitario", "quantidade", "pagamento", "avaliacao", "total",
}
DIAS = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"}
ORDEM_DIAS = list(DIAS.values())
ROTULOS = {
    "total": "Faturamento (R$)", "mes": "Mês", "cidade": "Cidade",
    "produto": "Produto", "quantidade": "Quantidade vendida",
    "pagamento": "Forma de pagamento", "hora": "Hora do dia",
    "dia_semana": "Dia da semana", "categoria": "Categoria",
}
TEMPLATE = "plotly_white"


# ----------------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------------
def brl(valor: float) -> str:
    """Formata como moeda brasileira: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro(valor: float) -> str:
    """Formata inteiro com ponto de milhar: 5.000."""
    return f"{valor:,.0f}".replace(",", ".")


@st.cache_data
def carregar(arquivo):
    return pd.read_csv(arquivo, parse_dates=["data"])


@st.cache_data
def carregar_generico(arquivo):
    """Lê qualquer CSV (detecta o separador sozinho)."""
    if hasattr(arquivo, "seek"):
        arquivo.seek(0)
    return pd.read_csv(arquivo, sep=None, engine="python")


# ----------------------------------------------------------------------------
# Carregamento dos dados
# ----------------------------------------------------------------------------
st.sidebar.header("📂 Dados")
arquivo = st.sidebar.file_uploader("Envie o CSV de vendas", type=["csv"])

if arquivo is None:
    if ARQUIVO_LOCAL.exists():
        st.sidebar.info(f"Usando `{ARQUIVO_LOCAL.name}` da pasta do projeto. "
                        "Envie outro arquivo se quiser trocar.")
        arquivo = str(ARQUIVO_LOCAL)
    else:
        st.info("Envie o arquivo para começar.")
        st.stop()

df_bruto = carregar(arquivo)

faltando = COLUNAS_ESPERADAS - set(df_bruto.columns)
if faltando:
    st.error("O CSV enviado não tem as colunas esperadas: "
             + ", ".join(sorted(faltando))
             + ". Use o arquivo gerado por `gerar_dados.py`.")
    st.stop()

# ----------------------------------------------------------------------------
# Tratamento de ausentes (Nível 1): preencher avaliacao com a mediana
# ----------------------------------------------------------------------------
ausentes = df_bruto.isna().sum()
n_aus_aval = int(ausentes["avaliacao"])
mediana_aval = df_bruto["avaliacao"].median()

df = df_bruto.copy()
df["avaliacao"] = df["avaliacao"].fillna(mediana_aval)
df["mes"] = df["data"].dt.to_period("M").astype(str)
df["dia_semana"] = df["data"].dt.dayofweek.map(DIAS)

# ----------------------------------------------------------------------------
# Filtros na barra lateral (Nível 3)
# ----------------------------------------------------------------------------
st.sidebar.header("🎛️ Filtros")

cidades_disp = sorted(df["cidade"].unique())
sel_cidades = st.sidebar.multiselect("Cidade", cidades_disp, default=cidades_disp)

categorias_disp = sorted(df["categoria"].unique())
sel_categorias = st.sidebar.multiselect("Categoria", categorias_disp,
                                        default=categorias_disp)

data_min, data_max = df["data"].min().date(), df["data"].max().date()
periodo = st.sidebar.date_input("Período", value=(data_min, data_max),
                                min_value=data_min, max_value=data_max,
                                format="DD/MM/YYYY")

periodo_ok = isinstance(periodo, (tuple, list)) and len(periodo) == 2
if periodo_ok:
    inicio, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
    df_f = df[
        df["cidade"].isin(sel_cidades)
        & df["categoria"].isin(sel_categorias)
        & df["data"].between(inicio, fim)
    ]
else:
    st.sidebar.warning("Selecione a data inicial **e** a data final.")
    df_f = df.iloc[0:0]


# ----------------------------------------------------------------------------
# Blocos da página
# ----------------------------------------------------------------------------
def secao_exploracao():
    """Nível 1: exploração e tratamento de ausentes."""
    with st.expander("🔍 Exploração dos dados (Nível 1)", expanded=True):
        st.markdown("**Primeiras linhas**")
        amostra = df_bruto.head(10).copy()
        amostra["data"] = amostra["data"].dt.strftime("%Y-%m-%d")
        st.dataframe(amostra)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Resumo estatístico** (`df.describe()`)")
            st.dataframe(df_bruto.select_dtypes("number").describe().round(2))
        with col_b:
            st.markdown("**Valores ausentes por coluna**")
            st.dataframe(ausentes.to_frame("ausentes"))

        pct = n_aus_aval / len(df_bruto) * 100
        pct_txt = f"{pct:.1f}".replace(".", ",")
        st.caption(
            f"**Tratamento de `avaliacao`:** {n_aus_aval} valores ausentes "
            f"({pct_txt}% das vendas) foram preenchidos com a **mediana** "
            f"({mediana_aval:.0f}). A nota é uma variável ordinal de 1 a 5, "
            "então a mediana é mais robusta que a média e mantém um valor que "
            "existe na escala. Remover as linhas descartaria vendas reais e "
            "distorceria faturamento e número de vendas."
        )


def secao_kpis(d: pd.DataFrame):
    """Nível 2: indicadores."""
    faturamento = d["total"].sum()
    vendas = len(d)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Faturamento total", brl(faturamento))
    c2.metric("🧾 Número de vendas", inteiro(vendas))
    c3.metric("🎯 Ticket médio", brl(faturamento / vendas))
    c4.metric("⭐ Avaliação média",
              f"{d['avaliacao'].mean():.2f}".replace(".", ",") + " / 5")


def secao_graficos(d: pd.DataFrame):
    """Nível 4: visualizações em abas."""
    abas = st.tabs([
        "📈 Faturamento mensal", "🏙️ Por cidade", "🏆 Top 5 produtos",
        "💳 Pagamentos", "🔥 Mapa de calor",
    ])

    with abas[0]:
        mensal = (d.groupby(d["data"].dt.to_period("M"))["total"].sum()
                  .reset_index())
        mensal["mes"] = mensal["data"].astype(str)
        fig = px.line(mensal, x="mes", y="total", markers=True,
                      labels=ROTULOS, template=TEMPLATE,
                      title="Faturamento mensal")
        fig.update_yaxes(tickprefix="R$ ")
        st.plotly_chart(fig)

    with abas[1]:
        por_cidade = (d.groupby("cidade")["total"].sum().reset_index()
                      .sort_values("total", ascending=False))
        fig = px.bar(por_cidade, x="cidade", y="total", text_auto=".2s",
                     color="cidade", labels=ROTULOS, template=TEMPLATE,
                     title="Faturamento por cidade")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickprefix="R$ ")
        st.plotly_chart(fig)

    with abas[2]:
        top5 = (d.groupby("produto")["quantidade"].sum().nlargest(5)
                .reset_index().sort_values("quantidade"))
        fig = px.bar(top5, x="quantidade", y="produto", orientation="h",
                     text_auto=True, labels=ROTULOS, template=TEMPLATE,
                     title="Top 5 produtos mais vendidos (em quantidade)")
        st.plotly_chart(fig)

    with abas[3]:
        pagamentos = d.groupby("pagamento")["total"].sum().reset_index()
        fig = px.pie(pagamentos, names="pagamento", values="total", hole=0.4,
                     labels=ROTULOS, template=TEMPLATE,
                     title="Participação de cada forma de pagamento (no faturamento)")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

    with abas[4]:
        fig = px.density_heatmap(
            d, x="hora", y="dia_semana", z="total", histfunc="sum",
            nbinsx=d["hora"].nunique(),
            category_orders={"dia_semana": ORDEM_DIAS},
            color_continuous_scale="YlOrRd", labels=ROTULOS,
            template=TEMPLATE,
            title="Faturamento por dia da semana e hora",
        )
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig)


def secao_insights(d: pd.DataFrame):
    """Nível 5: conclusões geradas a partir dos dados filtrados + exportação."""
    st.subheader("💡 Insights para a diretoria")

    por_cidade = d.groupby("cidade")["total"].sum().sort_values(ascending=False)
    cidade_top = por_cidade.index[0]
    part_cidade = por_cidade.iloc[0] / por_cidade.sum() * 100

    qtd_prod = d.groupby("produto")["quantidade"].sum().sort_values(ascending=False)
    produto_top = qtd_prod.index[0]
    categoria_top = d.groupby("categoria")["total"].sum().idxmax()

    hora_pico = d.groupby("hora")["total"].sum().idxmax()
    hora_pico_cidade = (d[d["cidade"] == cidade_top].groupby("hora")["total"]
                        .sum().idxmax())
    dia_pico = d.groupby("dia_semana")["total"].sum().idxmax()
    pagamento_top = d["pagamento"].value_counts(normalize=True)
    pct_cidade_txt = f"{part_cidade:.1f}".replace(".", ",")
    pct_pag_txt = f"{pagamento_top.iloc[0] * 100:.1f}".replace(".", ",")

    st.markdown(
        f"1. **Onde vendemos mais:** {cidade_top} lidera com "
        f"**{pct_cidade_txt}%** do faturamento do recorte atual "
        f"({brl(por_cidade.iloc[0])}).\n"
        f"2. **O que vendemos mais:** o produto mais vendido em quantidade é "
        f"**{produto_top}** ({inteiro(qtd_prod.iloc[0])} unidades), e a "
        f"categoria que mais fatura é **{categoria_top}**.\n"
        f"3. **Quando e como:** o horário de pico geral é às **{hora_pico}h** "
        f"(em {cidade_top}, às {hora_pico_cidade}h), o melhor dia é "
        f"**{dia_pico}**, e **{pagamento_top.index[0]}** é a forma de "
        f"pagamento mais usada ({pct_pag_txt}% das vendas)."
    )

    # Exportação do CSV já filtrado (colunas originais, data legível)
    export = d[list(df_bruto.columns)].copy()
    export["data"] = export["data"].dt.strftime("%Y-%m-%d")
    st.download_button(
        "⬇️ Baixar CSV filtrado",
        data=export.to_csv(index=False).encode("utf-8-sig"),
        file_name="vendas_filtradas.csv",
        mime="text/csv",
    )


def aba_explorador():
    """Desafio bônus: explorador livre de qualquer CSV."""
    st.subheader("🔎 Explorador livre")
    st.caption("Envie qualquer CSV (ou use os dados de vendas) e escolha "
               "eixo X, eixo Y e o tipo de gráfico. Esta aba não usa os "
               "filtros da barra lateral.")

    up = st.file_uploader("CSV para explorar", type=["csv"], key="up_livre")
    if up is not None:
        dados = carregar_generico(up)
        st.write(f"Arquivo: **{up.name}**: {inteiro(len(dados))} linhas, "
                 f"{len(dados.columns)} colunas")
    else:
        dados = df_bruto
        st.write("Usando os dados de vendas do painel.")

    st.dataframe(dados.head(5))

    colunas = list(dados.columns)
    numericas = list(dados.select_dtypes("number").columns)
    tipos = (["Barras", "Linha", "Dispersão", "Histograma", "Box plot"]
             if numericas else ["Histograma"])

    c1, c2, c3, c4 = st.columns(4)
    tipo = c1.selectbox("Tipo de gráfico", tipos)
    x = c2.selectbox("Eixo X", colunas)
    y = c3.selectbox("Eixo Y (numérico)", numericas or ["(sem colunas numéricas)"],
                     disabled=(tipo == "Histograma" or not numericas))
    agg_nome = c4.selectbox("Agregação", ["Soma", "Média", "Contagem", "Máximo", "Mínimo"],
                            disabled=tipo not in ("Barras", "Linha"))
    agg = {"Soma": "sum", "Média": "mean", "Contagem": "count",
           "Máximo": "max", "Mínimo": "min"}[agg_nome]

    try:
        if tipo in ("Barras", "Linha"):
            nome_y = f"{agg_nome} de {y}"
            g = dados.groupby(x, as_index=False).agg(**{nome_y: (y, agg)})
            if tipo == "Barras":
                g = g.sort_values(nome_y, ascending=False).head(30)
                fig = px.bar(g, x=x, y=nome_y, template=TEMPLATE,
                             title=f"{nome_y} por {x}")
            else:
                g = g.sort_values(x)
                fig = px.line(g, x=x, y=nome_y, markers=True, template=TEMPLATE,
                              title=f"{nome_y} por {x}")
        elif tipo == "Dispersão":
            fig = px.scatter(dados.head(5000), x=x, y=y, template=TEMPLATE,
                             title=f"{y} vs {x}")
        elif tipo == "Histograma":
            fig = px.histogram(dados, x=x, template=TEMPLATE,
                               title=f"Distribuição de {x}")
        else:  # Box plot
            eixo_x = x if dados[x].nunique() <= 20 else None
            fig = px.box(dados, x=eixo_x, y=y, template=TEMPLATE,
                         title=f"Box plot de {y}" + (f" por {x}" if eixo_x else ""))
        st.plotly_chart(fig)
    except Exception as erro:  # combinação de colunas inválida
        st.error(f"Não foi possível montar esse gráfico com as colunas escolhidas: {erro}")


# ----------------------------------------------------------------------------
# Montagem da página
# ----------------------------------------------------------------------------
tab_painel, tab_livre = st.tabs(["📊 Painel de vendas", "🔎 Explorador livre"])

with tab_painel:
    secao_exploracao()
    st.divider()
    if not periodo_ok:
        st.warning("Escolha a data inicial e a final na barra lateral.")
    elif df_f.empty:
        st.warning("Nenhuma venda encontrada com os filtros atuais. "
                   "Ajuste cidade, categoria ou período.")
    else:
        secao_kpis(df_f)
        st.divider()
        secao_graficos(df_f)
        st.divider()
        secao_insights(df_f)

with tab_livre:
    aba_explorador()