% =========================================================================
% Projeto dos sinais de excitacao para rodar na Planta de Pressão (Malha Aberta)
% Os sinais gerados abaixo sao usados como referencia para o setpoint da posição.
% =========================================================================
clear
clc

% [ALTERAÇÃO 1]: A taxa de amostragem original era Ts = 1/1e2 (10 milissegundos).
% Como a Planta de Pressão e o Elipse E3 vão rodar a 250ms, alteramos para 0.25.
Ts = 0.25; % 250ms de tempo de amostragem

% [ALTERAÇÃO 2]: O original usava "zeropad = zeros(1,500)". 
% 500 amostras a 10ms dariam 5 segundos. Se mantivéssemos 500 amostras a 250ms,
% a máquina ficaria 125 segundos (mais de 2 minutos) parada.
% Por isso, criamos a variável 'tempo_repouso' em segundos.
tempo_repouso = 10; % Tempo (em segundos) que a máquina fica parada no início/fim
% Calcula matematicamente quantos pontos zeros são necessários para dar 10s:
zeropad = zeros(1, round(tempo_repouso / Ts)); 

% [ALTERAÇÃO 3]: O ponto de operação foi alterado do original 45 para 50.
valorDC = 50; % Setpoint médio (50%)

%% ========================================================================
% 1. Curva Semi Estatica (Sobe em rampa, desce em rampa)
% =========================================================================
disp('Gerando Curva Semi Estatica...');
Tf1 = 60; % Tempo total da rampa de subida (60 segundos)
amp1 = 100; % Amplitude máxima que a rampa vai atingir

% Cria o vetor de tempo t1_temp (de 0 até 60s pulando de 0.25 em 0.25)
t1_temp = 0:Ts:Tf1;
N1_temp = length(t1_temp);

% Gera um vetor que sobe linearmente de 0 até 100% no tempo N1_temp
u1_temp = linspace(0, amp1, N1_temp);

% Constrói o sinal final colando as partes: 
% 10s de zero (zeropad) -> Sobe a rampa (u1_temp) -> Desce a rampa invertida (u1_temp(end:-1:1)) -> 10s de zero
u1 = [zeropad u1_temp u1_temp(end:-1:1) zeropad];
N1 = length(u1);
% Recalcula o tempo total final baseado no tamanho do sinal
t1 = ((1:N1)-1)*Ts;

% [ALTERAÇÃO 4]: Adicionado csvwrite para exportar automaticamente
csvwrite('../data/sinal_semi_estatica.csv', [t1' u1']);
figure(1); plot(t1, u1); title('Curva Semi Estatica'); xlabel('Tempo (s)'); ylabel('Amplitude (%)');

%% ========================================================================
% 2. Sequencia de Degraus Aleatorios (Random Steps)
% =========================================================================
disp('Gerando Sequencia de Degraus...');
rng(0) % Fixa a semente aleatória (garante que os degraus sejam sempre os mesmos)
Tf2 = 600; % Tempo total gerando degraus
Tduracao = 120; % Duração de cada degrau "parado" em segundos
amp2 = 50; % Variação máxima do degrau (vai variar entre -50 e +50 em torno do DC)

t_temp = (0:Ts:Tf2);
N_temp = length(t_temp);

% Calcula a quantidade de pontos necessários para durar 2 segundos
Ndeg = round(Tduracao/Ts); 
% Descobre quantos degraus aleatórios cabem dentro dos 120 segundos
Nrand = floor((N_temp-1)/Ndeg);
% Sorteia os valores dos degraus entre -amp2 e +amp2
randSteps = amp2*(2*rand(Nrand,1)-1);
% Clona o valor sorteado para que ele fique constante por 'Ndeg' amostras
Umat = repmat(randSteps,1,Ndeg)';

% Constrói o sinal colando 2x zeropads, a matriz de degraus somada com o 
% setpoint médio (valorDC = 50), e finaliza com mais zeropads
u2 = [zeropad zeropad ([zeropad zeropad Umat(:)' zeropad zeropad] + valorDC) zeropad zeropad];
N2 = length(u2);
t2 = ((1:N2)-1)*Ts;

% Exporta CSV
csvwrite('../data/sinal_degraus_aleatorios.csv', [t2' u2']);
figure(2); plot(t2, u2); title('Degraus Aleatorios'); xlabel('Tempo (s)'); ylabel('Amplitude (%)');

%% ========================================================================
% 3. Swept Sine (Chirp) - Frequencia aumentando gradativamente
% =========================================================================
disp('Gerando Swept Sine BEM LENTO...');
Fmax3 = 0.2; % Frequência máxima reduzida (rad/s) para a planta acompanhar
A3 = 50; % Amplitude da onda

T0 = 600; % Período do sinal esticado para 10 minutos (600 segundos)
f0 = 1/T0; % Frequência fundamental
k1 = 1; % Índice de frequência mais baixo
k2 = Fmax3/f0; % Índice de frequência mais alto

% Constantes da equação do Chirp
a = pi*(k2-k1)*f0^2;
b = 2*pi*k1*f0;

% Gera o vetor de tempo do Swept Sine
t3_temp = 0:Ts:T0;
% Equação matemática que gera a onda com frequência crescente
u3_temp = A3*sin((a*t3_temp+b).*t3_temp);

% Constrói o sinal adicionando os zeropads nas pontas e somando o valor médio (50%)
u3 = [zeropad zeropad ([zeropad zeropad u3_temp zeropad zeropad] + valorDC) zeropad zeropad];
N3 = length(u3);
t3 = ((1:N3)-1)*Ts;

% Exporta CSV
csvwrite('../data/sinal_swept_sine.csv', [t3' u3']);
figure(3); plot(t3, u3); title('Swept Sine (Chirp)'); xlabel('Tempo (s)'); ylabel('Amplitude (%)');

%% ========================================================================
% 4. Multi-Seno (Múltiplas frequências somadas)
% =========================================================================
disp('Gerando Multi-Seno...');
Fmax4 = 0.5; % Frequência máxima contida no sinal
Amp4 = 50; % Amplitude global do sinal resultante

rng(0)
% [OBSERVAÇÃO]: Tenta executar a função customizada multiSine. 
% Se a função não estiver na mesma pasta que este script, ele não dará crash,
% apenas avisará no painel (graças ao try/catch).
try
    [u4_temp, ~] = multiSine(1/Ts, Fmax4, Tf2, Amp4, 1);
    
    % Constrói o sinal somando o DC e colocando zeros nas pontas
    u4 = [zeropad zeropad ([zeropad zeropad u4_temp' zeropad zeropad] + valorDC) zeropad zeropad];
    N4 = length(u4);
    t4 = ((1:N4)-1)*Ts;

    % Exporta CSV
    csvwrite('../data/sinal_multiseno.csv', [t4' u4']);
    figure(4); plot(t4, u4); title('Multi-Seno'); xlabel('Tempo (s)'); ylabel('Amplitude (%)');
catch ME
    disp('Aviso: Funcao multiSine nao encontrada na pasta. Sinal multi-seno nao exportado.');
end

disp('Todos os sinais (Ts = 250ms) foram exportados com sucesso em CSV!');
