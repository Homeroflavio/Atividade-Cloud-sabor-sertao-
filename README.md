# 🌵 Painel de Vendas: Sabor do Sertão

Painel interativo em **Streamlit** para analisar um ano de vendas (2025) da rede
fictícia de lanchonetes **Sabor do Sertão**, com lojas em Recife, Olinda, Caruaru,
Petrolina e Garanhuns. O painel responde: **onde**, **o quê**, **quando** e
**como** os clientes pagam.

**Autores:** _(nome da dupla aqui)_
**Painel publicado (opcional):** _(link do Streamlit Community Cloud aqui)_

---

## 📸 Print do painel

<!-- 👇 SUBSTITUA ESTA ÁREA PELO PRINT DO PAINEL FUNCIONANDO 👇
     1. Rode o painel e tire o print da tela inteira.
     2. Salve como print_painel.png na raiz do repositório.
     3. A linha abaixo já aponta para esse arquivo. -->

![Print do painel funcionando](print_painel.png)

> ⚠️ **COLE AQUI O PRINT DO PAINEL** (apague este aviso depois de subir o `print_painel.png`).

---

## ✅ O que o painel tem

| Nível | Entrega |
|-------|---------|
| 1. Exploração | Primeiras linhas, `describe()`, ausentes por coluna e tratamento de `avaliacao` (mediana, justificado em `st.caption`) |
| 2. Indicadores | 4 KPIs: faturamento total, nº de vendas, ticket médio e avaliação média |
| 3. Filtros | Cidade, categoria e período na barra lateral; KPIs, gráficos e insights reagem a todos |
| 4. Gráficos | Em abas: faturamento mensal (linha), por cidade (barras), top 5 produtos (barras horizontais), pagamentos (pizza) e mapa de calor dia da semana × hora |
| 5. Insights | 3 conclusões geradas a partir dos dados filtrados + botão para baixar o CSV filtrado |
| Bônus | Aba **Explorador livre**: qualquer CSV, com escolha de eixo X, eixo Y e tipo de gráfico |

### Decisão sobre dados ausentes
A coluna `avaliacao` tem 60 valores ausentes (1,2% das vendas). Preenchi com a
**mediana**: a nota é ordinal (1 a 5), a mediana é robusta e mantém um valor que
existe na escala. Remover as linhas descartaria vendas reais e distorceria o
faturamento e o número de vendas.

---

## ▶️ Como rodar

Requisitos: Python 3.10+.

```bash
# 1. (opcional) criar e ativar um ambiente virtual
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# 2. instalar as dependências
pip install -r requirements.txt

# 3. gerar os dados (cria vendas_sabor_do_sertao.csv)
python gerar_dados.py

# 4. abrir o painel
streamlit run app.py
```

No painel, envie o `vendas_sabor_do_sertao.csv` pela barra lateral. Se o arquivo
estiver na mesma pasta do `app.py`, ele é carregado automaticamente.

## 📁 Estrutura

```
├── app.py                # painel Streamlit
├── gerar_dados.py        # gera o CSV de vendas (semente fixa 42)
├── requirements.txt      # dependências
├── README.md
└── print_painel.png      # print do painel (adicionar)
```
