# A Case Study for Nonlinear System Identification of Pressure Control Systems: Open Benchmark Dataset and MISO NARX/ARX Modeling

<div align="center">

[![Paper](https://img.shields.io/badge/IFAC-Conference_Paper-orange.svg)](./paper/main.tex)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![MATLAB](https://img.shields.io/badge/MATLAB-R2022b%2B-red.svg)](https://www.mathworks.com/)
[![SCADA](https://img.shields.io/badge/SCADA-Elipse_E3-green.svg)](https://www.elipse.com.br/)
[![PLC](https://img.shields.io/badge/PLC-Rockwell_Automation-navy.svg)](https://www.rockwellautomation.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Pontifícia Universidade Católica do Paraná (PUCPR)**  
*Graduate Program in Production and Systems Engineering (PPGEPS)*

**Authors:** Matheus Kale Mendes, Fabricio Cassanho Teodoro, Gabriel Ribeiro Tartari, Helon Vicente Hultmann Ayala

</div>

---

## 📌 Executive Summary

This repository provides an **open experimental and computational benchmark for Nonlinear System Identification** based on an industrial compressed-air pressure control plant. The project covers field-level industrial automation (Rockwell CompactLogix PLC and Elipse E3 SCADA) through advanced black-box system identification, comparing linear **MISO ARX** and polynomial **MISO NARX** models estimated via Orthogonal Least Squares (OLS) and Forward Regression Orthogonal Least Squares (FROLS) with the Error Reduction Ratio (ERR) criterion.

The data and code support the paper submitted to the **IFAC** (*International Federation of Automatic Control*):  
📄 *"A case study for nonlinear system identification of pressure control systems"*.

---

## 🏭 Experimental Setup

The physical experimental setup consists of a laboratory-scale compressed-air vessel fed by an industrial screw compressor, regulated by a proportional control valve (4–20 mA), and monitored by piezoresistive pressure transmitters.

```
                  [ Screw Compressor / Supply Manifold ]
                                    │
                                    ▼
                          [ Transmitter PT-02 ]
                       (Upstream Pressure PV_IN)
                                    │
                                    ▼
                         [ Proportional Valve ]
                         (Opening Command CV %)
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Pressure Vessel   │───► [ Transmitter PT-01 ]
                         │     (Chamber)       │     (Downstream Pressure PV_OUT)
                         └─────────────────────┘
                                    │
                                    ▼ (Discharge Orifice)
                                [ Exhaust ]
```

### Process Variables (MISO Configuration)

| Variable | Notation | Unit | Description |
| :--- | :---: | :---: | :--- |
| **`PV_OUT`** | $y(k)$ | psi | **System Output:** Downstream vessel pressure measured by transmitter PT-01. |
| **`CV`** | $u_1(k)$ | % | **Control Input:** Proportional valve opening command (0% to 100%). |
| **`PV_IN`** | $u_2(k)$ | psi | **Disturbance Input:** Upstream supply manifold pressure measured by transmitter PT-02. |

---

## 📊 Benchmark Datasets

All datasets are provided in tabular CSV format with synchronous 4 Hz sampling ($T_s = 0.25\text{ s}$):

- **[`data/Random Steps_4.csv`](./data/Random%20Steps_4.csv):** Benchmark dynamic excitation dataset containing $15,466$ samples ($64.4\text{ minutes}$) under random step sequences covering the full valve operating envelope ($0\text{--}100\%$) and upstream pressure dynamics.
- **[`data/sinal_degraus_aleatorios.csv`](./data/sinal_degraus_aleatorios.csv):** Synthesized excitation sequence for valve command.
- **[`data/sinal_semi_estatica.csv`](./data/sinal_semi_estatica.csv):** Quasi-static ramp test for nonlinear orifice and hysteresis characterization.
- **[`data/sinal_swept_sine.csv`](./data/sinal_swept_sine.csv):** Swept sine excitation signal.

---

## 🧠 Identified Models

### 1. Linear MISO ARX ($\ell = 1$, 6 terms)
$$y(k) = 0.9910\,y(k-1) + 2.1336\times 10^{-3}\,\mathrm{CV}(k-1) - 0.0934\,\mathrm{PV\_IN}(k-1) + 0.2068\,\mathrm{PV\_IN}(k-2) - 0.1223\,\mathrm{PV\_IN}(k-3) + 0.7718$$

### 2. Nonlinear Polynomial MISO NARX ($\ell = 3$, 8 terms via FROLS)
$$
\begin{aligned}
y(k) = &\; 0.5475\,y(k-1) + 0.4449\,y(k-3) + 8.2888\times 10^{-3}\,\mathrm{CV}(k-3) \\
       &\; + 8.3723\times 10^{-7}\,\mathrm{CV}(k-1)\mathrm{PV\_IN}^2(k-2) - 6.6645\times 10^{-7}\,y(k-1)\mathrm{CV}^2(k-1) \\
       &\; - 1.8624\times 10^{-4}\,y^2(k-3)\mathrm{PV\_IN}(k-1) + 1.8385\times 10^{-4}\,y^2(k-3)\mathrm{PV\_IN}(k-2) \\
       &\; - 3.8442\times 10^{-5}\,\mathrm{CV}^2(k-3)
\end{aligned}
$$

---

## 🗂️ Repository Structure

```
pressure-plant-case-study/
│
├── data/                                # Curated experimental datasets
│   ├── Random Steps_4.csv               # Primary benchmark dynamic dataset (4 Hz, 64.4 min)
│   ├── sinal_degraus_aleatorios.csv     # Synthesized random steps excitation
│   ├── sinal_semi_estatica.csv          # Quasi-static ramp excitation
│   └── sinal_swept_sine.csv             # Swept-sine chirp signal
│
├── scripts/                             # Python and MATLAB routines
│   ├── arx_miso.py                      # Linear MISO ARX estimation and validation
│   ├── narx_miso.py                     # Polynomial MISO NARX estimation and validation
│   ├── miso_narx.py                     # FROLS identification core class (MGS + ERR)
│   ├── closed_loop_system_Test.m        # MATLAB closed-loop PI simulation with identified NARX
│   ├── gerar_sinais_excitacao_pressao.m # MATLAB excitation signal generator
│   └── plot_csv_ifac.py                 # Automated publication-ready plotting routine
│
├── images/                              # Publication figures (PNG and PDF)
│   ├── Quasi_Static_Test.png/.pdf       # Preliminary quasi-static characterization
│   ├── Excitation_Random_Steps.png/.pdf # Programmed excitation profile
│   └── Random Steps_4.png/.pdf          # Measured process variables
│
├── IHM_Press_V4/                        # Industrial automation project
│   └── IHM_Press/
│       ├── Planta_PUC_Press.ACD         # Rockwell Studio 5000 PLC project
│       └── IHM_Temp.prj / .dom          # Elipse E3 SCADA project
│
└── paper/                               # IFAC conference paper source files
    ├── main.tex                         # Manuscript LaTeX source
    ├── ifacconf.bib                     # BibTeX reference database
    └── fig/                             # High-resolution vector figures
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Packages: `numpy`, `pandas`, `matplotlib`
- Optional: MATLAB R2022b+

### Installation
```bash
git clone https://github.com/Matheus2091/pressure-plant-case-study.git
cd pressure-plant-case-study
pip install numpy pandas matplotlib
```

### Reproduce System Identification

**1. Run Linear MISO ARX:**
```bash
python scripts/arx_miso.py
```

**2. Run Nonlinear Polynomial MISO NARX:**
```bash
python scripts/narx_miso.py
```

**3. Run Closed-Loop PI Simulation (MATLAB):**
Open and run `scripts/closed_loop_system_Test.m` in MATLAB.

---

## 📑 Citation

If you use this benchmark dataset or code in your research, please cite:

```bibtex
@inproceedings{Mendes2026Pressure,
  author    = {Mendes, Matheus Kale and Teodoro, Fabricio Cassanho and Tartari, Gabriel Ribeiro and Ayala, Helon Vicente Hultmann},
  title     = {A case study for nonlinear system identification of pressure control systems},
  booktitle = {Proceedings of the IFAC Conference},
  year      = {2026},
  address   = {Curitiba, Brazil},
  note      = {Open dataset available at: https://github.com/Matheus2091/pressure-plant-case-study}
}
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
