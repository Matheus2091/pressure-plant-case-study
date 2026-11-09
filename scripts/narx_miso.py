import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#  -----------------------------------------------------------------------------------------------------------------

scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

try:
    from miso_narx import MISONARX
except ImportError:
    from scripts.miso_narx import MISONARX

# =============================================================================================
# 1. Loading DATA(RANDOM STEPS 4)
# =======================================================================================================================

if __name__ == "__main__":

    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidatos_caminho = [
        os.path.abspath(os.path.join(base_dir, r'..\data\Random Steps_4.csv')),
        os.path.abspath(os.path.join(base_dir, r'..\IHM_Press_V4\IHM_Press\RESULTADOS\Random Steps_4.csv')),
        r'c:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\data\Random Steps_4.csv',
        r'c:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\IHM_Press_V4\IHM_Press\RESULTADOS\Random Steps_4.csv'
    ]
    data_path = None
    for p in candidatos_caminho:
        if os.path.exists(p):
            data_path = p
            break

    if data_path is None:
        raise FileNotFoundError("Dataset not f.")

    print(f"Loading data...: {data_path}")
    df = pd.read_csv(data_path, sep=';', decimal=',')

    col_out = 'PV_OUT'
    col_cv  = 'CV'
    col_in_filt = 'PV_IN (FILTRADO)' if 'PV_IN (FILTRADO)' in df.columns else 'PV_IN'
    col_in_raw  = 'PT_IN (SEM FILTRO)' if 'PT_IN (SEM FILTRO)' in df.columns else None

    req_cols = [col_out, col_cv, col_in_filt]
    if col_in_raw:
        req_cols.append(col_in_raw)
    df = df.dropna(subset=req_cols).reset_index(drop=True)

    num_total = len(df)

    # 4 Hz (250 ms)
    dt = 0.25 
    
    print(f"Total of samples: {num_total} (~{(num_total * dt) / 60.0:.1f} minuts of test)") #

    df_train = df.copy().reset_index(drop=True)
    df_test  = df.copy().reset_index(drop=True)

    print(f"Divisão dos Dados (100% Train/Test in the identification dataset):")
    print(f" - Train (100%): {len(df_train)} samples ({(len(df_train)*dt)/60.0:.1f} min)")
    print(f" - Test  (100%): {len(df_test)} samples ({(len(df_test)*dt)/60.0:.1f} min)\n")

    #TRAINING

    y_train = df_train[col_out].values
    u_train = {'CV': df_train[col_cv].values, 'PV_IN': df_train[col_in_filt].values}

    #TESTING
    y_test = df_test[col_out].values
    u_test = {'CV': df_test[col_cv].values, 'PV_IN': df_test[col_in_filt].values}

    paper_fig_dir = os.path.abspath(os.path.join(base_dir, r'..\paper\fig'))
    images_dir = os.path.abspath(os.path.join(base_dir, r'..\images'))
    os.makedirs(paper_fig_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # Configurações de estilo para publicação (IFAC)

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

    # =============================================================================
    # ======================================================================================
    
    tempo_total_min = (np.arange(num_total) * dt) / 60.0

    print("Generating and displaying the collected data graph (Figure 1)")
    fig1, (ax1, ax3) = plt.subplots(2, 1, figsize=(3.4, 3.5), sharex=True)
    plt.subplots_adjust(left=0.18, right=0.80, top=0.90, bottom=0.20, hspace=0.16)

    # Subplot 1:
    ax1.plot(tempo_total_min, df[col_cv].values, color='#d95f02', linewidth=0.8, label=r'Valve $\mathrm{CV}$')
    ax1.set_ylabel(r'Valve $\mathrm{CV}$ (%)', color='#d95f02', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#d95f02')
    ax1.set_ylim(-5, 115)
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(tempo_total_min, df[col_in_filt].values, color='#1b9e77', linewidth=0.85, label=r'Supply $P_{\mathrm{in}}$')
    ax2.set_ylabel(r'Supply $P_{\mathrm{in}}$ (psi)', color='#1b9e77', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#1b9e77')
    ax2.set_ylim(58, 85)

    # Legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=True,
               facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=7.0,
               columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

    # Subplot 2:
    ax3.plot(tempo_total_min, df[col_out].values, color='#2b5c8f', linewidth=0.8, label='Measured (100% Train)')
    ax3.set_xlabel('Time (min)')
    ax3.set_ylabel(r'Vessel $P_{\mathrm{out}}$ (psi)', fontweight='bold')
    ax3.set_ylim(0, 50)
    ax3.grid(True)
    ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.32), ncol=1, frameon=True,
               facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=7.0,
               columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

    for ext in ['pdf', 'png']:
        fig1.savefig(os.path.join(paper_fig_dir, f'Random Steps_4.{ext}'), dpi=300)
        fig1.savefig(os.path.join(images_dir, f'Random Steps_4.{ext}'), dpi=300)
    plt.show()

    # ==========================================================================

    ny_model = 3 
    nu_model = {               
        'CV': 3,
        'PV_IN': 3
    }
    poly_order_model = 3       
    n_components = 8          

    print(f"\nTraining Model NARX (ny={ny_model}, nu=3, grade={poly_order_model}, terms={n_components})...") 
    modelo_narx = MISONARX(
        ny=ny_model,
        nu_dict=nu_model,
        poly_order_l=poly_order_model,
        n_components=n_components
    )
    modelo_narx.fit((y_train, u_train))

    modelo_narx.print()

    termos_inline = []
    for i, (termo, coef) in enumerate(zip(modelo_narx.selected_P_colnames_, modelo_narx.theta_)):
        sinal = "+" if coef >= 0 else "-"
        val = abs(coef)
        termo_str = f"{val:.6e}" if termo == "constant" else f"{val:.6e} * {termo}"
        if i == 0:
            termos_inline.append(f"{'-' if coef < 0 else ''}{termo_str}")
        else:
            termos_inline.append(f"{sinal} {termo_str}")
    equacao_inline = f"y(k) = {' '.join(termos_inline)}"

    print("Equação do Modelo MISO NARX:")
    print(equacao_inline)
    print("=" * 65 + "\n")

    # ==========================================================================
    # 4. (RMSE)
    # ==========================================================================

    y_hat_train_osa, y_tgt_train = modelo_narx.predict(y_train, u_train, mode='OSA')
    y_hat_train_fr = modelo_narx.predict(y_train, u_train, mode='FR')
    rmse_train_osa = np.sqrt(np.mean((y_tgt_train - y_hat_train_osa) ** 2))
    rmse_train_fr  = np.sqrt(np.mean((y_tgt_train - y_hat_train_fr) ** 2))

    y_hat_test_osa, y_tgt_test = modelo_narx.predict(y_test, u_test, mode='OSA')
    y_hat_test_fr = modelo_narx.predict(y_test, u_test, mode='FR')
    rmse_test_osa = np.sqrt(np.mean((y_tgt_test - y_hat_test_osa) ** 2))
    rmse_test_fr  = np.sqrt(np.mean((y_tgt_test - y_hat_test_fr) ** 2))

    print("=" * 55)
    print("NARX PERFORMANCE: ")  
    print("=" * 55)
    print(f"Train/Test Set:") 
    print(f"  - RMSE One-Step-Ahead (OSA): {rmse_train_osa:.4f} psi")
    print(f"  - RMSE Free-Run (FR):        {rmse_train_fr:.4f} psi")
    print("=" * 55)

    # ===========================================================================================
    # 5.Graphical Results
    # =======================================================================================

    tempo_test_seg = np.arange(len(y_tgt_test)) * dt
    tempo_test_min = tempo_test_seg / 60.0

    print("\nNARX test results graph...")
    fig3, (ax1, ax3) = plt.subplots(2, 1, figsize=(3.4, 3.5), sharex=True)
    plt.subplots_adjust(left=0.18, right=0.80, top=0.96, bottom=0.20, hspace=0.16)

    # Subplot 1: Sinais de Excitação do Teste
    ax1.plot(tempo_test_min, df_test[col_cv].values[modelo_narx.max_lag:], color='#d95f02', linewidth=0.8)
    ax1.set_ylabel(r'Valve $\mathrm{CV}$ (%)', color='#d95f02', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#d95f02')
    ax1.set_ylim(-5, 115)
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(tempo_test_min, df_test[col_in_filt].values[modelo_narx.max_lag:], color='#1b9e77', linewidth=0.8)
    ax2.set_ylabel(r'Supply $P_{\mathrm{in}}$ (psi)', color='#1b9e77', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#1b9e77')
    ax2.set_ylim(58, 85)

    # Subplot 2: Resposta do Modelo vs Medição Real
    ax3.plot(tempo_test_min, y_tgt_test, color='black', linewidth=0.85, label='Measured')
    ax3.plot(tempo_test_min, y_hat_test_fr, color='#377eb8', linestyle='--', linewidth=0.95, label=f'Free-Run ({rmse_test_fr:.2f})')
    ax3.plot(tempo_test_min, y_hat_test_osa, color='#4daf4a', linestyle=':', linewidth=0.9, alpha=0.85, label=f'OSA ({rmse_test_osa:.2f})')
    ax3.set_xlabel('Time (min)')
    ax3.set_ylabel(r'Vessel $P_{\mathrm{out}}$ (psi)', fontweight='bold')
    ax3.set_ylim(0, 48)
    ax3.grid(True)
    ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.32), ncol=3, frameon=True,
               facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=7.0,
               columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

    for ext in ['pdf', 'png']:
        fig3.savefig(os.path.join(paper_fig_dir, f'Resultados_NARX_1.{ext}'), dpi=300)
        fig3.savefig(os.path.join(images_dir, f'Resultados_NARX_1.{ext}'), dpi=300)
    plt.show()
    print("NARX graphs saved successfully! ")
