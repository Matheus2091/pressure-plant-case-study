import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==============================================================================
# CONFIGURAÇÃO DE ENTRADA E SAÍDA
# ==============================================================================
# CSV de entrada padrão: Ensaio experimental de degraus aleatórios
ARQUIVO_CSV_PADRAO = r"..\data\Random Steps_4.csv"

# Nome base do arquivo de imagem que será gerado (.png e .pdf)
NOME_SAIDA_FIGURA = "acquisition_data"

# Pasta onde a imagem gerada será salva:
PASTA_IMAGENS_DESTINO = r"..\images"

# Outros parâmetros (usados apenas quando o CSV for um ensaio gravado da bancada):
DT_PADRAO = 0.25               # Período de amostragem (250 ms = 4 Hz)
DESTACAR_TREINO_TESTE = False  # True para colorir divisão 50% Treino / 50% Teste
UNIDADE_TEMPO = "min"          # "min" (minutos) ou "s" (segundos)

# ==============================================================================
# ESTILO VISUAL PADRÃO IFAC (300 DPI, SERIF)
# ==============================================================================
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


def plotar_e_salvar(caminho_csv, nome_saida=None, pasta_destino=None, dt=0.25, mostrar_split=False, unidade_tempo="min"):
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if pasta_destino is None:
        pasta_destino = os.path.abspath(os.path.join(base_dir, PASTA_IMAGENS_DESTINO))
    else:
        pasta_destino = os.path.abspath(pasta_destino)
        
    os.makedirs(pasta_destino, exist_ok=True)

    # Pasta paper/fig como espelho adicional para compilar no LaTeX
    paper_fig_dir = os.path.abspath(os.path.join(base_dir, r"..\paper\fig"))
    os.makedirs(paper_fig_dir, exist_ok=True)

    if nome_saida is None:
        nome_saida = os.path.splitext(os.path.basename(caminho_csv))[0]

    # Detecta formato do arquivo pela primeira linha
    with open(caminho_csv, "r", encoding="utf-8", errors="ignore") as f:
        primeira_linha = f.readline().strip()

    # Formato 1: CSV de 2 colunas do MATLAB (tempo, CV)
    if ";" not in primeira_linha and "," in primeira_linha:
        df = pd.read_csv(caminho_csv, header=None, names=["t_s", "cv"])
        t = df["t_s"].values / 60.0 if unidade_tempo == "min" else df["t_s"].values
        cv = df["cv"].values

        fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.0))
        plt.subplots_adjust(left=0.16, right=0.96, top=0.94, bottom=0.22)

        ax.plot(t, cv, color="#d95f02", linewidth=0.9, label=r"Valve $\mathrm{CV}$ (%)")
        ax.set_xlabel("Time (min)" if unidade_tempo == "min" else "Time (s)")
        ax.set_ylabel(r"Valve $\mathrm{CV}$ (%)", color="#d95f02", fontweight="bold")
        ax.tick_params(axis="y", labelcolor="#d95f02")
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-5, 108)
        ax.grid(True)

    # Formato 2: CSV adquirido na bancada pelo Elipse E3
    else:
        df = pd.read_csv(caminho_csv, sep=";", decimal=",")
        col_out = "PV_OUT" if "PV_OUT" in df.columns else ("PV_LOAD" if "PV_LOAD" in df.columns else df.columns[0])
        col_cv = "CV" if "CV" in df.columns else df.columns[1]
        col_in = "PV_IN (FILTRADO)" if "PV_IN (FILTRADO)" in df.columns else ("PV_IN" if "PV_IN" in df.columns else df.columns[2])

        df = df.dropna(subset=[col_out, col_cv, col_in]).reset_index(drop=True)
        num_total = len(df)
        t_sec = np.arange(num_total) * dt
        t = t_sec / 60.0 if unidade_tempo == "min" else t_sec

        fig, (ax1, ax3) = plt.subplots(2, 1, figsize=(3.4, 3.5), sharex=True)
        plt.subplots_adjust(left=0.18, right=0.94, top=0.96, bottom=0.20, hspace=0.16)

        ax1.plot(t, df[col_cv].values, color="#d95f02", linewidth=0.8)
        ax1.set_ylabel(r"Valve $\mathrm{CV}$ (%)", color="#d95f02", fontweight="bold")
        ax1.tick_params(axis="y", labelcolor="#d95f02")
        ax1.set_ylim(-5, 115)
        ax1.grid(True)

        ax3.plot(t, df[col_out].values, color="#2b5c8f", linewidth=0.8, label="Measured")
        if mostrar_split:
            split_idx = int(num_total * 0.5)
            t_split = t[split_idx]
            ax3.axvline(x=t_split, color="#d95f02", linestyle="--", linewidth=1.0)
            ax3.axvspan(0, t_split, color="#377eb8", alpha=0.08, label="Train (50%)")
            ax3.axvspan(t_split, t[-1], color="#ff7f00", alpha=0.08, label="Test (50%)")
            ncol_leg = 3
        else:
            ncol_leg = 1

        ax3.set_xlabel("Time (min)" if unidade_tempo == "min" else "Time (s)")
        ax3.set_ylabel(r"Vessel $P_{\mathrm{out}}$ (psi)", fontweight="bold")
        p_out_max = max(50, np.ceil(df[col_out].max() + 5))
        ax3.set_ylim(0, p_out_max)
        ax3.set_xlim(0, t[-1])
        ax3.grid(True)
        ax3.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=ncol_leg, frameon=True,
                   facecolor="white", edgecolor="#cccccc", framealpha=0.95, fontsize=7.0,
                   columnspacing=0.8, handletextpad=0.35, borderpad=0.25)

    # Salva nas pastas de destino
    for ext in ["png", "pdf"]:
        caminho_final_img = os.path.join(pasta_destino, f"{nome_saida}.{ext}")
        caminho_final_paper = os.path.join(paper_fig_dir, f"{nome_saida}.{ext}")
        fig.savefig(caminho_final_img, dpi=300)
        fig.savefig(caminho_final_paper, dpi=300)

    print("\n" + "=" * 65)
    print("IMAGEM GERADA COM SUCESSO:")
    print(f"  --> {os.path.join(pasta_destino, f'{nome_saida}.png')}")
    print(f"  --> {os.path.join(pasta_destino, f'{nome_saida}.pdf')}")
    print("=" * 65 + "\n")
    plt.show()


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        caminho_alvo = sys.argv[1]
        nome_fig = None
    else:
        caminho_alvo = os.path.abspath(os.path.join(base_dir, ARQUIVO_CSV_PADRAO))
        nome_fig = NOME_SAIDA_FIGURA

    pasta_images = os.path.abspath(os.path.join(base_dir, PASTA_IMAGENS_DESTINO))

    print(f"Lendo CSV: {caminho_alvo}")
    plotar_e_salvar(
        caminho_csv=caminho_alvo,
        nome_saida=nome_fig,
        pasta_destino=pasta_images,
        dt=DT_PADRAO,
        mostrar_split=DESTACAR_TREINO_TESTE,
        unidade_tempo=UNIDADE_TEMPO
    )
