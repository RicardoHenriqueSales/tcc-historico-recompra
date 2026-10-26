"""Confere resultados de referência do estudo após uma nova execução."""
from pathlib import Path
import argparse, json
import pandas as pd

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out', default='resultados')
    folder=Path(p.parse_args().out)
    summary=json.loads((folder/'resumo.json').read_text(encoding='utf-8'))
    for name, expected in {'linhas_vendas':392692,'clientes_vendas':4338,
        'clientes_elegiveis':1916,'dias_cliente':16763}.items():
        assert summary[name]==expected, (name,summary[name],expected)
    assert summary['auditoria'][0]['linhas']==541909
    assert round(summary['vendas_elegiveis_gbp'],2)==7318199.43
    matrix=pd.read_csv(folder/'matriz_concordancia.csv')
    assert matrix.clientes.tolist()==[1587,60,75,194]
    for minimo,counts,money in [(3,[55,118,201],[160925.17,367477.24,806234.98]),
                               (5,[31,58,111],[125556.09,282764.80,685254.63])]:
        rows=[x for x in summary['janelas_antecipacao'] if x['minimo_dias']==minimo]
        assert [x['clientes'] for x in rows]==counts
        assert [round(x['vendas_gbp'],2) for x in rows]==money
    sensitivity=pd.read_csv(folder/'sensibilidade.csv')
    assert sensitivity.alertas_individualizados.tolist()==[371,269,200]
    base=pd.read_csv(folder/'Base_clientes_PowerBI.csv',sep=';',decimal=',')
    assert len(base)==1916
    assert base.CustomerID.nunique()==1916
    assert set(base.DataReferencia)=={'2011-12-10'}
    assert round(base.VendasHistoricasGBP.sum(),2)==7318199.43
    print('Conferência concluída: base, grupos, sensibilidade, seis janelas e exportação Power BI coincidem com os resultados de referência.')

if __name__=='__main__': main()
