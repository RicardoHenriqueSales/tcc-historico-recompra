# Histórico de recompra como apoio à priorização do acompanhamento comercial

Material complementar do estudo de caso do MBA em Administração, Finanças e Geração de Valor da PUCRS, de Ricardo Henrique Sales.

O projeto organiza o histórico de compras por cliente, compara regras de atraso e examina janelas de antecipação. A referência principal é **10 de dezembro de 2011**. Os resultados são descritivos: não confirmam necessidade de compra, perda de clientes ou melhoria das vendas.

## Conteúdo

- `scripts/analisar_recompra.py`: tratamento da base, indicadores, concordância, sensibilidade, cortes temporais, janelas de antecipação e exportação para Power BI.
- `scripts/verificar_resultados.py`: conferência dos resultados de referência.
- `requirements.txt`: versões das bibliotecas do ambiente utilizado.
- `resultados/`: resultados agregados para conferência das tabelas e do painel.
- `docs/medidas_powerbi.md`: tabelas de parâmetros, medidas DAX e formatos utilizados no painel.
- `docs/metodo.md`: critérios operacionais e interpretação dos resultados.

## Fonte dos dados

CHEN, Daqing. **Online Retail**. UCI Machine Learning Repository, 2015. DOI: [10.24432/C5BW33](https://doi.org/10.24432/C5BW33).

O conjunto original é disponibilizado pela UCI sob CC BY 4.0. Este repositório contém resultados derivados, com exclusão de registros conforme o método descrito em `docs/metodo.md`. A base bruta não é incluída no pacote; o script pode baixá-la diretamente da UCI. A licença da fonte não é uma declaração de licença geral do código deste repositório.

## Como executar

Ambiente de referência: Python 3.12.14, pandas 3.0.1, numpy 2.3.5 e openpyxl 3.1.5.

Abra um terminal na pasta do projeto. Instale as bibliotecas:

```console
python -m pip install -r requirements.txt
```

Para baixar a base oficial e gerar os resultados:

```console
python scripts/analisar_recompra.py --out reproducao
```

O download exige acesso à internet. Se já tiver a base original:

```console
python scripts/analisar_recompra.py --input "CAMINHO/Online Retail.xlsx" --out reproducao
```

O argumento `--input` deve apontar para o arquivo bruto da UCI, sem tratamento prévio. A pasta de saída será criada se não existir. Use uma pasta separada, como `reproducao`, para comparar os novos arquivos com os resultados publicados. O processamento do XLSX pode levar alguns minutos.

Confira os resultados gerados:

```console
python scripts/verificar_resultados.py --out reproducao
```

## Resultados de referência

| Indicador | Resultado |
|---|---:|
| Linhas da base original | 541.909 |
| Linhas após o tratamento | 392.692 |
| Clientes com vendas positivas | 4.338 |
| Clientes com ao menos três dias de compra | 1.916 |
| Vendas positivas históricas dos elegíveis em GBP | 7.318.199,43 |
| Alertas pela regra fixa de 90 dias | 254 |
| Alertas pela regra individual de 1,6 × IMC | 269 |
| Classificações divergentes | 135 |
| Janela de antecipação de 10% | 55 |
| Janela de antecipação de 20% | 118 |
| Janela de antecipação de 30% | 201 |

As janelas de antecipação são cumulativas e não devem ser somadas. Ao exigir cinco dias de compra, a população cai para 1.026 clientes e as três janelas selecionam 31, 58 e 111 clientes.

## Power BI

O arquivo `resultados/Base_clientes_PowerBI.csv` utiliza UTF-8 com BOM, ponto e vírgula como separador e vírgula decimal. No Power Query, os tipos numéricos devem ser definidos com localidade Português (Brasil). `CustomerID` é texto; `DataReferencia`, `PrimeiraCompra` e `UltimaCompra` são datas; as contagens e a recência são inteiros; o IMC e o CV são decimais; as vendas históricas são decimais fixos em GBP.

As tabelas de parâmetros ficam sem relacionamento com `Clientes`. Os seletores permitem 10%, 20% ou 30% de antecipação; fatores 1,2, 1,6 ou 2,0; e mínimo de três ou cinco dias de compra. No painel, os filtros de cada página são independentes. Os cortes históricos são produzidos pelo script e não por um seletor de data no painel.

Painel público: [consultar relatório interativo](https://app.powerbi.com/view?r=eyJrIjoiNWNjNDc1NTgtOTE5OS00YjkwLWJjMTItMzVkZmEzN2YyNjJkIiwidCI6ImJmMzg0ODM5LWE4YTgtNGJjMS05Yzk2LTIwODM5YTRmZDZlOCJ9).

## Limites de interpretação

As vendas positivas históricas não abatem devoluções e não representam receita líquida, lucro, receita perdida ou retorno esperado. Os limites de 90 dias, 1,6 × IMC e as antecedências são escolhas operacionais de comparação. A análise não implementa modelos probabilísticos de churn nem mede o efeito causal de contatos comerciais.
