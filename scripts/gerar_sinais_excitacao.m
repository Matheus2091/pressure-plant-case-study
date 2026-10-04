% Projeto dos sinais de excitacao para rodar no 1/4 drone (malha fechada)
% Os sinais gerados abaixo sao usados como referencia para a posicao do pendulo
clear
clc

% Ts = 1/1e2; % 100 Hz (Original)
Ts = 1; % 1 Hz (Ajustado para Elipse E3)

zeropad = zeros(1, 10); % Ajustado para Ts=1 (10 segundos de zeros)
valorDC = 45; % Valor medio (RP na posicao de 45 graus)

%% 1. Curva Semi Estatica
disp('Gerando Curva Semi Estatica...');
Tf1 = 60;
amp1 = 90;

t1_temp = 0:Ts:Tf1;
N1_temp = length(t1_temp);
u1_temp = linspace(0, amp1, N1_temp);

% Constroi o sinal (Zeros -> Sobe -> Desce -> Zeros)
u1 = [zeropad u1_temp u1_temp(end:-1:1) zeropad];
N1 = length(u1);
t1 = ((1:N1)-1)*Ts;

% Exportar CSV
csvwrite('../data/sinal_semi_estatica.csv', [t1' u1']);
figure(1); plot(t1, u1); title('Curva Semi Estatica'); xlabel('Tempo (s)'); ylabel('Amplitude');

%% 2. Sequencia de Degraus (Random Steps)
disp('Gerando Sequencia de Degraus...');
rng(0)
Tf2 = 120;
Tduracao = 4; % quantos seg de duracao cada degrau
amp2 = 30; 

t_temp = (0:Ts:Tf2);
N_temp = length(t_temp);
Ndeg = round(Tduracao/Ts); 
Nrand = floor((N_temp-1)/Ndeg);
randSteps = amp2*(2*rand(Nrand,1)-1);
Umat = repmat(randSteps, 1, Ndeg)';

% Constroi o sinal
u2 = [zeropad zeropad ([zeropad zeropad Umat(:)' zeropad zeropad] + valorDC) zeropad zeropad];
N2 = length(u2);
t2 = ((1:N2)-1)*Ts;

% Exportar CSV
csvwrite('../data/sinal_degraus_aleatorios.csv', [t2' u2']);
figure(2); plot(t2, u2); title('Degraus Aleatorios'); xlabel('Tempo (s)'); ylabel('Amplitude');

%% 3. Swept Sine (Chirp)
disp('Gerando Swept Sine...');
Fmax = 0.5;
A = 30; % amplitude
T0 = 60; % period [s]
f0 = 1/T0; % frequency
k1 = 1; % lowest freq
k2 = Fmax/f0; % highest freq

a = pi*(k2-k1)*f0^2;
b = 2*pi*k1*f0;

t3_temp = 0:Ts:T0;
u3_temp = A*sin((a*t3_temp+b).*t3_temp);

% Constroi o sinal
u3 = [zeropad zeropad ([zeropad zeropad u3_temp zeropad zeropad] + valorDC) zeropad zeropad];
N3 = length(u3);
t3 = ((1:N3)-1)*Ts;

% Exportar CSV
csvwrite('../data/sinal_swept_sine.csv', [t3' u3']);
figure(3); plot(t3, u3); title('Swept Sine (Chirp)'); xlabel('Tempo (s)'); ylabel('Amplitude');

%% 4. Multi-Seno (n realizacoes)
disp('Gerando Multi-Seno...');
Fmax4 = 0.5;
Amp4 = 30;

rng(0)
% Requer a funcao multiSine.m no path do MATLAB
try
    [u4_temp, ~] = multiSine(1/Ts, Fmax4, Tf2, Amp4, 1);
    
    u4 = [zeropad zeropad ([zeropad zeropad u4_temp' zeropad zeropad] + valorDC) zeropad zeropad];
    N4 = length(u4);
    t4 = ((1:N4)-1)*Ts;

    % Exportar CSV
    csvwrite('../data/sinal_multiseno.csv', [t4' u4']);
    figure(4); plot(t4, u4); title('Multi-Seno'); xlabel('Tempo (s)'); ylabel('Amplitude');
catch ME
    disp('Aviso: Funcao multiSine nao encontrada no path. Pulando exportacao do multi-seno.');
end

disp('Sinais exportados com sucesso para a pasta /data em formato CSV!');
