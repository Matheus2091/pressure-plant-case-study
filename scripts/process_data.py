import pandas as pd
import matplotlib.pyplot as plt
import os

files = [
    r'..\raw_data\TESTE1.csv',
    r'..\raw_data\RAMPADEGRAIS1.csv',
    r'..\raw_data\SEMIESTÁTICA 2.csv'
]

for file_path in files:
    dir_path = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Lê os dados (delimitador é ; e separador decimal é ,)
    df = pd.read_csv(file_path, sep=';', decimal=',')
    
    # Padroniza a nomenclatura (se houver PV_OUT, converte para PV_LOAD)
    if 'PV_OUT' in df.columns:
        df = df.rename(columns={'PV_OUT': 'PV_LOAD'})
    
    # Força a conversão das colunas para numérico
    for col in ['PV_LOAD', 'CV', 'PV_IN']:
        if col in df.columns:
            # Sempre converte para string, substitui a vírgula e converte para numérico
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    # Cria a coluna de tempo em segundos (amostragem de 1s)
    df['Time_s'] = df.index * 1.0
    
    # Salva o dataframe atualizado em um novo arquivo CSV
    processed_file_path = os.path.join('..\data', f'{base_name}_processed.csv')
    df.to_csv(processed_file_path, sep=';', decimal=',', index=False)
    
    # Plota os dados
    plt.figure(figsize=(12, 8))
    
    # Verifica se as colunas existem antes de plotar para evitar erros
    if 'PV_LOAD' in df.columns:
        plt.plot(df['Time_s'], df['PV_LOAD'], label='PV_LOAD')
    if 'CV' in df.columns:
        plt.plot(df['Time_s'], df['CV'], label='CV')
    if 'PV_IN' in df.columns:
        plt.plot(df['Time_s'], df['PV_IN'], label='PV_IN')
        
    plt.title(f'Dados de Aquisição - {base_name} (Amostragem: 1s)')
    plt.xlabel('Tempo (Segundos)')
    plt.ylabel('Valores')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Salva o gráfico como imagem
    plot_path = os.path.join('..\images', f'{base_name}_plot.png')
    plt.savefig(plot_path)
    plt.close()
    
    print(f"Processado: {base_name}")
    print(f"  Dados salvos em: {processed_file_path}")
    print(f"  Gráfico salvo em: {plot_path}")


