# Procedimentos de tratamento e cálculo

1. Remover duplicatas exatas nas oito colunas, mantendo a primeira ocorrência.
2. Excluir registros sem CustomerID.
3. Excluir notas cujo InvoiceNo começa com C.
4. Excluir quantidades não positivas, preços não positivos e datas inválidas.
5. Calcular o valor da linha em pence, arredondando antes da agregação, e apresentar as somas em GBP.
6. Consolidar as compras por cliente e data civil. Várias notas no mesmo dia contam como um único evento para os intervalos.
7. Selecionar os clientes com pelo menos três dias distintos de compra, comparando também o mínimo de cinco dias.

## Indicadores

Para n dias de compra e período S entre o primeiro e o último dia, `IMC = S / (n − 1)`. A recência r é a diferença entre a referência e a última compra. O intervalo ainda aberto entre a última compra e a referência não integra a média.

O coeficiente de variação é o desvio-padrão amostral dos intervalos dividido pelo IMC. A próxima compra estimada corresponde à última data mais o IMC; a distância em dias até essa referência é `IMC − r`.

O alerta fixo utiliza `r > 90`. O individual utiliza `r > k × IMC`, com k igual a 1,2, 1,6 ou 2,0. A igualdade ao limite não produz alerta. Para evitar diferenças de ponto flutuante nas fronteiras, o cálculo individual compara inteiros: `10 × r × (n − 1) > round(10 × k) × S`.

Para antecedência a, a janela inclui `(1 − a) × IMC ≤ r ≤ IMC`. O cálculo utiliza a forma equivalente com inteiros. Clientes após o IMC não pertencem à fila antecipada.

A fila antecipada é ordenada por vendas históricas decrescentes, razão recência/IMC decrescente e CustomerID crescente. O valor histórico é descritivo e não uma estimativa de benefício da abordagem.

## Cortes temporais

As referências de 01/09/2011, 01/10/2011, 01/11/2011 e 10/12/2011 utilizam somente registros anteriores à respectiva data, com recálculo dos indicadores e da elegibilidade. São fotografias descritivas de populações diferentes, sem validação contra recompras futuras.

## Rastreabilidade

O resumo JSON registra a URL e o hash SHA-256 do XLSX, a auditoria de limpeza, os indicadores agregados e os resultados dos cenários. As tabelas publicadas podem ser comparadas com uma nova execução do script. Os scripts de geração do Word e os arquivos do documento acadêmico não fazem parte do processamento dos dados.
