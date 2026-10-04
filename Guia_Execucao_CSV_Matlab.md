# Guia de Execução de Sinal CSV (MATLAB) no Elipse E3

Este guia documenta a implementação da funcionalidade que permite ler sinais gerados matematicamente (como Chirp, Multi-seno ou PRBS gerados no MATLAB), gravados em um arquivo `.csv`, e executá-los diretamente na máquina através do Elipse E3.

Para garantir estabilidade, esta funcionalidade foi construída em uma **arquitetura modular isolada**, ou seja, possui um `TagTimer` exclusivo, garantindo que qualquer falha na leitura não afete as rampas padrão da máquina.

---

## 1. Arquitetura de Tags (Pasta: `Dados`)

Para o funcionamento do motor de CSV, é necessário criar os seguintes elementos na pasta `Dados`:

1. **TagTimer_CSV**:
   - `RepeatInterval`: `00:00:01` (1 segundo - ajuste conforme a taxa de amostragem `Ts` se sua rede suportar).
   - `Enabled`: `False`.
2. **Tag_ArraySinal_CSV**: Tag Interna (padrão) para armazenar o texto gigante com todos os dados.
3. **Tag_Tamanho_CSV**: Tag Interna (padrão) para armazenar a quantidade de pontos lidos.
4. **Tag_Indice_CSV**: Tag Interna (padrão) que atua como o cursor/ponteiro de leitura linha a linha.

---

## 2. Formato do Arquivo CSV Esperado

O script espera que o arquivo `.csv` contenha o tempo na coluna 1 e a amplitude na coluna 2, separados por ponto-e-vírgula (`;`).
*Exemplo (`sinal.csv`):*
```text
0.0;45.0
1.0;60.5
2.0;75.0
```

---

## 3. Botão "Importar e Rodar CSV" (Tela Principal)

Crie um botão na tela com a propriedade **Name** igual a `btnImportarCSV`.
Este script abre o arquivo, concatena todas as amplitudes separadas por `|`, salva na Tag de memória, desliga a rampa antiga e aciona o novo Timer.

**Evento:** `Click`
```vbscript
Sub btnImportarCSV_Click()
    Dim fso, arquivo, linha, dados, contador
    Dim stringCompleta
    Dim CaminhoCSV
    
    ' ========================================================
    ' ALTERE O CAMINHO DO ARQUIVO AQUI SE NECESSÁRIO
    CaminhoCSV = "c:\Users\mathe\OneDrive\Desktop\IHM_Press\sinal_teste.csv"
    ' ========================================================
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    stringCompleta = ""
    
    If fso.FileExists(CaminhoCSV) Then
        Set arquivo = fso.OpenTextFile(CaminhoCSV, 1) 
        contador = 0
        
        Do Until arquivo.AtEndOfStream
            linha = arquivo.ReadLine
            If Trim(linha) <> "" Then
                dados = Split(linha, ";")
                ' Garante o uso da vírgula decimal e concatena com pipe (|)
                stringCompleta = stringCompleta & CDbl(Replace(dados(1), ".", ",")) & "|"
                contador = contador + 1
            End If
        Loop
        arquivo.Close
        
        ' Salva na memória do E3
        Application.GetObject("Dados.Tag_ArraySinal_CSV").Value = stringCompleta
        Application.GetObject("Dados.Tag_Tamanho_CSV").Value = contador
        Application.GetObject("Dados.Tag_Indice_CSV").Value = 0
        
        ' Desliga o Timer Antigo e os CheckBoxes para evitar conflitos
        On Error Resume Next
        Application.GetObject("Dados.TagTimer_Rampa").Enabled = False
        Screen.Item("chk_CurvaEstatica").Value = False
        Screen.Item("chk_Degraus").Value = False
        On Error GoTo 0
        
        ' LIGA O TIMER DO CSV
        Application.GetObject("Dados.TagTimer_CSV").Enabled = True
        
        MsgBox "CSV Carregado e Execução Iniciada! (" & contador & " pontos)"
    Else
        MsgBox "Arquivo CSV não encontrado: " & CaminhoCSV
    End If
End Sub
```

---

## 4. O Cérebro da Leitura: TagTimer_CSV

Este script roda a cada "X" milissegundos ou segundos (dependendo do seu `RepeatInterval`). Ele fatia o texto armazenado na memória e envia um ponto por vez para a máquina.

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
            ' Lê o texto longo da memória e corta nas posições do pipe (|)
            TextoSinal = Application.GetObject("Dados.Tag_ArraySinal_CSV").Value
            ArrayPontos = Split(TextoSinal, "|")
            
            ' Envia a posição atual para a Válvula/Máquina
            Com.Value = CDbl(ArrayPontos(CInt(Indice.Value)))
            
            ' Avança o ponteiro
            Indice.Value = CInt(Indice.Value) + 1
        Else
            ' O arquivo chegou no fim! Zera a máquina e desliga o Timer.
            Com.Value = 0 
            Application.GetObject("Dados.TagTimer_CSV").Enabled = False
        End If
        
    End If
End Sub
```

---

## 5. Atualização no Botão STOP Geral

Sempre que adicionar um módulo novo que controla a máquina, é vital atualizar o botão STOP (Parada de Emergência/Reset) para desarmar o novo sistema.

**Evento:** `Click` (do seu botão STOP na tela)
```vbscript
Sub CommandButton_Click()
    ' Desliga os Timers
    Application.GetObject("Dados.TagTimer_Rampa").Enabled = False
    Application.GetObject("Dados.TagTimer_CSV").Enabled = False
    
    ' Zera a Máquina
    Application.GetObject("DriverPress.IP_CV1_IHM").Value = 0
    
    ' Desmarca os Checkboxes visualmente
    On Error Resume Next
    Screen.Item("chk_CurvaEstatica").Value = False
    Screen.Item("chk_Degraus").Value = False
    On Error GoTo 0
End Sub
```
