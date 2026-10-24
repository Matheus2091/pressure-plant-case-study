# Arquitetura e Funcionamento Geral da Bancada de Pressão
> **Documento Técnico de Referência do Projeto**  
> *Pontifícia Universidade Católica do Paraná (PUCPR)*  
> *Autores:* Matheus Kale Mendes, Fabricio Cassanho Teodoro, Gabriel Tartari, Helon Vicente Hultmann Ayala

---

## 1. Visão Geral do Projeto

Este projeto consiste em um **benchmark experimental e computacional completo para Identificação de Sistemas Não Lineares** aplicado a um processo industrial de controle de pressão de ar comprimido.

O objetivo central é fornecer à comunidade científica e de engenharia um conjunto de dados fidedigno, reprodutível e desafiador, acompanhado de ferramentas de software que integram:
1. **Modelagem Matemática Avançada:** Identificação de modelos polinomiais autoregressivos não lineares com entradas exógenas (**MISO NARX**) e comparação com modelos lineares (**ARX**) usando ortogonalização por Gram-Schmidt Modificado (**MGS**) e regressão progressiva (**FROLS**);
2. **Automação Industrial em Tempo Real:** Integração de CLP industrial Allen-Bradley (Rockwell Automation) e sistema supervisório SCADA (Elipse E3);
3. **Pipeline de Excitação Arbitrária por CSV:** Injeção precisa de sinais sintetizados no MATLAB diretamente no atuador da bancada com sincronismo rígido a 4 Hz (250 ms);
4. **Artigo Científico para Congresso Internacional:** Estrutura metodológica e dados alinhados com o template da conferência internacional **IFAC** (*International Federation of Automatic Control*).

---

## 2. A Planta Física e Instrumentação

A bancada didática-industrial está instalada no laboratório de automação da PUCPR e é composta pelos seguintes elementos principais:

```
                  [ Rede de Ar Comprimido ]
                             │
                             ▼
                    [ Transmissor PV_IN ]
                     (Pressão de Entrada)
                             │
                             ▼
                 [ Válvula de Controle CV ]
                 (0 a 100% de Abertura)
                             │
                             ▼
                 ┌───────────────────────┐
                 │    Vaso de Pressão    │───► [ Transmissor PV_OUT ]
                 │ (Câmara de Acúmulo)   │     (Pressão de Saída / Processo)
                 └───────────────────────┘
                             │
                             ▼ (Válvula de Escape / Carga)
                         [ Escape ]
```

### 2.1 Variáveis do Processo (Estrutura MISO)
O sistema opera em configuração **MISO** (*Multiple-Input Single-Output*), com duas entradas exógenas e uma saída medida:

| Variável | Tipo | Unidade | Descrição Física |
| :--- | :--- | :--- | :--- |
| **`PV_OUT`** | **Saída do Processo ($y$)** | psi | Pressão instantânea no interior do vaso de pressão. Variável a ser modelada e predita. |
| **`CV`** | **Entrada Exógena 1 ($u_1$)** | % | Variável de Controle: percentual de abertura da válvula reguladora de vazão proporcional (0% = totalmente fechada, 100% = totalmente aberta). |
| **`PV_IN`** | **Entrada Exógena 2 ($u_2$)** | psi | Pressão de suprimento na linha de alimentação a montante da válvula. Sofre variações dinâmicas provocadas pelo compressor da fábrica e pelo consumo da própria bancada. |

### 2.2 Desafios Físicos e Não Linearidades
Diferente de sistemas puramente lineares ou térmicos simples, a dinâmica de pressão em vasos apresenta fortes características não lineares:
- **Compressibilidade do Gás:** A relação entre densidade, pressão e volume é governada pela termodinâmica dos gases reais/ideais;
- **Vazão por Orifício Variável:** A vazão mássica através do obturador da válvula depende não apenas da abertura `CV`, mas da raiz quadrada da diferença de pressões $(PV_{IN} - PV_{OUT})$ e de efeitos de estrangulamento sônico/subsônico;
- **Assimetria Temporal Intrínseca:** O enchimento do vaso é forçado pela alta pressão da linha de alimentação (dinâmica rápida de subida), enquanto o esvaziamento depende da perda de carga e despressurização natural para a atmosfera (dinâmica lenta de descida);
- **Atrito e Histerese:** Não linearidades no atuador eletropneumático da válvula de controle.

---

## 3. Arquitetura de Automação: CLP + Supervisório Elipse E3

A aquisição de dados e a atuação em tempo real são orquestradas por uma infraestrutura de automação industrial robusta:

```mermaid
graph LR
    subgraph Nivel_Algoritmo ["Nível de Algoritmo e Pesquisa"]
        MATLAB["MATLAB (gerar_sinais.m)"] -->|Exporta CSV| CSV["Sinal CSV (250 ms)"]
        PYTHON["Python (arx_miso / narx_miso)"] <--|Lê CSVs| DATA["Dataset (Random Steps_3.csv)"]
    end

    subgraph Nivel_Supervisao ["Nível de Supervisão SCADA"]
        CSV -->|btnImportarCSV| ELIPSE["Elipse E3 SCADA (IHM_Temp.prj)"]
        ELIPSE -->|TagTimer_CSV 250ms| BUFFER["Fatiador de String (Memória E3)"]
        HIST["Histórico E3 / Exportador"] -->|Grava dados| DATA
    end

    subgraph Nivel_Campo ["Nível de Controle e Campo"]
        BUFFER -->|Driver ABCIP / Modbus| CLP["CLP Allen-Bradley (Planta_PUC_Press.ACD)"]
        CLP -->|Sinal 4-20 mA| VALV["Válvula de Controle (CV)"]
        PT_IN["Transmissor PT_IN"] -->|Entrada Analógica| CLP
        PT_OUT["Transmissor PT_OUT"] -->|Entrada Analógica| CLP
        VALV --> PLANTA["Vaso de Pressão Industrial"]
        PT_IN -.-> PLANTA
        PT_OUT -.-> PLANTA
        CLP -->|Telemetria em Tempo Real| ELIPSE
    end
```

### 3.1 Arquivos da Automação na Pasta `IHM_Press_V3`
Localização: `IHM_Press_V3/IHM_Press_V3/IHM_Press/`

1. **`Planta_PUC_Press.ACD`**: Programa em Ladder / Blocos para Rockwell Studio 5000 / RSLogix 5000:
   - Configura os módulos analógicos do CLP Allen-Bradley;
   - Realiza a conversão de escala (*scaling*) dos transmissores para psi;
   - Recebe a referência da tag de controle `DriverPress.IP_CV1_IHM` e aciona o módulo de saída analógica 4-20 mA da válvula.
2. **`IHM_Temp.prj` e `IHM_Temp.dom`**: Projeto e Domínio do Supervisório Elipse E3:
   - Contém as telas visuais de monitoramento contínuo das pressões e percentual de abertura;
   - Gerencia a comunicação via drivers proprietários (`ABCIP.dll` e `Modbus.dll`);
   - Implementa o **Motor de CSV** com isolamento modular para evitar travamentos na bancada.

### 3.2 Como Funciona o "Motor de Execução de CSV" no Elipse E3
Para injetar sinais arbitrários de identificação (Chirp, degraus aleatórios, etc.) na planta física sem depender de timers imprecisos de sistemas operacionais comuns:
1. O usuário clica no botão **`btnImportarCSV`** na tela do Elipse;
2. O script VBScript lê o arquivo `.csv`, converte pontos decimais para vírgula e concatena todos os pontos de comando em uma única variável de memória em formato texto, separada por barras verticais (`|`), por exemplo: `"10,0|15,5|50,0|..."`;
3. Armazena o número total de amostras na tag `Dados.Tag_Tamanho_CSV` e zera o ponteiro `Dados.Tag_Indice_CSV`;
4. Desativa quaisquer rampas manuais anteriores e liga o timer periódico **`Dados.TagTimer_CSV`** com período ajustado para **`00:00:00.250`** (250 ms = 4 Hz);
5. A cada disparo do timer (evento `OnPreset`), o script extrai exatamente o ponto do índice corrente via comando `Split`, escreve na tag do CLP `DriverPress.IP_CV1_IHM` e incrementa o índice;
6. Ao atingir o último ponto, desliga o timer e zera a válvula por segurança;
7. O botão **STOP** geral atua como parada de emergência, desabilitando o timer e enviando zero imediato para o atuador.

---

## 4. Ciclo de Vida do Dado: Do MATLAB aos Modelos Matemáticos

```
┌────────────────────────────────┐
│ 1. MATLAB                      │ ➜ Projeto de sinais de teste ricos em frequências
│    gerar_sinais_excitacao_...  │   (sinal_degraus_aleatorios.csv, etc.)
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│ 2. ELIPSE E3 SCADA + CLP       │ ➜ Execução física na planta com amostragem de 250 ms
│    btnImportarCSV / TagTimer   │   (Válvula excitada, pressões medidas simultaneamente)
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│ 3. PASTA RESULTADOS            │ ➜ Arquivos CSV/XLSX exportados
│    Random Steps_3.csv          │   (Ensaio ativo padrão-ouro com 5.871 amostras)
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│ 4. PYTHON PLOT (plotar_dados)  │ ➜ Inspeção preliminar gráfica instantânea
│    Subplots + Curvas Sobreposta│   (Inspeção visual de saturações e ruído)
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│ 5. SCRIPTS DE IDENTIFICAÇÃO    │ ➜ Estimador MISO ARX e MISO NARX (FROLS + ERR)
│    arx_miso.py / narx_miso.py  │   (Validação em OSA e Free-Run nos dados de teste)
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│ 6. ARTIGO IFAC (paper/main.tex)│ ➜ Figuras geradas, métricas RMSE e equações finais
└────────────────────────────────┘
```

---

## 5. Organização dos Datasets: Ativos vs. Obsoletos

Para garantir rigor científico e facilitar a reprodução de trabalhos por terceiros, os arquivos de dados foram rigorosamente categorizados:

### 5.1 Dataset Ativo Principal (Ouro)
- **Arquivo:** `data/Random Steps_3.csv` e `IHM_Press_V3/.../RESULTADOS/Random Steps_3.csv`
- **Características:**
  - Amostragem: $T_s = 0{,}25$ s (4 Hz);
  - Duração: 24,5 minutos (5.871 amostras);
  - Protocolo de Validação: 50% Treino inicial (amostras 1 a 2.935, ~12,2 min) e 50% Teste final (amostras 2.936 a 5.871, ~12,3 min);
  - Exclusividade: Utilizado no artigo IFAC como referência experimental definitiva.

### 5.2 Sinais de Excitação Sintetizados
Localizados em `data/`:
- `sinal_degraus_aleatorios.csv`: Sequência de degraus pseudo-aleatórios com amplitudes variando de 0 a 100% e duração aleatória por patamar;
- `sinal_semi_estatica.csv`: Rampa ascendente lenta (0 a 100%) seguida de rampa descendente para identificação estática;
- `sinal_swept_sine.csv`: Senoide de frequência varrida linearmente (*chirp*) para levantamento dinâmico em frequência.

### 5.3 Ensaios Arquivados em `OBSOLETOS`
Localizados em `IHM_Press_V3/.../RESULTADOS/OBSOLETOS/` e `raw_data/`:
- `Random Steps_1` e `Random Steps_2`: Ensaios preliminares realizados durante o ajuste da taxa de comunicação do driver de rede e calibração de escala da válvula;
- `Shirp_1.csv` / `.xlsx`: Teste com chirp cujas frequências mais altas excederam a banda passante do posicionador mecânico;
- `TESTE1_SENO.csv` / `.xlsx`: Ensaio preliminar senoidal de validação de conectividade;
- `TESTE1.csv`, `RAMPADEGRAIS1.csv`, `SEMIESTÁTICA 1/2.csv`: Ensaios legados coletados com taxa de amostragem anterior de 1 segundo (substituídos pela aquisição rápida de 250 ms).

---

## 6. Metodologia de Modelagem Não Linear (MISO NARX)

A modelagem matemática desenvolvida em `scripts/narx_miso.py` e `scripts/miso_narx.py` emprega o modelo NARX polinomial:

$$y(k) = F\Big(y(k-1), \dots, y(k-n_y), u_1(k-1), \dots, u_1(k-n_{u1}), u_2(k-1), \dots, u_2(k-n_{u2})\Big) + e(k)$$

### 6.1 Algoritmo FROLS (Forward Regression Orthogonal Least Squares)
1. Constrói-se uma matriz de regressores candidatos contendo termos lineares, quadráticos, cúbicos e produtos cruzados (espaço de dimensão elevada);
2. A matriz de regressores é decomposta em uma base ortogonal através do **Gram-Schmidt Modificado (MGS)**;
3. A cada iteração, o regressor que mais reduz a variância do erro de saída é selecionado através do critério **ERR** (*Error Reduction Ratio*):
   $$\mathrm{ERR}_i = \frac{(Y^T w_i)^2}{Y^T Y \cdot (w_i^T w_i)}$$
4. O processo se encerra quando o critério de parada ($\rho$ ou número fixo de componentes) é satisfeito.

### 6.2 Desempenho Comparativo (Métrica: RMSE em psi)
Resultados obtidos no conjunto de dados de teste (50% final, dados nunca vistos no treinamento):

| Modelo | Grau ($\ell$) | Termos | RMSE One-Step-Ahead (OSA) | RMSE Simulação Livre (Free-Run) |
| :--- | :---: | :---: | :---: | :---: |
| **ARX Linear** | 1 | 6 | 0.1231 psi | 4.9262 psi |
| **NARX Polinomial** | 3 | 8 | **0.0934 psi** | **1.2115 psi** *(Redução de 75,4%)* |

> **Interpretação Física:** Em simulação livre (Free-Run), o modelo linear acumula erro rapidamente devido à incapacidade de descrever a despressurização assimétrica do vaso. O modelo NARX selecionou o termo cruzado $CV(k-3) \cdot PV_{IN}^2(k-1)$, capturando exatamente o acoplamento termofluídico da vazão mássica através da válvula.

---

## 7. Mapeamento de Arquivos e Atenção aos Caminhos

Se você estiver abrindo o projeto em uma nova máquina ou executando a IHM na bancada, certifique-se de verificar os caminhos descritos abaixo:

| Componente | Arquivo | Onde alterar ou verificar caminhos |
| :--- | :--- | :--- |
| **Elipse E3 (Botão Importar CSV)** | `IHM_Temp.prj` | Abrir tela no Elipse Studio ➜ Inspecionar botão `btnImportarCSV` ➜ Evento `Click` ➜ Variável `CaminhoCSV`. Deve apontar para o arquivo CSV desejado (ex: `.../data/sinal_degraus_aleatorios.csv`). |
| **Elipse E3 (Driver de Comunicação)** | `IHM_Temp.prj` | Configuração do driver `DriverPress` (ABCIP / Modbus) ➜ Conferir endereço IP do CLP Allen-Bradley na rede física da bancada. |
| **Scripts Python** | `scripts/arx_miso.py` e `scripts/narx_miso.py` | Já possuem busca relativa automática em `../data/Random Steps_3.csv` e na pasta `RESULTADOS/`. Não exigem alteração manual. |
| **Script MATLAB** | `scripts/gerar_sinais_excitacao_pressao.m` | Exporta automaticamente para `../data/`. Funciona diretamente ao ser executado na pasta `scripts/`. |
| **Workspace do VS Code** | `IHM_Press_V3.code-workspace` | Já configurado para carregar a raiz do repositório, o diretório da IHM e a pasta RESULTADOS de forma relativa. |

---

## 8. Conclusão

Esta arquitetura integra todo o ciclo da engenharia: desde o projeto matemático de sinais e automação em tempo real de nível de campo até a modelagem matemática não linear de ponta. 

Para instruções detalhadas de como carregar os sinais no supervisório e rodar na planta física, consulte o [Guia de Execução CSV no Elipse E3](Guia_Execucao_CSV_Matlab.md). Para a visão executiva e resumo do trabalho científico, consulte o [README.md](README.md).
