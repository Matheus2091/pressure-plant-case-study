import pandas as pd
import matplotlib.pyplot as plt
import os

processed_file_path = r'c:\Users\mathe\OneDrive\Desktop\IHM_Press_V3\IHM_Press_V3\IHM_Press\SEMIESTÁTICA 1_processed.csv'
dir_path = os.path.dirname(processed_file_path)

# Lê os dados do arquivo processado editado pelo usuário
try:
    df = pd.read_csv(processed_file_path, sep=';', decimal=',')
except Exception as e:
    # Caso o usuário tenha salvo com pontuação diferente, tenta com padrão
    df = pd.read_csv(processed_file_path, sep=';')

# Para garantir, substituímos vírgulas caso o pandas não tenha lido corretamente
for col in ['PV_LOAD', 'CV', 'PV_IN']:
    if col in df.columns and df[col].dtype == object:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

plt.figure(figsize=(12, 8))

if 'Time_s' not in df.columns:
    df['Time_s'] = df.index * 1.0

if 'PV_LOAD' in df.columns:
    plt.plot(df['Time_s'], df['PV_LOAD'], label='PV_LOAD')
if 'CV' in df.columns:
    plt.plot(df['Time_s'], df['CV'], label='CV')
if 'PV_IN' in df.columns:
    plt.plot(df['Time_s'], df['PV_IN'], label='PV_IN')
    
plt.title('Dados de Aquisição - SEMIESTÁTICA 1 (Atualizado)')
plt.xlabel('Tempo (Segundos)')
plt.ylabel('Valores')
plt.legend()
plt.grid(True)
plt.tight_layout()

plot_path = os.path.join(dir_path, 'SEMIESTÁTICA 1_plot.png')
plt.savefig(plot_path)
plt.close()

print(f"Plot salvo em: {plot_path}")

