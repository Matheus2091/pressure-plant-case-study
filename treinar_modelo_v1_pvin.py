import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from sysid import NARX
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'git+https://github.com/helonayala/sysid.git'])
    from sysid import NARX

data_path = r'c:\Users\mathe\OneDrive\Desktop\IHM_Press_V3\IHM_Press_V3\IHM_Press\Dataset_NARX\data\RAMPADEGRAIS1_processed.csv'

df = pd.read_csv(data_path, sep=';', decimal=',')
df = df.dropna(subset=['CV', 'PV_IN'])

u_train = df['CV'].values
y_train = df['PV_IN'].values

print(f"Dados carregados! Total de amostras: {len(u_train)}")

# V1 - Melhorias nos Hiperparâmetros
# 1. Aumentamos a janela de memória do passado (de 2 para 5 segundos)
# 2. Aumentamos o número de termos da equação (de 4 para 12)
n_components = 12
nu_model = 5
ny_model = 5
poly_order_model = 3

print(f"Treinando o modelo_V1 (PV_IN) com ny={ny_model}, nu={nu_model}, l={poly_order_model}, termos={n_components}...")
modelo_V1 = NARX(nu=nu_model, ny=ny_model, poly_order_l=poly_order_model, n_components=n_components)
modelo_V1.fit(u_train, y_train)

print("\n--- Termos Selecionados ---")
modelo_V1.print()

print("\nRodando predição OSA...")
y_hat_osa, y_target_osa = modelo_V1.predict(u_train, y_train, mode='OSA')
mse_osa = np.mean((y_target_osa - y_hat_osa)**2)

print("Rodando simulação FR (Free-Run)...")
max_lag = modelo_V1._max_lag_internal_
y_initial_conditions_fr = y_train[:max_lag]
u_sequence_for_fr = u_train

y_hat_fr = modelo_V1.predict(u_sequence_for_fr,
                              y_history_for_lags_or_osa=y_initial_conditions_fr,
                              mode='FR')

y_actual_for_fr_comparison = y_train[max_lag:]
min_len = min(len(y_hat_fr), len(y_actual_for_fr_comparison))
mse_fr = np.mean((y_actual_for_fr_comparison[:min_len] - y_hat_fr[:min_len])**2)

print(f"MSE OSA: {mse_osa:.4f}")
print(f"MSE Free-Run: {mse_fr:.4f}")

plt.figure(figsize=(14, 10))

plt.subplot(2, 1, 1)
plt.plot(y_target_osa, label='Sinal Real (PV_IN)', alpha=0.8, color='green')
plt.plot(y_hat_osa, label='Predição OSA', linestyle='--', alpha=0.9, color='orange')
plt.title(f'One-Step-Ahead (OSA) - modelo_V1 (PV_IN) | MSE: {mse_osa:.4f}')
plt.xlabel('Amostras (s)')
plt.ylabel('Pressão (PV_IN)')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(y_actual_for_fr_comparison[:min_len], label='Sinal Real (PV_IN)', alpha=0.8, color='green')
plt.plot(y_hat_fr[:min_len], label='Simulação FR', linestyle='--', alpha=0.9, color='red')
plt.title(f'Free-Run (FR) - modelo_V1 (PV_IN) | MSE: {mse_fr:.4f}')
plt.xlabel('Amostras (s)')
plt.ylabel('Pressão (PV_IN)')
plt.legend()
plt.grid(True)

plt.tight_layout()

plot_dir = r'c:\Users\mathe\OneDrive\Desktop\IHM_Press_V3\IHM_Press_V3\IHM_Press\Dataset_NARX\images'
plot_path = os.path.join(plot_dir, 'modelo_V1_pvin_plot.png')
plt.savefig(plot_path)
plt.close()

print(f"\nGráfico salvo com sucesso em: {plot_path}")
