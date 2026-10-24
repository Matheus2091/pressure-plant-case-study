# Relatório de Aquisição e Evolução dos Dados - Planta de Pressão

> **Documento de Auditoria e Curadoria dos Datasets**  
> *Bancada de Controle de Pressão — PUCPR*

---

## 1. Visão Geral da Campanha de Dados

Este relatório descreve a evolução metrológica e experimental das aquisições de dados realizadas na planta de pressão da PUCPR para fins de identificação de sistemas dinâmicos (modelos ARX e NARX).

A campanha experimental transitou por três fases:
1. **Fase 1 (Testes Preliminares Legados - 1 Hz):** Estímulos manuais em degrau, rampas de calibração e curvas semi-estáticas com taxa de amostragem de 1 segundo (arquivados em `raw_data/`);
2. **Fase 2 (Ajustes de Comunicação do Supervisório):** Primeiros ensaios automatizados de excitação em 4 Hz (arquivados em `IHM_Press_V3/.../RESULTADOS/OBSOLETOS/`);
3. **Fase 3 (Ensaio Oficial Padrão-Ouro - 4 Hz):** Ensaio de degraus pseudo-aleatórios com duração de 24,5 minutos, rico em frequências e dinâmicas acopladas (`Random Steps_3.csv`), adotado como referência definitiva para publicação.

---

## 2. Ensaio Oficial: `Random Steps_3.csv` (Ativo Principal)

- **Localização:** [`data/Random Steps_3.csv`](./data/Random%20Steps_3.csv) e [`IHM_Press_V3/.../RESULTADOS/Random Steps_3.csv`](./IHM_Press_V3/IHM_Press_V3/IHM_Press/RESULTADOS/Random%20Steps_3.csv)
- **Frequência de Amostragem:** $4{,}0$ Hz ($T_s = 250$ ms)
- **Número Total de Amostras:** 5.871
- **Duração Total:** 1.467,5 segundos ($\approx 24{,}5$ minutos)
- **Variáveis Monitoradas:**
  - `PV_OUT` (Pressão de saída do vaso em psi);
  - `CV` (Comando percentual de abertura da válvula reguladora, 0 a 100%);
  - `PV_IN` (Pressão da linha de alimentação de ar comprimido em psi);
  - `TIME` (Timestamp contínuo da coleta).

### Visualização do Ensaio Oficial
![Aquisição Random Steps 3](./images/aquisicao_random_steps_3.png)

### Divisão de Protocolo (50% Treino / 50% Teste)
- **Subconjunto de Treino:** Amostras 1 a 2.935 (tempo 0 a 12,2 min) — Utilizado para ortogonalização e estimação dos parâmetros;
- **Subconjunto de Teste:** Amostras 2.936 a 5.871 (tempo 12,3 a 24,5 min) — Reservado exclusivamente para validação em simulação livre (*Free-Run*) e predição passo a passo (*One-Step-Ahead*).

---

## 3. Ensaios Arquivados na Pasta `OBSOLETOS`

Com a evolução da instrumentação e do supervisório, os ensaios preliminares abaixo foram preservados para rastreabilidade histórica na pasta:  
`IHM_Press_V3/IHM_Press_V3/IHM_Press/RESULTADOS/OBSOLETOS/`

| Arquivo | Descrição | Motivo do Arquivamento / Obsolescência |
| :--- | :--- | :--- |
| **`Random Steps_1`** | Primeiro teste com degraus aleatórios em 4 Hz. | Amostragem preliminar com duração mais curta; serviu para validação do buffer de string do Elipse E3. |
| **`Random Steps_2`** | Segundo teste com degraus aleatórios em 4 Hz. | Saturação de pressão máxima alcançada em alguns patamares; superado pela distribuição balanceada de `Random Steps_3`. |
| **`Shirp_1`** | Excitação dinâmica tipo Swept Sine (Chirp). | As frequências superiores do sinal ultrapassaram a velocidade limite de resposta do posicionador pneumático, gerando atenuação mecânica excessiva. |
| **`TESTE1_SENO`** | Ensaio senoidal mononodal preliminar. | Excitação restrita a uma única frequência fundamental; insuficiente para caracterizar todas as não linearidades da planta. |

---

## 4. Ensaios Legados em `raw_data/` (Taxa Lenta de 1 Segundo)

Os ensaios abaixo pertencem à fase inicial do projeto e foram mantidos para documentação histórica de bancada:
- **`TESTE1.csv` / `.xlsx`:** Degraus manuais aplicados pelo operador para testar a comunicação básica do CLP;
- **`RAMPADEGRAIS1.csv` / `.xlsx`:** Aplicação de degraus progressivos em patamares fixos;
- **`SEMIESTÁTICA 1` e `SEMIESTÁTICA 2`:** Ensaio em regime quase-estático com subida e descida lentas para levantamento da curva estática e avaliação de histerese do atuador.

---

## 5. Como Inspecionar os Dados

Para plotar graficamente qualquer um dos datasets do repositório, utilize o script automatizado:

```powershell
# Execução na pasta de resultados:
cd IHM_Press_V3/IHM_Press_V3/IHM_Press/RESULTADOS
py plotar_dados.py "Random Steps_3.csv"

# Para inspecionar um ensaio arquivado:
py plotar_dados.py "OBSOLETOS/Shirp_1.csv"
```
