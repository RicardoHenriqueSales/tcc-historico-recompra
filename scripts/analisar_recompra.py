"""Estudo descritivo de recompra. Fonte: Chen (2015), DOI 10.24432/C5BW33.

Uso: python analisar_recompra.py --input "Online Retail.xlsx" --out resultados
Sem --input, baixa o ZIP oficial da UCI. Requer pandas, openpyxl e numpy.
Tambem exporta as janelas de antecipacao e a base agregada para o Power BI.
Valores monetarios sao vendas positivas historicas, em GBP, sem abater devolucoes.
"""
from pathlib import Path
import argparse, hashlib, json, zipfile, urllib.request
import pandas as pd
import numpy as np

URL = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
GROUPS = ['Nenhuma regra', 'Somente fixa', 'Somente individualizada', 'Ambas as regras']

def snapshot(sales, cutoff, minimum=3, factor=1.6):
    x = sales[sales['dia'] < pd.Timestamp(cutoff)]
    daily = x.groupby(['CustomerID','dia'], as_index=False)['vendas_gbp'].sum()
    c = daily.groupby('CustomerID').agg(primeira_compra=('dia','min'),ultima_compra=('dia','max'),dias_compra=('dia','size'),vendas_gbp=('vendas_gbp','sum'))
    c = c[c.dias_compra >= minimum].copy()
    c['recencia_dias'] = (pd.Timestamp(cutoff) - c.ultima_compra).dt.days
    c['imc_dias'] = (c.ultima_compra-c.primeira_compra).dt.days/(c.dias_compra-1)
    gaps = daily.sort_values(['CustomerID','dia']).groupby('CustomerID')['dia'].diff().dt.days
    daily['intervalo'] = gaps
    cv = daily.groupby('CustomerID').intervalo.agg(['mean','std'])
    c['cv_intervalos'] = cv['std']/cv['mean']
    c['limiar_dias'] = factor*c.imc_dias
    c['desvio_ciclos'] = c.recencia_dias/c.imc_dias
    c['alerta_fixa'] = c.recencia_dias > 90
    span=(c.ultima_compra-c.primeira_compra).dt.days
    c['alerta_individualizada'] = c.recencia_dias*10*(c.dias_compra-1) > round(factor*10)*span
    c['grupo'] = np.select([c.alerta_fixa & c.alerta_individualizada,c.alerta_fixa, c.alerta_individualizada],[GROUPS[3],GROUPS[1],GROUPS[2]],default=GROUPS[0])
    return c, daily

def matrix(c):
    m = c.groupby('grupo').agg(clientes=('dias_compra','size'),vendas_gbp=('vendas_gbp','sum')).reindex(GROUPS,fill_value=0)
    m['pct_clientes'] = m.clientes/len(c)*100
    m['pct_vendas'] = m.vendas_gbp/c.vendas_gbp.sum()*100
    return m


def exportar_antecipacao_e_powerbi(c, out, cutoff):
    """Exporta cenarios cumulativos e a tabela de indicadores usada no Power BI."""
    scenarios=[]
    for minimo in (3, 5):
        eligible=c[c.dias_compra >= minimo]
        span=(eligible.ultima_compra-eligible.primeira_compra).dt.days
        tempo=eligible.recencia_dias*(eligible.dias_compra-1)
        for pct in (10, 20, 30):
            selected=eligible[(100-pct)*span <= 100*tempo]
            # O limite superior inclui a igualdade ao IMC.
            selected=selected[selected.recencia_dias*(selected.dias_compra-1)
                              <= (selected.ultima_compra-selected.primeira_compra).dt.days]
            scenarios.append({
                'minimo_dias':minimo, 'antecedencia_pct':pct,
                'clientes_elegiveis':len(eligible), 'clientes':len(selected),
                'pct_elegiveis':len(selected)/len(eligible)*100,
                'vendas_gbp':round(float(selected.vendas_gbp.sum()),2)
            })
            queue=selected.reset_index().sort_values(
                ['vendas_gbp','desvio_ciclos','CustomerID'],ascending=[False,False,True])
            queue.to_csv(out/f'fila_antecipacao_{minimo}dias_{pct}pct.csv',
                         index=False,encoding='utf-8-sig')
    pd.DataFrame(scenarios).to_csv(out/'janelas_antecipacao.csv',index=False,
                                  encoding='utf-8-sig')
    rows=c.reset_index()
    base=pd.DataFrame({
        'CustomerID':rows.CustomerID.astype(str),
        'DataReferencia':cutoff,
        'PrimeiraCompra':rows.primeira_compra.dt.strftime('%Y-%m-%d'),
        'UltimaCompra':rows.ultima_compra.dt.strftime('%Y-%m-%d'),
        'DiasCompra':rows.dias_compra,
        'PeriodoObservadoDias':(rows.ultima_compra-rows.primeira_compra).dt.days,
        'RecenciaDias':rows.recencia_dias,
        'IMCDias':rows.imc_dias,
        'CVIntervalos':rows.cv_intervalos,
        'VendasHistoricasGBP':rows.vendas_gbp.round(2)
    })
    base.to_csv(out/'Base_clientes_PowerBI.csv',sep=';',decimal=',',
                index=False,encoding='utf-8-sig')
    return scenarios

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--out', default='resultados'); args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    if args.input: source=Path(args.input)
    else:
        zpath=out/'online_retail.zip'; urllib.request.urlretrieve(URL,zpath)
        with zipfile.ZipFile(zpath) as z: z.extract('Online Retail.xlsx',out)
        source=out/'Online Retail.xlsx'
    print('Lendo a base original...',flush=True)
    raw=pd.read_excel(source,engine='openpyxl')
    print('Base carregada; preparando as agregacoes...',flush=True)
    audit=[]
    def record(stage, x):
        audit.append({'etapa':stage,'linhas':len(x),'clientes_identificados':int(x.CustomerID.nunique()),'notas':int(x.InvoiceNo.nunique())})
    record('Base original',raw)
    d=raw.drop_duplicates().copy(); record('Sem duplicatas exatas nas oito colunas',d)
    d=d[d.CustomerID.notna()].copy(); record('Com CustomerID',d)
    identified=d.copy()
    d=d[~d.InvoiceNo.astype(str).str.upper().str.startswith('C')].copy(); record('Sem notas iniciadas por C',d)
    d=d[d.Quantity>0].copy(); record('Quantidade positiva',d)
    d=d[d.UnitPrice>0].copy(); record('Preco unitario positivo',d)
    d['InvoiceDate']=pd.to_datetime(d.InvoiceDate,errors='coerce')
    d=d[d.InvoiceDate.notna()].copy(); record('Data valida',d)
    d['CustomerID']=d.CustomerID.astype('int64')
    d['dia']=d.InvoiceDate.dt.normalize()
    # Representacao em pence evita acumulo de erro binario no valor da linha.
    d['vendas_gbp']=(d.Quantity*d.UnitPrice*100).round().astype('int64')/100
    cutoff='2011-12-10'
    c,daily=snapshot(d,cutoff)
    m=matrix(c)
    pd.DataFrame(audit).to_csv(out/'auditoria_limpeza.csv',index=False,encoding='utf-8-sig')
    d.to_csv(out/'vendas_positivas.csv',index=False,encoding='utf-8-sig')
    daily.drop(columns='intervalo').to_csv(out/'compras_diarias.csv',index=False,encoding='utf-8-sig')
    c.reset_index().to_csv(out/'clientes_classificados.csv',index=False,encoding='utf-8-sig')
    m.reset_index().to_csv(out/'matriz_concordancia.csv',index=False,encoding='utf-8-sig')
    sensitivity=[]
    for f in [1.2,1.6,2.0]:
        cc,_=snapshot(d,cutoff,factor=f); mm=matrix(cc)
        sensitivity.append({'multiplicador':f,'clientes':len(cc),'alertas_individualizados':int(cc.alerta_individualizada.sum()),'pct_alertas':float(cc.alerta_individualizada.mean()*100),'vendas_alertas_gbp':float(cc.loc[cc.alerta_individualizada,'vendas_gbp'].sum()),'somente_fixa':int(mm.loc[GROUPS[1],'clientes']),'somente_individualizada':int(mm.loc[GROUPS[2],'clientes']),'ambas':int(mm.loc[GROUPS[3],'clientes'])})
    pd.DataFrame(sensitivity).to_csv(out/'sensibilidade.csv',index=False,encoding='utf-8-sig')
    temporal=[]
    for dt in ['2011-09-01','2011-10-01','2011-11-01',cutoff]:
        cc,_=snapshot(d,dt); mm=matrix(cc)
        temporal.append({'data_referencia':dt,'clientes_elegiveis':len(cc),'alertas_fixa':int(cc.alerta_fixa.sum()),'alertas_individualizada':int(cc.alerta_individualizada.sum()),'pct_divergencia':float((cc.alerta_fixa!=cc.alerta_individualizada).mean()*100),'somente_fixa':int(mm.loc[GROUPS[1],'clientes']),'somente_individualizada':int(mm.loc[GROUPS[2],'clientes'])})
    pd.DataFrame(temporal).to_csv(out/'cortes_temporais.csv',index=False,encoding='utf-8-sig')
    min5,_=snapshot(d,cutoff,minimum=5)
    # Reconciliacoes independentes das agregacoes principais.
    assert len(raw)==541909
    assert (c.imc_dias>0).all() and (c.recencia_dias>0).all()
    assert int(m.clientes.sum())==len(c)
    assert abs(m.vendas_gbp.sum()-c.vendas_gbp.sum())<0.001
    assert abs(d.vendas_gbp.sum()-daily.vendas_gbp.sum())<0.001
    assert (c.primeira_compra<c.ultima_compra).all()
    assert abs((c.imc_dias*(c.dias_compra-1)-(c.ultima_compra-c.primeira_compra).dt.days)).max()<1e-8
    assert all(cc>=dd for cc,dd in zip([s['alertas_individualizados'] for s in sensitivity],[s['alertas_individualizados'] for s in sensitivity][1:]))
    examples=[]
    for group in GROUPS:
        x=c[c.grupo==group].sort_values('vendas_gbp',ascending=False).head(1).reset_index()
        examples+=json.loads(x.to_json(orient='records',date_format='iso'))
    neg=identified[(identified.Quantity<0)&(identified.UnitPrice>0)]
    summary={
       'fonte':'Chen, D. (2015). Online Retail. UCI. DOI 10.24432/C5BW33. CC BY 4.0.',
       'download_url':URL,'sha256_xlsx':hashlib.sha256(source.read_bytes()).hexdigest(),
       'referencia':cutoff,'inicio':str(raw.InvoiceDate.min()),'fim':str(raw.InvoiceDate.max()),
       'auditoria':audit,'linhas_vendas':len(d),'notas_vendas':int(d.InvoiceNo.nunique()),
       'dias_cliente':len(daily),'clientes_vendas':int(d.CustomerID.nunique()),'clientes_elegiveis':len(c),
       'clientes_excluidos_poucas_compras':int(d.CustomerID.nunique()-len(c)),
       'vendas_positivas_total_gbp':float(d.vendas_gbp.sum()),'vendas_elegiveis_gbp':float(c.vendas_gbp.sum()),
       'valor_absoluto_linhas_negativas_identificadas_gbp':float(-(neg.Quantity*neg.UnitPrice).sum()),
       'maior_linha_venda_gbp':float(d.vendas_gbp.max()),'maior_cliente_pct_vendas':float(c.vendas_gbp.max()/c.vendas_gbp.sum()*100),
       'imc':{str(k):float(v) for k,v in c.imc_dias.describe(percentiles=[.1,.25,.5,.75,.9,.95]).items()},
       'cv_mediano':float(c.cv_intervalos.median()),'pct_cv_maior_1':float((c.cv_intervalos>1).mean()*100),
       'matriz':json.loads(m.reset_index().to_json(orient='records')),'sensibilidade':sensitivity,'cortes_temporais':temporal,
       'minimo_5_compras':{'clientes':len(min5),'pct_divergencia':float((min5.alerta_fixa!=min5.alerta_individualizada).mean()*100)},
       'exemplos':examples,'verificacoes':'contagens, somas, formula IMC, exclusividade de grupos e monotonicidade verificadas'
    }
    summary['janelas_antecipacao']=exportar_antecipacao_e_powerbi(c,out,cutoff)
    (out/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
