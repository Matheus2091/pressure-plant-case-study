%% ========================================================================
%  SIMULAÇÃO DE CONTROLE PI FIXO DE PRESSÃO (MODELO NARX - PLANTA PUCPR)
%  Script com maior tempo de permanência em cada degrau para atingir o RP
% =========================================================================
clc; clear; close all;
Ts = 0.25; % Tempo de amostragem do CLP (4 Hz -> dt = 0.25 s)
% Sequência de degraus de referência dentro da faixa física real do vaso (6.21 a 38 psi)
r_levels = [6.21 12 18 24 30 34 38 34 30 24 18 12 6.21];
t_step   = 60; % Aumentado para 60 segundos por degrau (tempo suficiente para atingir o RP)
t_end    = length(r_levels) * t_step;
N_closed = round(t_end / Ts);
t_closed = (0:N_closed-1) * Ts;
r_psi = zeros(1, N_closed);
for i = 1:length(r_levels)
    r_psi(t_closed >= (i-1)*t_step & t_closed < i*t_step) = r_levels(i);
end
% 2ª Entrada (PV_IN): fixa em 80 psi (vetor estruturado para permitir variações futuras)
p_in_vec = 80.0 * ones(1, N_closed);
% Ganhos fixos do controlador PI obtidos por linearização (tau_cl = 12 s)
Kp_val = 4.1920;
Ki_val = 0.1500;
u_min = 0.0;   % Abertura mínima da válvula [%]
u_max = 100.0; % Abertura máxima da válvula [%]
% Variáveis de Armazenamento
y_psi_hist = zeros(1, N_closed);
u_hist     = zeros(1, N_closed);
% Condições Iniciais nas 3 primeiras amostras (ordem máxima do modelo = 3)
% Equilíbrio exato com válvula completamente fechada (u = 0%) para PV_IN = 80 psi
y_psi_hist(1:3) = 6.21; 
u_hist(1:3)     = 0.0;
% Inicializar o histórico do modelo NARX [amostra(k-1); amostra(k-2); amostra(k-3)]
y_history    = y_psi_hist(3:-1:1)';
u_history    = u_hist(3:-1:1)';
p_in_history = p_in_vec(3:-1:1)';
e_int = 0;
%% Laço Principal de Simulação em Malha Fechada
for k = 4:N_closed
    % 1. Prever saída atual y(k) baseado no histórico de y, u (CV) e p_in (PV_IN)
    y_atual = pressure_narx(y_history, u_history, p_in_history);
    
    % 2. Lei de Controle PI Fixo com Anti-Windup por Clamping
    e = r_psi(k) - y_atual;
    p_term = Kp_val * e;
    
    e_int_cand = e_int + e * Ts;
    u_unsat    = p_term + Ki_val * e_int_cand;
    
    % Saturação física da válvula proporcional (0% a 100%)
    u_k = min(max(u_unsat, u_min), u_max);
    
    % Atualização condicional do integrador (evita windup na saturação)
    if (u_unsat >= u_min && u_unsat <= u_max) || ...
       (u_unsat > u_max && e < 0) || ...
       (u_unsat < u_min && e > 0)
        e_int = e_int_cand;
    end
    
    % 3. Salvar logs para os gráficos
    y_psi_hist(k) = y_atual;
    u_hist(k)     = u_k;
    
    % 4. Atualizar vetores de histórico para o próximo passo
    y_history    = [y_atual;     y_history(1:end-1)];
    u_history    = [u_k;         u_history(1:end-1)];
    p_in_history = [p_in_vec(k); p_in_history(1:end-1)];
end
%% Plotagem dos Resultados
figure('Name', 'Simulação: Controle PI Fixo + NARX', 'Color', 'w');
subplot(2,1,1);
plot(t_closed, r_psi, 'k--', 'LineWidth', 1.5); hold on;
plot(t_closed, y_psi_hist, 'b-', 'LineWidth', 1.8);
ylabel('Pressão [psi]');
title(sprintf('Controle PI Fixo (Kp=%.3f, Ki=%.3f) + Modelo NARX (PV\\_IN = 80 psi - t_{step}=60s)', Kp_val, Ki_val));
legend('Referência [psi]', 'Saída PV\_OUT [psi]', 'Location', 'best');
grid on;
subplot(2,1,2);
stairs(t_closed, u_hist, 'r-', 'LineWidth', 1.5); hold on;
yline(u_max, 'k:'); yline(u_min, 'k:');
xlabel('Tempo [s]');
ylabel('Controle Aplicado CV [%]');
title('Sinal de Controle da Válvula (com Anti-Windup)');
ylim([-5 105]);
grid on;
% =========================================================================
% --- Função Auxiliar: Modelo Não Linear NARX (Equação 2 do Artigo) ---
% =========================================================================
function y_next = pressure_narx(y, u, p_in)
    % Entradas:
    %   y    = [y(k-1);    y(k-2);    y(k-3)]    -> PV_OUT [psi]
    %   u    = [CV(k-1);   CV(k-2);   CV(k-3)]   -> Abertura da válvula [%]
    %   p_in = [PV_IN(k-1);PV_IN(k-2);PV_IN(k-3)]-> Pressão de entrada [psi]
    
    theta = [  0.5475; 
               0.4449; 
               8.29e-3;
               8.37e-7; 
              -6.66e-7; 
              -1.86e-4;
               1.84e-4; 
              -3.84e-5 ];
             
    terms = [ y(1);                         % y(k-1)
              y(3);                         % y(k-3)
              u(3);                         % CV(k-3)
              u(1) * (p_in(2)^2);           % CV(k-1)*PV_IN^2(k-2)
              y(1)  * (u(1)^2);             % y(k-1)*CV^2(k-1)
              (y(3)^2) * p_in(1);           % y^2(k-3)*PV_IN(k-1)
              (y(3)^2) * p_in(2);           % y^2(k-3)*PV_IN(k-2)
              u(3)^2 ];                     % CV^2(k-3)
              
    y_next = sum(theta .* terms);
end