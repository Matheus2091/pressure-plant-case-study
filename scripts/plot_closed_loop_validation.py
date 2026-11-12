import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.abspath(os.path.join(base_dir, r'..\data\closed loop\PI_DATA.csv'))
paper_fig_dir = os.path.abspath(os.path.join(base_dir, r'..\images'))
images_dir = os.path.abspath(os.path.join(base_dir, r'..\images'))
os.makedirs(paper_fig_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)

df = pd.read_csv(csv_path, sep=';', decimal=',')
df = df.dropna(subset=['PV_OUT', 'SP', 'CV']).reset_index(drop=True)

N = len(df)
Ts = 0.25  # 4 Hz
sp_real = df['SP'].values
pv_real = df['PV_OUT'].values
cv_real = df['CV'].values

# Parameters from closed_loop_system_Test.m
Kp = 4.1920
Ki = 0.1500
u_min = 0.0
u_max = 100.0
p_in_nominal = 80.0

# Identified NARX 8-term parameters
theta = np.array([
    0.547532,
    0.444867,
    8.288803e-3,
    8.372271e-7,
    -6.664476e-7,
    -1.862358e-4,
    1.838539e-4,
    -3.844165e-5
])

def pressure_narx(y_hist, u_hist, pin_hist):
    terms = np.array([
        y_hist[0],
        y_hist[2],
        u_hist[2],
        u_hist[0] * (pin_hist[1]**2),
        y_hist[0] * (u_hist[0]**2),
        (y_hist[2]**2) * pin_hist[0],
        (y_hist[2]**2) * pin_hist[1],
        u_hist[2]**2
    ])
    return np.sum(theta * terms)

y_sim = np.zeros(N)
u_sim = np.zeros(N)
y_sim[:3] = pv_real[:3]
u_sim[:3] = cv_real[:3]
e_int = 0.0

for k in range(3, N):
    y_hist = [y_sim[k-1], y_sim[k-2], y_sim[k-3]]
    u_hist = [u_sim[k-1], u_sim[k-2], u_sim[k-3]]
    pin_hist = [p_in_nominal, p_in_nominal, p_in_nominal]
    
    y_k = pressure_narx(y_hist, u_hist, pin_hist)
    y_sim[k] = y_k
    
    e = sp_real[k] - y_k
    p_term = Kp * e
    e_int_cand = e_int + e * Ts
    u_unsat = p_term + Ki * e_int_cand
    u_k = np.clip(u_unsat, u_min, u_max)
    
    # Conditional integration (anti-windup by clamping)
    if (u_unsat >= u_min and u_unsat <= u_max) or \
       (u_unsat > u_max and e < 0) or \
       (u_unsat < u_min and e > 0):
        e_int = e_int_cand
        
    u_sim[k] = u_k

t_min = np.arange(N) * Ts / 60.0
rmse_pv = np.sqrt(np.mean((pv_real[3:] - y_sim[3:])**2))
rmse_cv = np.sqrt(np.mean((cv_real[3:] - u_sim[3:])**2))

print(f"Closed-loop validation results:")
print(f" - Pressure (PV_OUT) RMSE: {rmse_pv:.4f} psi")
print(f" - Control action (CV) RMSE: {rmse_cv:.4f} %")

# IFAC formatting
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 8.5,
    'axes.labelsize': 8.5,
    'axes.titlesize': 8.5,
    'xtick.labelsize': 8.0,
    'ytick.labelsize': 8.0,
    'legend.fontsize': 7.0,
    'lines.linewidth': 1.0,
    'grid.linewidth': 0.4,
    'grid.alpha': 0.45,
    'grid.linestyle': '--',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'mathtext.fontset': 'cm'
})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.4, 3.6), sharex=True)
plt.subplots_adjust(left=0.18, right=0.94, top=0.95, bottom=0.22, hspace=0.16)

# Subplot 1: CV
ax1.plot(t_min, cv_real, color='#377eb8', linewidth=0.85, label='Measured (Plant)')
ax1.plot(t_min, u_sim, color='#e41a1c', linestyle='--', linewidth=0.9, label=f'Simulated PI (RMSE: {rmse_cv:.1f}%)')
ax1.set_ylabel(r'Valve $\mathrm{CV}$ (%)', fontweight='bold')
ax1.set_ylim(-5, 65)
ax1.grid(True)
ax1.legend(loc='upper right', frameon=True, fontsize=6.5)

# Subplot 2: PV and SP
ax2.plot(t_min, sp_real, color='black', linestyle=':', linewidth=1.0, label='Setpoint (SP)')
ax2.plot(t_min, pv_real, color='#2b5c8f', linewidth=0.9, label='Measured (Plant)')
ax2.plot(t_min, y_sim, color='#e41a1c', linestyle='--', linewidth=0.95, label=f'NARX Simulation ({rmse_pv:.2f} psi)')
ax2.set_xlabel('Time (min)')
ax2.set_ylabel(r'Vessel $P_{\mathrm{out}}$ (psi)', fontweight='bold')
ax2.set_ylim(0, 42)
ax2.grid(True)
ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.34), ncol=3, frameon=True,
           facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=6.8,
           columnspacing=0.6, handletextpad=0.3, borderpad=0.2)

for ext in ['pdf', 'png']:
    fig.savefig(os.path.join(paper_fig_dir, f'PI_Control_Comparison.{ext}'), dpi=300)
    fig.savefig(os.path.join(images_dir, f'PI_Control_Comparison.{ext}'), dpi=300)

print("Saved PI_Control_Comparison.png and .pdf in paper/fig and images/")

