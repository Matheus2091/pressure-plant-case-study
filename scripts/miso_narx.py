


import numpy as np
from itertools import combinations_with_replacement

try:
    from sysid import frols_py
except ImportError:
    import subprocess
    import sys
    print("Instaling sysid package...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'git+https://github.com/helonayala/sysid.git'])
    from sysid import frols_py


class MISONARX:
    
    #y(k) = F(y(k-1)...y(k-ny), u1(k-1)...u1(k-nu1), u2(k-1)...u2(k-nu2)...)

    def __init__(self, ny: int = 2, nu_dict: dict = None, poly_order_l: int = 2, n_components: int = 6):
    
        self.ny = int(ny)
        self.nu_dict = nu_dict if nu_dict is not None else {'u1': 2, 'u2': 2}
        self.poly_order_l = int(poly_order_l)
        self.n_components = int(n_components)
        
        self.input_names = list(self.nu_dict.keys())
        self.max_lag = max(self.ny, max(self.nu_dict.values()) if self.nu_dict else 0)
        
        # Traing results -------------------------------------------------------------------

        self.theta_ = None
        self.selected_P_colnames_ = None
        self.selected_indices_ = None
        self.fit_results_ = None
        self.P_candidate_colnames_ = None
        self._recipes_ = None
        self._sel_recipes_ = None
        self._base_names_ = None

    def _setup_recipes(self):
        base_names = []
        if self.ny > 0:
            base_names.extend([f"y(k-{i})" for i in range(1, self.ny + 1)])
        for name in self.input_names:
            nu = self.nu_dict[name]
            if nu > 0:
                base_names.extend([f"{name}(k-{i})" for i in range(1, nu + 1)])
        
        self._base_names_ = base_names
        num_base = len(base_names)
        
       #  (0)
        recipes = [()]  
        cand_names = ['constant']
        
        # (1)
        for i in range(num_base):
            recipes.append((i,))
            cand_names.append(base_names[i])
            
        # (2 to poly_order_l)
        if self.poly_order_l >= 2 and num_base > 0:
            for deg in range(2, self.poly_order_l + 1):
                for comb in combinations_with_replacement(range(num_base), deg):
                    recipes.append(comb)
                    cand_names.append("*".join([base_names[idx] for idx in comb]))
                    
        self._recipes_ = recipes
        self.P_candidate_colnames_ = cand_names

    def _build_candidate_matrix(self, y_signal, u_dict):

        N = len(y_signal)
        NP = N - self.max_lag
        if NP <= 0:
            return np.empty((0, len(self._recipes_))), np.empty((0,))
            
        rows = []
        for k in range(self.max_lag, N):
            row = []
            if self.ny > 0:
                row.extend([y_signal[k - i] for i in range(1, self.ny + 1)])
            for name in self.input_names:
                u_sig = u_dict[name]
                nu = self.nu_dict[name]
                row.extend([u_sig[k - i] for i in range(1, nu + 1)])
            rows.append(row)
            
        P0 = np.array(rows, dtype=float)

        
        cand_cols = [np.ones((NP, 1), dtype=float)]
        for r in self._recipes_[1:]:
            col = np.prod(P0[:, list(r)], axis=1, keepdims=True)
            cand_cols.append(col)
            
        P_cand = np.concatenate(cand_cols, axis=1)
        y_target = y_signal[self.max_lag:].astype(float)
        return P_cand, y_target

    def fit(self, datasets):

        if isinstance(datasets, tuple):
            datasets = [datasets]
            
        self._setup_recipes()
        
        P_blocks, Y_blocks = [], []
        for y_i, u_dict_i in datasets:
            y_arr = np.asarray(y_i, dtype=float)
            u_dict_arr = {k: np.asarray(v, dtype=float) for k, v in u_dict_i.items()}
            P_i, Y_i = self._build_candidate_matrix(y_arr, u_dict_arr)
            if P_i.shape[0] > 0:
                P_blocks.append(P_i)
                Y_blocks.append(Y_i)
                
        if not P_blocks:
            raise ValueError("NO data usable after lags.") 
            
        P_matrix = np.vstack(P_blocks)
        Y_matrix = np.concatenate(Y_blocks)
        
        frols_res = frols_py(P_matrix, Y_matrix, self.n_components, self.P_candidate_colnames_)
        
        self.theta_ = frols_res['th']
        self.selected_P_colnames_ = frols_res['Psel_colnames']
        self.selected_indices_ = frols_res['selected_indices']
        self.fit_results_ = frols_res
        self._sel_recipes_ = [self._recipes_[idx] for idx in self.selected_indices_]
        
        return self

    def print(self):
        if self.theta_ is None or len(self.theta_) == 0:
            print("Model not fitted or no terms selected") 
            return
            
        err = self.fit_results_['ERR_values']
        print("=" * 65)
        print("MISO NARX — Selected Terms")
        print("=" * 65)
        print(f"Max Lag: {self.max_lag} (ny={self.ny}, nu={self.nu_dict}, l={self.poly_order_l})")
        print(f"{'#':<4} {'Term':<38} {'Theta':>10}  {'ERR (%)':>10}")
        print("-" * 65)
        for i, term in enumerate(self.selected_P_colnames_):
            err_pct = err[i] * 100 if i < len(err) else float('nan')
            print(f"{i + 1:<4} {term:<38} {self.theta_[i]:>10.4e}  {err_pct:>10.4f}")
        print("-" * 65)
        print(f"ERR explained: {np.sum(err) * 100:.6f}%\n") #

    def predict(self, y_series, u_dict, mode='OSA'):
        if self.theta_ is None or len(self.theta_) == 0:
            raise RuntimeError("Model not fitted before predict().")

        y_arr = np.asarray(y_series, dtype=float)
        u_dict_arr = {k: np.asarray(v, dtype=float) for k, v in u_dict.items()}
        N = len(y_arr)
        
        if mode == 'OSA':
            P_cand, y_target = self._build_candidate_matrix(y_arr, u_dict_arr)
            P_sel = P_cand[:, self.selected_indices_]
            y_hat_osa = P_sel @ self.theta_
            return y_hat_osa, y_target
            
        elif mode == 'FR':
            y_hat_fr = np.zeros(N)
            y_hat_fr[:self.max_lag] = y_arr[:self.max_lag]
            
            for k in range(self.max_lag, N):
    
                base = []
                if self.ny > 0:
                    base.extend([y_hat_fr[k - i] for i in range(1, self.ny + 1)])
                for name in self.input_names:
                    u_sig = u_dict_arr[name]
                    nu = self.nu_dict[name]
                    base.extend([u_sig[k - i] for i in range(1, nu + 1)])



                
                val = 0.0
                for j, r in enumerate(self._sel_recipes_):
                    term_val = 1.0 if len(r) == 0 else np.prod([base[idx] for idx in r])
                    val += self.theta_[j] * term_val
                y_hat_fr[k] = val
                
            return y_hat_fr[self.max_lag:]
            
        else:
            raise ValueError(f"Unknown mode: {mode}. Choose 'OSA' or 'FR'.")
