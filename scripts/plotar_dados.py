"""
Script Geral para leitura e plotagem dos dados de ensaios de pressão (IHM Press).

Características dos dados:
- Período de amostragem padrão: dt = 0.25 s (250 ms) -> Frequência de amostragem: 4 Hz.
- Variáveis lidas:
    - PV_OUT : Variável de Processo de Saída (Pressão de saída)
    - CV     : Variável de Controle (Sinal de comando do atuador em %)
    - PV_IN  : Variável de Processo de Entrada (Pressão de alimentação)
    - TIME   : Timestamp original da coleta
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# ⚙️ CONFIGURAÇÕES PRINCIPAIS (Altere aqui conforme a sua necessidade)
# ==============================================================================
# 1. Caminho ou nome do arquivo padrão:
#    - Se estiver na mesma pasta, basta o nome: "Shirp_1.csv"
#    - Se estiver em outra pasta, coloque o caminho completo: r"C:\sua_pasta\dados.csv"
ARQUIVO_PADRAO = "Shirp_1.csv"

# 2. Período de amostragem (dt) em segundos:
#    250 ms = 0.25 segundos (taxa de 4 Hz)
PERIODO_AMOSTRAGEM = 0.25

# 3. Unidade do eixo horizontal de tempo:
#    - "min"       : Minutos decorridos (ex: 0 a 30 min) -> Recomendado
#    - "s"         : Segundos decorridos (ex: 0 a 1800 s)
#    - "timestamp" : Horário real da coleta (data e hora contínua)
UNIDADE_TEMPO = "min"

# 4. Salvar arquivos PNG automaticamente ao rodar o script?
#    - True  : Salva automaticamente os dois gráficos na mesma pasta do arquivo.
#    - False : Apenas abre a janela na tela, permitindo que você dê zoom e salve
#              manualmente pelo botão de disquete 💾 na barra inferior do gráfico.
SALVAR_AUTOMATICO = True
# ==============================================================================


def encontrar_arquivo(origem: str | Path) -> Path:
    """
    Resolve o caminho do arquivo, aceitando caminhos absolutos, relativos
    ao terminal ou relativos à pasta onde este script está localizado.
    """
    caminho = Path(origem)
    
    # 1. Verifica se o caminho absoluto ou direto existe
    if caminho.exists():
        return caminho.resolve()
        
    # 2. Verifica relativo à pasta do próprio script
    pasta_script = Path(__file__).resolve().parent
    caminho_relativo = pasta_script / origem
    if caminho_relativo.exists():
        return caminho_relativo.resolve()

    # Verifica se o arquivo esta na pasta ../data
    caminho_data = pasta_script.parent / 'data' / origem
    if caminho_data.exists():
        return caminho_data.resolve()
        
    # 3. Fallback: Se não encontrou, lista arquivos CSV/XLSX disponíveis na pasta para ajudar o usuário
    arquivos_disp = list(pasta_script.glob("*.csv")) + list(pasta_script.glob("*.xlsx"))
    nomes_disp = [f.name for f in arquivos_disp if not f.name.startswith("~")]
    
    msg_erro = f"Arquivo não encontrado: '{origem}'\n"
    if nomes_disp:
        msg_erro += f"Arquivos de dados encontrados nesta pasta: {nomes_disp}"
    else:
        msg_erro += f"Nenhum arquivo .csv ou .xlsx encontrado na pasta '{pasta_script}'."
        
    raise FileNotFoundError(msg_erro)


def carregar_dados(caminho_arquivo: str | Path, dt: float = 0.25) -> pd.DataFrame:
    """
    Carrega o arquivo CSV ou Excel, detecta delimitadores automaticamente,
    converte números com vírgula ou ponto e reconstrói o eixo temporal contínuo.
    """
    caminho = encontrar_arquivo(caminho_arquivo)
    
    # 1. Carregamento dos dados
    if caminho.suffix.lower() == '.csv':
        # Tenta primeiro com separador ';' e decimal ',' (padrão Brasil/Excel exportado)
        try:
            df = pd.read_csv(caminho, sep=';', decimal=',', encoding='utf-8')
            if len(df.columns) <= 1:
                # Tenta separador vírgula caso o arquivo esteja em padrão internacional
                df = pd.read_csv(caminho, sep=',', decimal='.', encoding='utf-8')
        except Exception:
            df = pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8')
    elif caminho.suffix.lower() in ('.xlsx', '.xls'):
        df = pd.read_excel(caminho)
    else:
        raise ValueError(f"Extensão não suportada: {caminho.suffix}. Use .csv ou .xlsx")
        
    # 2. Localização insensível a maiúsculas/minúsculas para as colunas
    mapa_colunas = {col.strip().upper(): col for col in df.columns}
    colunas_chave = {}
    for padrao in ['PV_OUT', 'CV', 'PV_IN', 'TIME']:
        if padrao in mapa_colunas:
            colunas_chave[padrao] = mapa_colunas[padrao]
            
    if 'PV_OUT' not in colunas_chave or 'CV' not in colunas_chave:
        raise ValueError(f"Colunas mínimas necessárias (PV_OUT, CV) não encontradas. Colunas no arquivo: {list(df.columns)}")
        
    # 3. Cria dataframe padronizado com as colunas essenciais
    df_limpo = pd.DataFrame()
    for padrao, col_orig in colunas_chave.items():
        if padrao != 'TIME':
            df_limpo[padrao] = pd.to_numeric(df[col_orig], errors='coerce')
        else:
            df_limpo['TIME'] = df[col_orig]
            
    # Remove registros com valores inválidos/nulos
    cols_numericas = [c for c in ['PV_OUT', 'CV', 'PV_IN'] if c in df_limpo.columns]
    df_limpo = df_limpo.dropna(subset=cols_numericas).reset_index(drop=True)
    
    # 4. Reconstrução precisa do eixo de tempo a partir de dt
    n_pontos = len(df_limpo)
    df_limpo['Tempo_s'] = np.arange(n_pontos) * dt        # Eixo em segundos
    df_limpo['Tempo_min'] = df_limpo['Tempo_s'] / 60.0    # Eixo em minutos
    
    # Reconstrução opcional de data/hora contínua
    if 'TIME' in df_limpo.columns:
        try:
            inicio = pd.to_datetime(df_limpo['TIME'].iloc[0], dayfirst=True)
            df_limpo['Timestamp'] = inicio + pd.to_timedelta(df_limpo['Tempo_s'], unit='s')
        except Exception:
            pass
            
    return df_limpo


def _obter_eixo_x(df: pd.DataFrame, unidade: str = "min"):
    """Retorna os dados do eixo X e o rótulo correspondente."""
    if unidade.lower() == 's':
        return df['Tempo_s'], "Tempo decorrido (segundos)"
    elif unidade.lower() == 'timestamp' and 'Timestamp' in df.columns:
        return df['Timestamp'], "Horário de Coleta"
    else:
        return df['Tempo_min'], "Tempo decorrido (minutos)"


def plotar_grafico_separado(df: pd.DataFrame, 
                            titulo: str = "Ensaio de Pressão", 
                            eixo_x: str = "min", 
                            salvar_imagem: str | Path | None = None) -> plt.Figure:
    """
    Gráfico 1: Dois subplots sincronizados compartilhando o eixo X.
      - Subplot superior: PV_IN (azul) e PV_OUT (vermelho)
      - Subplot inferior: CV (verde)
    """
    x_data, x_label = _obter_eixo_x(df, eixo_x)
    
    fig, (ax_pressao, ax_cv) = plt.subplots(
        nrows=2, 
        ncols=1, 
        figsize=(12, 7), 
        sharex=True, 
        gridspec_kw={'height_ratios': [2, 1.2]}
    )
    
    # Subplot 1: Pressões
    if 'PV_IN' in df.columns:
        ax_pressao.plot(x_data, df['PV_IN'], label='PV_IN (Pressão de Entrada)', color='#1f77b4', linewidth=1.4)
    ax_pressao.plot(x_data, df['PV_OUT'], label='PV_OUT (Pressão de Saída)', color='#d62728', linewidth=1.5)
    
    ax_pressao.set_ylabel('Pressão (bar / PSI)', fontsize=11, fontweight='bold')
    ax_pressao.set_title(f"{titulo} - Gráfico Separado (Subplots)\nResposta das Variáveis de Processo (PV)", fontsize=13, fontweight='bold', pad=10)
    ax_pressao.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    ax_pressao.grid(True, linestyle='--', alpha=0.6)
    
    pv_out_min, pv_out_max = df['PV_OUT'].min(), df['PV_OUT'].max()
    ax_pressao.text(0.015, 0.90, f"PV_OUT: [{pv_out_min:.2f} ~ {pv_out_max:.2f}]", 
                    transform=ax_pressao.transAxes, fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d62728", alpha=0.8))

    # Subplot 2: Sinal de Controle
    ax_cv.plot(x_data, df['CV'], label='CV (Variável de Controle)', color='#2ca02c', linewidth=1.3)
    ax_cv.set_xlabel(x_label, fontsize=11, fontweight='bold')
    ax_cv.set_ylabel('CV (%)', fontsize=11, fontweight='bold')
    ax_cv.set_title('Ação de Controle Excitadora (CV)', fontsize=11, fontweight='bold', pad=6)
    ax_cv.set_ylim(-5, 105)
    ax_cv.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    ax_cv.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    
    if salvar_imagem:
        caminho_save = Path(salvar_imagem)
        fig.savefig(caminho_save, dpi=200, bbox_inches='tight')
        print(f"[OK] Gráfico Separado salvo em: {caminho_save.name}")
        
    return fig


def plotar_grafico_sobreposto(df: pd.DataFrame, 
                              titulo: str = "Ensaio de Pressão", 
                              eixo_x: str = "min", 
                              salvar_imagem: str | Path | None = None) -> plt.Figure:
    """
    Gráfico 2: Sinais Sobrepostos no mesmo gráfico.
      - CV     : Linha pontilhada verde
      - PV_OUT : Linha contínua vermelha
      - PV_IN  : Linha contínua azul
    """
    x_data, x_label = _obter_eixo_x(df, eixo_x)
    
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    # 1. PV_IN: Linha contínua azul
    if 'PV_IN' in df.columns:
        ax.plot(x_data, df['PV_IN'], 
                label='PV_IN (Pressão de Entrada)', 
                color='#1f77b4', 
                linestyle='-', 
                linewidth=1.5)
    
    # 2. PV_OUT: Linha contínua vermelha
    ax.plot(x_data, df['PV_OUT'], 
            label='PV_OUT (Pressão de Saída)', 
            color='#d62728', 
            linestyle='-', 
            linewidth=1.7)
    
    # 3. CV: Linha pontilhada verde
    ax.plot(x_data, df['CV'], 
            label='CV (Sinal de Controle)', 
            color='#2ca02c', 
            linestyle=':', 
            linewidth=2.0)
    
    ax.set_xlabel(x_label, fontsize=11, fontweight='bold')
    ax.set_ylabel('Amplitude (Pressão / CV %)', fontsize=11, fontweight='bold')
    ax.set_title(f"{titulo} - Sinais Sobrepostos (PV_IN, PV_OUT e CV)", fontsize=13, fontweight='bold', pad=12)
    
    # Escala Y adequada cobrindo pressões e controle (%)
    y_max = max(105, df[['PV_IN', 'PV_OUT', 'CV']].max().max() * 1.05) if 'PV_IN' in df.columns else max(105, df[['PV_OUT', 'CV']].max().max() * 1.05)
    ax.set_ylim(-5, y_max)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    
    plt.tight_layout()
    
    if salvar_imagem:
        caminho_save = Path(salvar_imagem)
        fig.savefig(caminho_save, dpi=200, bbox_inches='tight')
        print(f"[OK] Gráfico Sobreposto salvo em: {caminho_save.name}")
        
    return fig


def executar_pipeline(caminho_arquivo: str | Path | None = None,
                      dt: float = PERIODO_AMOSTRAGEM,
                      eixo_x: str = UNIDADE_TEMPO,
                      salvar_auto: bool = SALVAR_AUTOMATICO,
                      mostrar: bool = True):
    """
    Função principal que orquestra a leitura e a geração dos dois gráficos.
    """
    # Se nenhum arquivo foi informado por parâmetro, usa a configuração padrão do topo
    arquivo_alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_PADRAO
    caminho = encontrar_arquivo(arquivo_alvo)
    
    print("=" * 65)
    print(f"Lendo arquivo: {caminho.name}")
    print(f"Localização  : {caminho.parent}")
    print("=" * 65)
    
    dados = carregar_dados(caminho, dt=dt)
    
    print(f"Total de amostras lidas : {len(dados)}")
    print(f"Duração total do ensaio  : {dados['Tempo_s'].iloc[-1]:.2f} s ({dados['Tempo_min'].iloc[-1]:.2f} minutos)")
    print(f"Período de amostragem    : {dt * 1000:.0f} ms ({dt} s) | Frequência: {1/dt:.1f} Hz")
    print("-" * 65)
    
    prefixo = caminho.stem
    pasta_saida = caminho.parent
    
    caminho_img_separado = pasta_saida / f"{prefixo}_grafico_separado.png" if salvar_auto else None
    caminho_img_sobreposto = pasta_saida / f"{prefixo}_grafico_sobreposto.png" if salvar_auto else None
    
    # Aplica tema visual moderno
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # 1. Gera o Gráfico Separado
    plotar_grafico_separado(dados, titulo=f"Ensaio: {prefixo}", eixo_x=eixo_x, salvar_imagem=caminho_img_separado)
    
    # 2. Gera o Gráfico Sobreposto
    plotar_grafico_sobreposto(dados, titulo=f"Ensaio: {prefixo}", eixo_x=eixo_x, salvar_imagem=caminho_img_sobreposto)
    
    if salvar_auto:
        print("-" * 65)
        print(f"[INFO] As imagens foram salvas na pasta: {pasta_saida}")
        
    if mostrar:
        print("\n[INFO] Janelas dos gráficos abertas!")
        print("💡 DICA: Use as ferramentas na barra inferior da janela do gráfico:")
        print("   - 🔍 Lupa / Zoom : Para inspecionar detalhes de qualquer região;")
        print("   - ↔️  Pan / Mover : Para arrastar o gráfico;")
        print("   - 💾 Salvar      : Para salvar a imagem onde e como você quiser (PNG, PDF, SVG, etc.).")
        print("\n(Feche as janelas dos gráficos para finalizar a execução)")
        plt.show()


if __name__ == "__main__":
    # Prioridade de escolha do arquivo:
    # 1. Se passou arquivo via terminal: 'python plotar_dados.py outro_arquivo.csv'
    # 2. Caso contrário: usa a constante ARQUIVO_PADRAO definida no topo do script
    arquivo_escolhido = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        executar_pipeline(
            caminho_arquivo=arquivo_escolhido,
            dt=PERIODO_AMOSTRAGEM,
            eixo_x=UNIDADE_TEMPO,
            salvar_auto=SALVAR_AUTOMATICO,
            mostrar=True
        )
    except Exception as erro:
        print(f"\n[ERRO] {erro}")
