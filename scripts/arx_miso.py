import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.linalg import solve

def MGS(P):

  # Modified Gram-Schmidt (MGS) algorithm for QR decomposition of matrix P

    n_rows, n_cols = P.shape
    A = np.eye(n_cols, dtype=float)
    P_curr = P.astype(float)
    Q = np.zeros_like(P_curr, dtype=float)
    for i in range(n_cols):
        Q[:, i] = P_curr[:, i]
        for j in range(i + 1, n_cols):
            q_i_norm_sq = Q[:, i].T @ Q[:, i]
            if q_i_norm_sq > 1e-18:
                A[i, j] = (Q[:, i].T @ P_curr[:, j]) / q_i_norm_sq
                P_curr[:, j] = P_curr[:, j] - A[i, j] * Q[:, i]
    return Q, A


def ols(P, Y_target):
    
    niter = P.shape[1]
    W, A = MGS(P)
    g = np.zeros(niter)
    for i in range(niter):
        denom = (W[:, i].T @ W[:, i]).item()
        g[i] = (Y_target.T @ W[:, i]).item() / denom if denom > 1e-18 else 0.0
    g = g.reshape(-1, 1)

    ERR = np.zeros(niter)
    y_norm_sq = (Y_target.T @ Y_target).item()
    for i in range(niter):
        denom = y_norm_sq * (W[:, i].T @ W[:, i]).item()
        ERR[i] = ((Y_target.T @ W[:, i]).item() ** 2) / denom if denom > 1e-18 else 0.0

    ESR = 1.0 - np.sum(ERR)
    th_OLS = solve(A, g)
    return th_OLS, ERR, ESR


def build_matrix(u_dict, y, ny, nu_dict, include_constant=True):

    N = len(y)
    max_lag = ny
    for nu in nu_dict.values():
        if nu > max_lag:
            max_lag = nu

    regressor_names = []
    regressor_cols = []

    for lag in range(1, ny + 1):
        regressor_names.append(f"y(k-{lag})")
        regressor_cols.append(y[max_lag - lag : N - lag])

    for input_name, u_vals in u_dict.items():
        nu = nu_dict[input_name]
        for lag in range(1, nu + 1):
            regressor_names.append(f"{input_name}(k-{lag})")
            regressor_cols.append(u_vals[max_lag - lag : N - lag])

    if include_constant:
        regressor_names.append("constant")
        regressor_cols.append(np.ones(N - max_lag))

    P = np.column_stack(regressor_cols)
    Y = y[max_lag:]
    return P, Y, regressor_names, max_lag

# ==============================================================================


class ARX_MISO_OLS:
   
    def __init__(self, ny=3, nu_dict=None, rho=0.01, include_constant=True):
        
        self.ny = ny
        self.nu_dict = nu_dict if nu_dict is not None else {'CV': 2, 'PV_IN': 2}
        self.rho = rho
        self.include_constant = include_constant

        self.max_lag = max(self.ny, max(self.nu_dict.values()))
        self.theta = None
        self.selected_indices = None
        self.selected_terms_names = []
        self.all_regressor_names = []
        self.selected_terms_info = []

    def fit(self, u_dict, y):
        P, Y, all_names, _ = build_matrix(
            u_dict, y, self.ny, self.nu_dict, self.include_constant
        )
        self.all_regressor_names = all_names
        #ERR ==================================
        _, ERR, _ = ols(P, Y)

        sorted_indices = np.argsort(ERR)[::-1]
        cumulative_err = 0.0
        selected_indices = []
        self.selected_terms_info = []

        if 0 < self.rho < 1:
            target_err = 1.0 - self.rho
            for idx in sorted_indices:
                if cumulative_err < target_err or len(selected_indices) == 0:
                    selected_indices.append(idx)
                    cumulative_err += ERR[idx]
                    self.selected_terms_info.append({
                        'name': all_names[idx],
                        'err': ERR[idx],
                        'original_index': idx
                    })
        elif self.rho >= 1:
            num_terms = int(self.rho)
            for i in range(min(num_terms, len(sorted_indices))):
                idx = sorted_indices[i]
                selected_indices.append(idx)
                cumulative_err += ERR[idx]
                self.selected_terms_info.append({
                    'name': all_names[idx],
                    'err': ERR[idx],
                    'original_index': idx
                })
        self.selected_indices = sorted(selected_indices)
        self.selected_terms_names = [all_names[i] for i in self.selected_indices]

        P_selected = P[:, self.selected_indices]
        self.theta, _, _ = ols(P_selected, Y)

    def print_model_summary(self):
        print("\n" + "=" * 65)
        print("ARX SELECTED TERMS AND ERR:")
        print("=" * 65)
        print(f"{'Order':<8}{'Term':<18}{'ERR (%)':>12}{'Coefficient':>22}")
        print("-" * 65)

        sorted_info = sorted(self.selected_terms_info, key=lambda x: x['err'], reverse=True)
        for rank, term_info in enumerate(sorted_info, 1):
            theta_idx = self.selected_indices.index(term_info['original_index'])
            coeff = self.theta[theta_idx].item()
            print(f"{rank:<8}{term_info['name']:<18}{term_info['err']*100:>11.4f}%{coeff:>22.6e}")
        print("=" * 65)

        termos_str = []
        for i, idx in enumerate(self.selected_indices):
            coeff = self.theta[i].item()
            name = self.all_regressor_names[idx]
            sinal = "+" if coeff >= 0 else "-"
            val = abs(coeff)
            termo_fmt = f"{val:.6e}" if name == "constant" else f"{val:.6e} * {name}"
            if i == 0:
                termos_str.append(f"{'-' if coeff < 0 else ''}{termo_fmt}")
            else:
                termos_str.append(f"{sinal} {termo_fmt}")

        equacao = "y(k) = " + " ".join(termos_str)
        print("\nModel Equation:")
        print(equacao)
        print("=" * 65 + "\n")

    def predict(self, u_dict, y, prediction_type='OSA'):

        # Simulates the output: ===================================================================================

        N = len(y)
        P, _, _, max_lag = build_matrix(
            u_dict, y, self.ny, self.nu_dict, self.include_constant
        )

        if prediction_type == 'OSA':
            P_selected = P[:, self.selected_indices]
            y_hat = np.zeros(N)
            y_hat[max_lag:] = (P_selected @ self.theta).flatten()
            return y_hat[max_lag:], y[max_lag:]

        elif prediction_type == 'FR':
            y_hat_fr = np.zeros(N)
            y_hat_fr[:max_lag] = y[:max_lag]

            coeff_map = {self.all_regressor_names[idx]: self.theta[i].item()
                         for i, idx in enumerate(self.selected_indices)}

            for k in range(max_lag, N):
                val_k = 0.0
                for lag in range(1, self.ny + 1):
                    t_name = f"y(k-{lag})"
                    if t_name in coeff_map:
                        val_k += coeff_map[t_name] * y_hat_fr[k - lag]

                for input_name, u_vals in u_dict.items():
                    nu = self.nu_dict[input_name]
                    for lag in range(1, nu + 1):
                        t_name = f"{input_name}(k-{lag})"
                        if t_name in coeff_map:
                            val_k += coeff_map[t_name] * u_vals[k - lag]

                # K
                if "constant" in coeff_map:
                    val_k += coeff_map["constant"]

                y_hat_fr[k] = val_k

            return y_hat_fr[max_lag:], y[max_lag:]


# ==============================================================================
# 3. EXECUTION EXPERIMENt
# ==============================================================================

if __name__ == "__main__":
    # Dataset Random Steps_4.csv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files_path = [
        os.path.abspath(os.path.join(base_dir, r'..\data\Random Steps_4.csv')),
        os.path.abspath(os.path.join(base_dir, r'..\IHM_Press_V4\IHM_Press\RESULTADOS\Random Steps_4.csv')),
        r'c:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\data\Random Steps_4.csv',
        r'c:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\IHM_Press_V4\IHM_Press\RESULTADOS\Random Steps_4.csv'
    ]
    data_path = None
    for p in files_path:
        if os.path.exists(p):
            data_path = p
            break

    if data_path is None:
        raise FileNotFoundError("CSV File not found")

    print(f"Loading data from: {data_path}")
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
    dt = 0.25  # 4 Hz (250 ms)
    print(f"Total of samples: {num_total} (~{(num_total * dt) / 60.0:.1f} minutes of testing)")

    # 100% dos dados para Treino e Teste (validação externa será feita em script separado com dados de malha fechada)
    df_train = df.copy().reset_index(drop=True)
    df_test  = df.copy().reset_index(drop=True)

    print(f"Data Split:")
    print(f" - Train (100%): {len(df_train)} samples ({(len(df_train)*dt)/60.0:.1f} min)")
    print(f" - Test  (100%): {len(df_test)} samples ({(len(df_test)*dt)/60.0:.1f} min)\n")

    # Variables =================================================================================

    y_train = df_train[col_out].values
    u_train = {'CV': df_train[col_cv].values, 'PV_IN': df_train[col_in_filt].values}

    y_test = df_test[col_out].values
    u_test = {'CV': df_test[col_cv].values, 'PV_IN': df_test[col_in_filt].values}

    # Graphical Settings -------------------------------------------------------------------

    base_dir = os.path.dirname(os.path.abspath(__file__))
    paper_fig_dir = os.path.abspath(os.path.join(base_dir, r'..\paper\fig'))
    images_dir = os.path.abspath(os.path.join(base_dir, r'..\images'))
    os.makedirs(paper_fig_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

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

    # ==================================================================================================================
    # 4. DATA VISUALIZATION
    # ================================================================================================================

    tempo_total_min = (np.arange(num_total) * dt) / 60.0

    print("#Generating data graph...")
    fig1, (ax1, ax3) = plt.subplots(2, 1, figsize=(3.4, 3.5), sharex=True)
    plt.subplots_adjust(left=0.18, right=0.80, top=0.90, bottom=0.20, hspace=0.16)


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

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=True,
               facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=7.0,
               columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

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
    # 5. Traing model ARX DO MODELO ARX
    # ==================================================================
    # Order: 3 
    # rho = 6 
    ny_order = 3
    nu_orders = {'CV': 3, 'PV_IN': 3}
    rho = 6

    print(f"\nTreinando ARX MISO (ny={ny_order}, nu=3, selecionando {num_termos_selecionar} termos)...")
    modelo_arx = ARX_MISO_OLS(
        ny=ny_order,
        nu_dict=nu_orders,
        rho=num_termos_selecionar,
        include_constant=True
    )
    modelo_arx.fit(u_train, y_train)

    # Print resume

    modelo_arx.print_model_summary()

    # ===========================================================================================
    # 6. TRAIN AND TEST (RMSE)
    # =============================================================================
    

    y_hat_train_osa, y_tgt_train = modelo_arx.predict(u_train, y_train, 'OSA')
    y_hat_train_fr,  _           = modelo_arx.predict(u_train, y_train, 'FR')
    rmse_train_osa = np.sqrt(np.mean((y_tgt_train - y_hat_train_osa) ** 2))
    rmse_train_fr  = np.sqrt(np.mean((y_tgt_train - y_hat_train_fr) ** 2))


    
    y_hat_test_osa, y_tgt_test = modelo_arx.predict(u_test, y_test, 'OSA')
    y_hat_test_fr,  _          = modelo_arx.predict(u_test, y_test, 'FR')
    rmse_test_osa = np.sqrt(np.mean((y_tgt_test - y_hat_test_osa) ** 2))
    rmse_test_fr  = np.sqrt(np.mean((y_tgt_test - y_hat_test_fr) ** 2))

    print("=" * 55)
    print("Model Performance ARXS:") #
    print("=" * 55)
    print(f"TRAIN AND TEST DATA:")
    print(f"  - RMSE One-Step-Ahead (OSA): {rmse_train_osa:.4f} psi")
    print(f"  - RMSE Free-Run (FR):        {rmse_train_fr:.4f} psi")
    print("=" * 55)

    # ===========================================================================================
    # 7. GRAPHICAL RESULTS
    # ======================================================================================================
    tempo_test_seg = np.arange(len(y_tgt_test)) * dt
    tempo_test_min = tempo_test_seg / 60.0

    print("\nGenerating graphical results ARX...")
    fig2, (ax1, ax3) = plt.subplots(2, 1, figsize=(3.4, 3.5), sharex=True)
    plt.subplots_adjust(left=0.18, right=0.80, top=0.96, bottom=0.20, hspace=0.16)

    ax1.plot(tempo_test_min, df_test[col_cv].values[modelo_arx.max_lag:], color='#d95f02', linewidth=0.8)
    ax1.set_ylabel(r'Valve $\mathrm{CV}$ (%)', color='#d95f02', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#d95f02')
    ax1.set_ylim(-5, 115)
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(tempo_test_min, df_test[col_in_filt].values[modelo_arx.max_lag:], color='#1b9e77', linewidth=0.8)
    ax2.set_ylabel(r'Supply $P_{\mathrm{in}}$ (psi)', color='#1b9e77', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#1b9e77')
    ax2.set_ylim(58, 85)

    ax3.plot(tempo_test_min, y_tgt_test, color='black', linewidth=0.85, label='Measured')
    ax3.plot(tempo_test_min, y_hat_test_fr, color='#e41a1c', linestyle='--', linewidth=0.95, label=f'Free-Run ({rmse_test_fr:.2f})')
    ax3.plot(tempo_test_min, y_hat_test_osa, color='#7570b3', linestyle=':', linewidth=0.9, alpha=0.85, label=f'OSA ({rmse_test_osa:.2f})')
    ax3.set_xlabel('Time (min)')
    ax3.set_ylabel(r'Vessel $P_{\mathrm{out}}$ (psi)', fontweight='bold')
    ax3.set_ylim(0, 48)
    ax3.grid(True)
    ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.32), ncol=3, frameon=True,
               facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=7.0,
               columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

    for ext in ['pdf', 'png']:
        fig2.savefig(os.path.join(paper_fig_dir, f'Resultado_ARX_1.{ext}'), dpi=300)
        fig2.savefig(os.path.join(images_dir, f'Resultado_ARX_1.{ext}'), dpi=300)
    plt.show()
    print("Graphical results for ARX saved")
