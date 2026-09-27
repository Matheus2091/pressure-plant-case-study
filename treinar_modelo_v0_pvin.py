import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Garante que a biblioteca sysid está instalada
try:
    from sysid import NARX
except ImportError:
    import subprocess
    import sys
    print("Instalando a biblioteca sysid...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'git+https://github.com/helonayala/sysid.git'])
    from sysid import NARX

# Caminho do Dataset da Rampa de Degraus
data_path = r'c:\Users\mathe\OneDrive\Desktop\IHM_Press_V3\IHM_Press_V3\IHM_Press\Dataset_NARX\data\RAMPADEGRAIS1_processed.csv'

# Carregamento e preparação dos dados
df = pd.read_csv(data_path, sep=';', decimal=',')
df = df.dropna(subset=['CV', 'PV_IN']) # Garante que não teremos NaNs para PV_IN

# Variável de Controle (u) e Variável de Processo (y) alterada para PV_IN
u_train = df['CV'].values
y_train = df['PV_IN'].values

print(f"Dados carregados! Total de amostras: {len(u_train)}")

# 1. Definição dos parâmetros do modelo (baseado na receita)
n_components = 4
nu_model = 2
ny_model = 2
poly_order_model = 3

print("Treinando o modelo_V0 (com PV_IN)...")
# 2. Instanciar e treinar o modelo
modelo_V0 = NARX(nu=nu_model, ny=ny_model, poly_order_l=poly_order_model, n_components=n_components)
modelo_V0.fit(u_train, y_train)

print("\n--- Termos Selecionados ---")
modelo_V0.print()

# 3. One-Step-Ahead (OSA) Prediction
print("\nRodando predição OSA...")
y_hat_osa, y_target_osa = modelo_V0.predict(u_train, y_train, mode='OSA')
mse_osa = np.mean((y_target_osa - y_hat_osa)**2)
print(f"MSE OSA: {mse_osa:.4f}")

# 4. Free-Run (FR) Simulation
print("Rodando simulação FR (Free-Run)...")
max_lag = modelo_V0._max_lag_internal_

y_initial_conditions_fr = y_train[:max_lag]
u_sequence_for_fr = u_train

y_hat_fr = modelo_V0.predict(u_sequence_for_fr,
                              y_history_for_lags_or_osa=y_initial_conditions_fr,
                              mode='FR')

y_actual_for_fr_comparison = y_train[max_lag:]
min_len = min(len(y_hat_fr), len(y_actual_for_fr_comparison))

mse_fr = np.mean((y_actual_for_fr_comparison[:min_len] - y_hat_fr[:min_len])**2)
print(f"MSE Free-Run: {mse_fr:.4f}")

# 5. Plotagem e salvamento
plt.figure(figsize=(14, 10))

# Subplot OSA
plt.subplot(2, 1, 1)
plt.plot(y_target_osa, label='Sinal Real (PV_IN)', alpha=0.8, color='green')
plt.plot(y_hat_osa, label='Predição OSA', linestyle='--', alpha=0.9, color='orange')
plt.title(f'One-Step-Ahead (OSA) - modelo_V0 (PV_IN) | MSE: {mse_osa:.4f}')
plt.xlabel('Amostras (s)')
plt.ylabel('Pressão (PV_IN)')
plt.legend()
plt.grid(True)

# Subplot FR
plt.subplot(2, 1, 2)
plt.plot(y_actual_for_fr_comparison[:min_len], label='Sinal Real (PV_IN)', alpha=0.8, color='green')
plt.plot(y_hat_fr[:min_len], label='Simulação FR', linestyle='--', alpha=0.9, color='red')
plt.title(f'Free-Run (FR) - modelo_V0 (PV_IN) | MSE: {mse_fr:.4f}')
plt.xlabel('Amostras (s)')
plt.ylabel('Pressão (PV_IN)')
plt.legend()
plt.grid(True)

plt.tight_layout()

# Salva a imagem na pasta de imagens do projeto
plot_dir = r'c:\Users\mathe\OneDrive\Desktop\IHM_Press_V3\IHM_Press_V3\IHM_Press\Dataset_NARX\images'
plot_path = os.path.join(plot_dir, 'modelo_V0_pvin_plot.png')
plt.savefig(plot_path)
plt.close()

print(f"\nGráfico salvo com sucesso em: {plot_path}")
