# Tabelas e medidas do Power BI

As tabelas de parâmetros devem permanecer sem relacionamentos com Clientes. Crie as três tabelas antes das medidas.

## Parametro Antecipacao

```dax
Parametro Antecipacao =
DATATABLE(
    "Percentual", DOUBLE,
    {
        {0.10},
        {0.20},
        {0.30}
    }
)
```

## Parametro Multiplicador

```dax
Parametro Multiplicador =
DATATABLE(
    "Multiplicador", DOUBLE,
    {
        {1.2},
        {1.6},
        {2.0}
    }
)
```

## Parametro Historico

```dax
Parametro Historico =
DATATABLE(
    "MinimoDiasCompra", INTEGER,
    {
        {3},
        {5}
    }
)
```

## Total Clientes

```dax
Total Clientes =
VAR Minimo = [Historico minimo selecionado]
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
        )
    )
```

## Vendas Históricas GBP

```dax
Vendas Históricas GBP =
VAR Minimo = [Historico minimo selecionado]
RETURN
    SUMX(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
        ),
        Clientes[VendasHistoricasGBP]
    )
```

## Clientes — Regra de 90 dias

```dax
Clientes — Regra de 90 dias =
VAR Minimo = [Historico minimo selecionado]
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
                && Clientes[RecenciaDias] > 90
        )
    )
```

## Clientes — Regra individual

```dax
Clientes — Regra individual =
VAR Minimo = [Historico minimo selecionado]
VAR Fator10 = ROUND([Multiplicador selecionado] * 10, 0)
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
                && Clientes[RecenciaDias] * 10
                    * (Clientes[DiasCompra] - 1)
                    > Fator10 * Clientes[PeriodoObservadoDias]
        )
    )
```

## Antecipacao selecionada

```dax
Antecipacao selecionada =
SELECTEDVALUE(
    'Parametro Antecipacao'[Percentual],
    0.20
)
```

## Multiplicador selecionado

```dax
Multiplicador selecionado =
SELECTEDVALUE(
    'Parametro Multiplicador'[Multiplicador],
    1.6
)
```

## Historico minimo selecionado

```dax
Historico minimo selecionado =
SELECTEDVALUE(
    'Parametro Historico'[MinimoDiasCompra],
    3
)
```

## Clientes — Ambas as regras

```dax
Clientes — Ambas as regras =
VAR Minimo = [Historico minimo selecionado]
VAR Fator10 = ROUND([Multiplicador selecionado] * 10, 0)
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
                && Clientes[RecenciaDias] > 90
                && Clientes[RecenciaDias] * 10
                    * (Clientes[DiasCompra] - 1)
                    > Fator10 * Clientes[PeriodoObservadoDias]
        )
    )
```

## Clientes — Somente regra individual

```dax
Clientes — Somente regra individual =
[Clientes — Regra individual]
    - [Clientes — Ambas as regras]
```

## Clientes — Nenhuma regra

```dax
Clientes — Nenhuma regra =
[Total Clientes]
    - [Clientes — Regra de 90 dias]
    - [Clientes — Regra individual]
    + [Clientes — Ambas as regras]
```

## Clientes — Regras divergentes

```dax
Clientes — Regras divergentes =
[Clientes — Somente regra fixa]
    + [Clientes — Somente regra individual]
```

## Clientes — Somente regra fixa

```dax
Clientes — Somente regra fixa =
[Clientes — Regra de 90 dias]
    - [Clientes — Ambas as regras]
```

## Percentual de divergencia

```dax
Percentual de divergencia =
DIVIDE(
    [Clientes — Regras divergentes],
    [Total Clientes],
    0
)
```

## Clientes — Janela de recompra

```dax
Clientes — Janela de recompra =
VAR Minimo = [Historico minimo selecionado]
VAR Percentual100 = ROUND([Antecipacao selecionada] * 100, 0)
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            VAR Tempo100 =
                Clientes[RecenciaDias]
                    * (Clientes[DiasCompra] - 1) * 100
            VAR Periodo =
                Clientes[PeriodoObservadoDias]
            RETURN
                Clientes[DiasCompra] >= Minimo
                    && Tempo100 >= (100 - Percentual100) * Periodo
                    && Tempo100 <= 100 * Periodo
        )
    )
```

## Percentual na janela de recompra

```dax
Percentual na janela de recompra =
DIVIDE(
    [Clientes — Janela de recompra],
    [Total Clientes],
    0
)
```

## Vendas históricas — Janela GBP

```dax
Vendas históricas — Janela GBP =
VAR Minimo = [Historico minimo selecionado]
VAR Percentual100 = ROUND([Antecipacao selecionada] * 100, 0)
RETURN
    SUMX(
        FILTER(
            Clientes,
            VAR Tempo100 =
                Clientes[RecenciaDias]
                    * (Clientes[DiasCompra] - 1) * 100
            VAR Periodo =
                Clientes[PeriodoObservadoDias]
            RETURN
                Clientes[DiasCompra] >= Minimo
                    && Tempo100 >= (100 - Percentual100) * Periodo
                    && Tempo100 <= 100 * Periodo
        ),
        Clientes[VendasHistoricasGBP]
    )
```

## Clientes — Antes da janela

```dax
Clientes — Antes da janela =
VAR Minimo = [Historico minimo selecionado]
VAR Percentual100 = ROUND([Antecipacao selecionada] * 100, 0)
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
                && Clientes[RecenciaDias]
                    * (Clientes[DiasCompra] - 1) * 100
                    < (100 - Percentual100)
                        * Clientes[PeriodoObservadoDias]
        )
    )
```

## Clientes — Apos IMC sem alerta

```dax
Clientes — Apos IMC sem alerta =
VAR Minimo = [Historico minimo selecionado]
VAR Fator10 = ROUND([Multiplicador selecionado] * 10, 0)
RETURN
    COUNTROWS(
        FILTER(
            Clientes,
            VAR Tempo =
                Clientes[RecenciaDias] * (Clientes[DiasCompra] - 1)
            VAR Periodo =
                Clientes[PeriodoObservadoDias]
            RETURN
                Clientes[DiasCompra] >= Minimo
                    && Tempo > Periodo
                    && Tempo * 10 <= Fator10 * Periodo
        )
    )
```

## Vendas históricas — Alerta individual GBP

```dax
Vendas históricas — Alerta individual GBP =
VAR Minimo = [Historico minimo selecionado]
VAR Fator10 = ROUND([Multiplicador selecionado] * 10, 0)
RETURN
    SUMX(
        FILTER(
            Clientes,
            Clientes[DiasCompra] >= Minimo
                && Clientes[RecenciaDias] * 10
                    * (Clientes[DiasCompra] - 1)
                    > Fator10 * Clientes[PeriodoObservadoDias]
        ),
        Clientes[VendasHistoricasGBP]
    )
```

## Comparacao das regras

```dax
Comparacao das regras =
VAR Fator10 =
    ROUND([Multiplicador selecionado] * 10, 0)
VAR RegraFixa =
    MAX(Clientes[RecenciaDias]) > 90
VAR RegraIndividual =
    MAX(Clientes[RecenciaDias]) * 10
        * (MAX(Clientes[DiasCompra]) - 1)
        > Fator10 * MAX(Clientes[PeriodoObservadoDias])
RETURN
    IF(
        HASONEVALUE(Clientes[CustomerID]),
        SWITCH(
            TRUE(),
            [Cliente elegivel] = 0, "Historico insuficiente",
            RegraFixa && RegraIndividual, "Ambas as regras",
            RegraFixa, "Somente regra fixa",
            RegraIndividual, "Somente regra individual",
            "Nenhuma regra"
        ),
        BLANK()
    )
```

## Cliente elegivel

```dax
Cliente elegivel =
VAR Minimo = [Historico minimo selecionado]
RETURN
    IF(
        HASONEVALUE(Clientes[CustomerID]),
        IF(
            MAX(Clientes[DiasCompra]) >= Minimo,
            1,
            0
        ),
        BLANK()
    )
```

## Razao Recencia IMC

```dax
Razao Recencia IMC =
IF(
    HASONEVALUE(Clientes[CustomerID]),
    DIVIDE(
        MAX(Clientes[RecenciaDias]),
        MAX(Clientes[IMCDias])
    ),
    BLANK()
)
```

## Dias ate recompra estimada

```dax
Dias ate recompra estimada =
IF(
    HASONEVALUE(Clientes[CustomerID]),
    MAX(Clientes[IMCDias]) - MAX(Clientes[RecenciaDias]),
    BLANK()
)
```

## Limite individual em dias

```dax
Limite individual em dias =
IF(
    HASONEVALUE(Clientes[CustomerID]),
    MAX(Clientes[IMCDias]) * [Multiplicador selecionado],
    BLANK()
)
```

## Etapa do cliente

```dax
Etapa do cliente =
VAR Antecipacao100 =
    ROUND([Antecipacao selecionada] * 100, 0)
VAR Fator10 =
    ROUND([Multiplicador selecionado] * 10, 0)
VAR Tempo =
    MAX(Clientes[RecenciaDias])
        * (MAX(Clientes[DiasCompra]) - 1)
VAR Periodo =
    MAX(Clientes[PeriodoObservadoDias])
RETURN
    IF(
        HASONEVALUE(Clientes[CustomerID]),
        SWITCH(
            TRUE(),
            [Cliente elegivel] = 0, "Historico insuficiente",
            Tempo * 10 > Fator10 * Periodo, "Alerta individual",
            Tempo > Periodo, "Apos o IMC, sem alerta",
            Tempo * 100 >= (100 - Antecipacao100) * Periodo,
                "Na janela de recompra",
            "Antes da janela"
        ),
        BLANK()
    )
```

## Cliente na janela

```dax
Cliente na janela =
IF([Cliente elegivel] = 1 && [Etapa do cliente] = "Na janela de recompra", 1, 0)
```

## Formatos

Valores em GBP: `"GBP "#,##0.00`. Percentuais: `0.00%`. IMC, CV, razão e distância temporal: `0.00`. Contagens: `#,##0`. Valores financeiros devem ser apresentados em GBP, sem conversão para reais.
