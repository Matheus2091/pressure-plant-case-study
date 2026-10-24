import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from miso_narx import MISONARX

# ==============================================================================
# ⚙️ 1. CONFIGURAÇÕES DOS DADOS E VARIÁVEIS
# ==============================================================================
# Caminho do dataset Random Steps_2
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), r'..\..\RESULTADOS\Random Steps_2.csv'))

# Variáveis do ensaio
VAR_INPUT_1 = 'CV'        # Ação de controle: abertura da válvula (%)
VAR_INPUT_2 = 'PV_IN'     # Pressão de entrada da alimentação (psi)
VAR_OUTPUT  = 'PV_OUT'    # Pressão de saída do vaso (psi)

print(f"Carregando dados de: {data_path}")
df = pd.read_csv(data_path, sep=';', decimal=',')
df = df.dropna(subset=[VAR_INPUT_1, VAR_INPUT_2, VAR_OUTPUT])

y_train = df[VAR_OUTPUT].values
u_train = {
    VAR_INPUT_1: df[VAR_INPUT_1].values,
    VAR_INPUT_2: df[VAR_INPUT_2].values
}

num_amostras = len(y_train)
dt = 0.25  # Taxa de amostragem de 4 Hz (250 ms)
tempo_seg = np.arange(num_amostras) * dt
tempo_min = tempo_seg / 60.0

print(f"Total de amostras carregadas: {num_amostras} (~{tempo_min[-1]:.1f} minutos de ensaio)")
print(f"Inputs exógenos: [{VAR_INPUT_1}, {VAR_INPUT_2}]  -->  Output: [{VAR_OUTPUT}]")

# ==============================================================================
# 🧠 2. HIPERPARÂMETROS DO MODELO MISO NARX
# ==============================================================================
ny_model = 3              # 3 atrasos da saída y: y(k-1), y(k-2), y(k-3)
nu_model = {              # 3 atrasos para cada entrada
    VAR_INPUT_1: 3,
    VAR_INPUT_2: 3
}
poly_order_model = 3      # Grau 3 para capturar não linearidades e produtos cruzados
n_components = 8          # 8 termos selecionados pelo FROLS

# ==============================================================================
# 🚀 3. TREINAMENTO COM FROLS
# ==============================================================================
print(f"\nTreinando Modelo MISO NARX (ny={ny_model}, nu=3, l={poly_order_model}, termos={n_components})...")
modelo = MISONARX(ny=ny_model, nu_dict=nu_model, poly_order_l=poly_order_model, n_components=n_components)
modelo.fit((y_train, u_train))

modelo.print()

# ------------------------------------------------------------------------------
# 1. PRINT DOS TERMOS SELECIONADOS
# ------------------------------------------------------------------------------
print("\n" + "=" * 65)
print("TERMOS SELECIONADOS PELO FROLS:")
print("=" * 65)
for i, termo in enumerate(modelo.selected_P_colnames_, 1):
    print(f"  {i}. {termo}")
print("=" * 65)

# ------------------------------------------------------------------------------
# 2. PRINT DA EQUACAO DO MODELO
# ------------------------------------------------------------------------------
equacao_termos = []
for i, (termo, coef) in enumerate(zip(modelo.selected_P_colnames_, modelo.theta_)):
    sinal = "+" if coef >= 0 else "-"
    val = abs(coef)
    termo_str = f"{val:.6e}" if termo == "constant" else f"{val:.6e} * {termo}"
    if i == 0 and coef >= 0:
        equacao_termos.append(f"       {termo_str}")
    else:
        equacao_termos.append(f"     {sinal} {termo_str}")

equacao_formatada = "y(k) =\n" + "\n".join(equacao_termos)

# Versao em linha unica (facil de copiar para codigo ou documentos)
termos_inline = []
for i, (termo, coef) in enumerate(zip(modelo.selected_P_colnames_, modelo.theta_)):
    sinal = "+" if coef >= 0 else "-"
    val = abs(coef)
    termo_str = f"{val:.6e}" if termo == "constant" else f"{val:.6e}*{termo}"
    if i == 0:
        termos_inline.append(f"{'-' if coef < 0 else ''}{termo_str}")
    else:
        termos_inline.append(f"{sinal} {termo_str}")
equacao_inline = f"y(k) = {' '.join(termos_inline)}"

print("\n" + "=" * 65)
print("EQUACAO DO MODELO MISO NARX:")
print("=" * 65)
print(equacao_formatada)
print("-" * 65)
print("Linha unica:")
print(equacao_inline)
print("=" * 65 + "\n")

# ==============================================================================
# 📊 4. VALIDAÇÃO: ONE-STEP-AHEAD (OSA) E FREE-RUN (FR)
# ==============================================================================
print("Calculando predição One-Step-Ahead (OSA)...")
y_hat_osa, y_tgt = modelo.predict(y_train, u_train, mode='OSA')
mse_osa = np.mean((y_tgt - y_hat_osa)**2)

print("Calculando simulação Free-Run (Simulação Livre autoalimentada)...")
y_hat_fr = modelo.predict(y_train, u_train, mode='FR')
mse_fr = np.mean((y_tgt - y_hat_fr)**2)

# Tempo correspondente após o corte dos lags
tempo_plot_min = tempo_min[modelo.max_lag:]

print(f"\n" + "=" * 50)
print(f"Desempenho no Dataset 'Random Steps_2':")
print(f" - MSE OSA (One-Step-Ahead): {mse_osa:.6f}")
print(f" - MSE FR  (Free-Run):       {mse_fr:.4f}")
print("=" * 50)

# ==============================================================================
# 📈 5. GERAÇÃO E SALVAMENTO DOS GRÁFICOS
# ==============================================================================
plt.figure(figsize=(15, 11))

# Subplot 1: Sinais de Entrada (CV e PV_IN)
plt.subplot(3, 1, 1)
ax1 = plt.gca()
linha1 = ax1.plot(tempo_min, df[VAR_INPUT_1], color='darkorange', label='Válvula CV (%)', alpha=0.9, linewidth=1.2)
ax1.set_ylabel('Válvula CV (%)', color='darkorange', fontweight='bold')
ax1.tick_params(axis='y', labelcolor='darkorange')

ax2 = ax1.twinx()
linha2 = ax2.plot(tempo_min, df[VAR_INPUT_2], color='teal', linestyle=':', label='Pressão Entrada PV_IN (psi)', alpha=0.8, linewidth=1.2)
ax2.set_ylabel('PV_IN (psi)', color='teal', fontweight='bold')
ax2.tick_params(axis='y', labelcolor='teal')

linhas = linha1 + linha2
labels = [l.get_label() for l in linhas]
ax1.legend(linhas, labels, loc='upper right')
ax1.set_title('Sinais de Entrada Exógenos: Abertura da Válvula (CV) e Pressão da Rede (PV_IN)', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Subplot 2: One-Step-Ahead (OSA)
plt.subplot(3, 1, 2)
plt.plot(tempo_plot_min, y_tgt, label=f'Real ({VAR_OUTPUT})', color='navy', alpha=0.8, linewidth=1.2)
plt.plot(tempo_plot_min, y_hat_osa, label='Predição OSA', linestyle='--', color='crimson', alpha=0.85, linewidth=1.2)
plt.title(f'One-Step-Ahead (OSA) | MSE: {mse_osa:.6f}', fontsize=12, fontweight='bold')
plt.ylabel('Pressão (psi)')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)

# Subplot 3: Free-Run (FR)
plt.subplot(3, 1, 3)
plt.plot(tempo_plot_min, y_tgt, label=f'Real ({VAR_OUTPUT})', color='navy', alpha=0.8, linewidth=1.2)
plt.plot(tempo_plot_min, y_hat_fr, label='Simulação Livre (Free-Run)', linestyle='--', color='forestgreen', alpha=0.85, linewidth=1.2)
plt.title(f'Simulação Livre (Free-Run) — Modelo Não Realimentado por Medições Reais | MSE: {mse_fr:.4f}', fontsize=12, fontweight='bold')
plt.xlabel('Tempo Decorrido (minutos)')
plt.ylabel('Pressão (psi)')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)

plt.tight_layout()

images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), r'..\images'))
os.makedirs(images_dir, exist_ok=True)
plot_path = os.path.join(images_dir, 'modelo_miso_random_steps_plot.png')
plt.savefig(plot_path, dpi=200)
plt.close()

print(f"\nGráfico salvo com sucesso em: {plot_path}")
