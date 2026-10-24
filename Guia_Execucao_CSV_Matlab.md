# Guia de Execução de Sinal CSV (MATLAB) no Elipse E3
> **Procedimento Operacional Padrão (POP) para Injeção de Sinais Arbitrários na Bancada de Pressão**  
> *Pontifícia Universidade Católica do Paraná (PUCPR)*

---

## 1. Visão Geral

Este guia documenta o procedimento completo para sintetizar sinais de excitação matemáticos no **MATLAB** (como Degraus Aleatórios, Chirp/Swept Sine ou Curvas Semi-Estáticas), salvá-los em formato `.csv` e executá-los em tempo real na bancada física através do supervisório **Elipse E3** conectado ao **CLP Allen-Bradley**.

Para garantir segurança operacional e determinismo temporal:
- A funcionalidade utiliza um **`TagTimer_CSV` dedicado** com período configurado para **`00:00:00.250`** (250 ms / 4 Hz);
- Opera em **arquitetura modular isolada**, desligando automaticamente quaisquer rampas manuais anteriores no momento da importação;
- O botão **STOP Geral** atua como desarme de segurança imediato.

---

## 2. Passo 1: Geração dos Sinais de Excitação no MATLAB

O script oficial para projeto dos sinais está localizado em:
`scripts/gerar_sinais_excitacao_pressao.m`

### 2.1 Parâmetros Temporais Padronizados
- **Tempo de Amostragem ($T_s$):** `0.25` s (250 ms);
- **Período de Repouso:** 10 segundos no início e no fim em 0% para estabilização de pressão;
- **Faixa de Amplitude da Válvula:** 0 a 100%.

### 2.2 Sinais Disponíveis para Exportação
Ao executar o script no MATLAB, três arquivos prontos são exportados automaticamente para a pasta `data/`:
1. **`sinal_degraus_aleatorios.csv`**: Sequência de degraus pseudo-aleatórios com semente fixa (`rng(0)`), ideal para identificação linear e não linear dinâmica (**ensaio principal**);
2. **`sinal_semi_estatica.csv`**: Rampa suave subindo de 0 a 100% e descendo de 100 a 0% para mapeamento estático da válvula;
3. **`sinal_swept_sine.csv`**: Senoide de frequência crescente (Chirp) com amplitude de 50% em torno do ponto de operação médio (50%).

### 2.3 Formato do Arquivo CSV Gerado
O Elipse E3 espera arquivos sem cabeçalho, com o tempo na primeira coluna e a amplitude na segunda coluna, separados por ponto-e-vírgula (`;`):
```text
0.0;0.0
0.25;0.0
0.50;10.0
0.75;25.5
1.00;50.0
```

---

## 3. Passo 2: Estrutura de Tags no Elipse E3

No software **Elipse E3 Studio**, certifique-se de que a pasta `Dados` contenha as seguintes tags configuradas:

| Nome da Tag | Tipo de Tag | Propriedade | Valor / Configuração | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **`TagTimer_CSV`** | Tag Timer | `RepeatInterval`<br/>`Enabled` | `00:00:00.250` (250 ms)<br/>`False` | Responsável pelo envio periódico síncrono de 4 Hz para o CLP. |
| **`Tag_ArraySinal_CSV`** | Tag Interna (String) | `Value` | `""` | Armazena na memória do SCADA o vetor de amplitudes concatenado por `\|`. |
| **`Tag_Tamanho_CSV`** | Tag Interna (Integer) | `Value` | `0` | Quantidade total de pontos lidos no arquivo CSV. |
| **`Tag_Indice_CSV`** | Tag Interna (Integer) | `Value` | `0` | Ponteiro/cursor da amostra que está sendo enviada no instante atual. |

---

## 4. Passo 3: Script do Botão "Importar e Rodar CSV"

Na tela de operação do Elipse E3 (`TelaInicial`), crie ou inspecione o botão com a propriedade `Name = "btnImportarCSV"`.

### 4.1 Atenção ao Caminho do Arquivo (`CaminhoCSV`)
> [!IMPORTANT]
> **Atenção aos Caminhos de Arquivo:**  
> Como a pasta da IHM foi movida para dentro do repositório `pressure-plant-case-study`, certifique-se de que a variável `CaminhoCSV` aponte para o caminho absoluto do arquivo no seu computador atual:  
> `C:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\data\sinal_degraus_aleatorios.csv`  
> *(Ou o sinal correspondente que deseja executar)*

### 4.2 Código VBScript do Evento `Click`
```vbscript
Sub btnImportarCSV_Click()
    Dim fso, arquivo, linha, dados, contador
    Dim stringCompleta
    Dim CaminhoCSV
    
    ' =========================================================================
    ' ATENÇÃO: CONFIGURE O CAMINHO DO CSV DESEJADO ABAIXO:
    CaminhoCSV = "C:\Users\mathe\OneDrive\Desktop\pressure-plant-case-study\data\sinal_degraus_aleatorios.csv"
    ' =========================================================================
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    stringCompleta = ""
    
    If fso.FileExists(CaminhoCSV) Then
        Set arquivo = fso.OpenTextFile(CaminhoCSV, 1) 
        contador = 0
        
        Do Until arquivo.AtEndOfStream
            linha = arquivo.ReadLine
            If Trim(linha) <> "" Then
                dados = Split(linha, ";")
                ' Converte para vírgula decimal e concatena usando o delimitador pipe (|)
                stringCompleta = stringCompleta & CDbl(Replace(dados(1), ".", ",")) & "|"
                contador = contador + 1
            End If
        Loop
        arquivo.Close
        
        ' Armazena o buffer de dados na memória do E3
        Application.GetObject("Dados.Tag_ArraySinal_CSV").Value = stringCompleta
        Application.GetObject("Dados.Tag_Tamanho_CSV").Value = contador
        Application.GetObject("Dados.Tag_Indice_CSV").Value = 0
        
        ' Desativa timers antigos e caixas de seleção de rampas para evitar conflito
        On Error Resume Next
        Application.GetObject("Dados.TagTimer_Rampa").Enabled = False
        Screen.Item("chk_CurvaEstatica").Value = False
        Screen.Item("chk_Degraus").Value = False
        On Error GoTo 0
        
        ' LIGA O TIMER DO MOTOR DE CSV (Amostragem em 250 ms)
        Application.GetObject("Dados.TagTimer_CSV").Enabled = True
        
        MsgBox "CSV Carregado com Sucesso! Execução iniciada em 250ms (" & contador & " amostras)."
    Else
        MsgBox "Arquivo CSV não encontrado no caminho especificado:" & vbCrLf & CaminhoCSV, vbCritical, "Erro de Leitura"
    End If
End Sub
```

---

## 5. Passo 4: Script do Disparo Periódico (`TagTimer_CSV`)

Este script é acionado a cada 250 ms pelo evento `OnPreset` da tag `TagTimer_CSV`. Ele fatiará a string da memória e atualizará a variável de controle da válvula no CLP.

**Objeto:** `Dados.TagTimer_CSV`  
**Evento:** `OnPreset`

```vbscript
Sub TagTimer_CSV_OnPreset()
    If Application.GetObject("Dados.TagTimer_CSV").Enabled = True Then
        
        Dim Indice, Tamanho, TextoSinal, ArrayPontos, Com
        Set Indice = Application.GetObject("Dados.Tag_Indice_CSV")
        Set Tamanho = Application.GetObject("Dados.Tag_Tamanho_CSV")
        Set Com = Application.GetObject("DriverPress.IP_CV1_IHM")
        
        If CInt(Indice.Value) < CInt(Tamanho.Value) Then
            ' Fatia o texto armazenado na memória na posição do pipe (|)
            TextoSinal = Application.GetObject("Dados.Tag_ArraySinal_CSV").Value
            ArrayPontos = Split(TextoSinal, "|")
            
            ' Escreve o valor instantâneo na tag de saída analógica do CLP (CV da válvula)
            Com.Value = CDbl(ArrayPontos(CInt(Indice.Value)))
            
            ' Incrementa o cursor da amostra
            Indice.Value = CInt(Indice.Value) + 1
        Else
            ' Fim do sinal: zera a válvula por segurança e desliga o Timer
            Com.Value = 0 
            Application.GetObject("Dados.TagTimer_CSV").Enabled = False
            MsgBox "Ensaio Finalizado com Sucesso!", vbInformation, "Fim da Execução"
        End If
        
    End If
End Sub
```

---

## 6. Passo 5: Atualização do Botão STOP (Segurança Geral)

É mandatório que o botão de Parada / Reset da tela desative o timer de CSV e zere o sinal do atuador imediatamente.

**Objeto:** Botão STOP na tela  
**Evento:** `Click`

```vbscript
Sub CommandButton_Click()
    ' Desliga os Timers de controle
    Application.GetObject("Dados.TagTimer_Rampa").Enabled = False
    Application.GetObject("Dados.TagTimer_CSV").Enabled = False
    
    ' Zera a saída da Válvula imediatamente (0%)
    Application.GetObject("DriverPress.IP_CV1_IHM").Value = 0
    
    ' Desmarca caixas de seleção na tela
    On Error Resume Next
    Screen.Item("chk_CurvaEstatica").Value = False
    Screen.Item("chk_Degraus").Value = False
    On Error GoTo 0
End Sub
```

---

## 7. Passo 6: Exportação dos Dados e Análise Pós-Ensaio

1. **Exportação dos Resultados:**  
   Após o término do ensaio, o Elipse E3 exporta as variáveis gravadas no histórico (`PV_IN`, `CV`, `PV_OUT`, `TIME`) para a pasta oficial de resultados:  
   `IHM_Press_V3/IHM_Press_V3/IHM_Press/RESULTADOS/`
2. **Visualização Gráfica Instantânea:**  
   Para inspecionar as curvas coletadas (gráfico separado em subplots e gráfico com curvas sobrepostas), basta rodar o utilitário Python na pasta de resultados:
   ```powershell
   cd IHM_Press_V3/IHM_Press_V3/IHM_Press/RESULTADOS
   py plotar_dados.py "Random Steps_3.csv"
   ```
3. **Modelagem Matemática:**  
   Com os dados validados, execute os scripts de identificação MISO ARX e MISO NARX na pasta `scripts/`:
   ```powershell
   py scripts/arx_miso.py
   py scripts/narx_miso.py
   ```

---

## 8. Checklist de Resolução de Problemas

- [ ] **Erro "Arquivo CSV não encontrado":** Verifique se o caminho especificado na variável `CaminhoCSV` do botão existe e se a barra invertida foi mantida;
- [ ] **Válvula não responde:** Verifique se o driver `DriverPress` está comunicando com o CLP (indicador de boa qualidade de comunicação na tag);
- [ ] **Taxa de amostragem lenta ou engasgada:** Certifique-se de que o `RepeatInterval` do `TagTimer_CSV` está em `00:00:00.250` e que a rede Ethernet entre o computador do SCADA e o CLP não apresenta saturação de tráfego.
