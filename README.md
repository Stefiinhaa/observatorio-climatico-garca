# Observatório Climático Local — Garça/SP (Projeto Integrador Extensionista II)

Repositório oficial do projeto **Observatório Climático Local**, desenvolvido na disciplina de **Projeto Integrador Extensionista II** (Prof. Luiz Henrique).

## 1. Objetivo e Público-Alvo
- **Objetivo:** Coletar, validar, armazenar em banco analítico local (DuckDB) e analisar séries históricas recentes de dados meteorológicos (30 dias consecutivos) do município de **Garça — SP**, transformando-os em indicadores úteis para o manejo agrícola.
- **Público-alvo / Beneficiários:** Pequenos produtores rurais, cafeicultores familiares, horticultores que abastecem feiras locais e técnicos extensionistas do município de Garça/SP.

## 2. Fonte, Localidade, Período e Variáveis
- **Fonte dos Dados:** API Histórica Open-Meteo (`https://open-meteo.com/` — endpoint `https://archive-api.open-meteo.com/v1/archive`).
- **Localidade:** Garça — SP (Latitude `-22.2106`, Longitude `-49.6561`, Fuso horário `America/Sao_Paulo`).
- **Período Analisado:** 30 dias consecutivos (`2026-03-01` a `2026-03-30`).
- **Variáveis Selecionadas:**
  1. `temperature_2m_max` (`temp_max_c`): Temperatura máxima diária a 2 m (°C).
  2. `temperature_2m_min` (`temp_min_c`): Temperatura mínima diária a 2 m (°C).
  3. `precipitation_sum` (`precipitacao_mm`): Precipitação diária acumulada (mm).

## 3. Estrutura de Arquivos do Repositório
```text
├── dados/
│   ├── clima_garca_bruto.json         # Resposta original da API preservada em JSON
│   └── observatorio_garca.duckdb      # Banco de dados analítico DuckDB
├── docs/
│   └── escopo-1/
│       └── AE2/
│           └── relatorio_tecnico_ae2_garca.pdf  # Relatório Técnico e Analítico da AE2
├── .gitignore                         # Exclusão de venv, caches e arquivos temporários
├── coleta.py                          # Script de coleta via Python + Requests
├── banco.py                           # Tratamento com pandas, validação e carga no DuckDB
├── consultas.sql                      # Consultas SQL das perguntas analíticas e KPIs
├── requirements.txt                   # Dependências do projeto
└── README.md                          # Documentação e instruções de execução
```
## 4. Preparação do Ambiente e Instalação das Dependências

Certifique-se de possuir o Python 3.10+ instalado. No terminal, dentro da pasta raiz do projeto, execute:
# 1. Criar o ambiente virtual
python -m venv .venv

# 2. Ativar o ambiente virtual
# No Windows (PowerShell / CMD):
.venv\Scripts\activate
# No Linux / macOS:
source .venv/bin/activate

# 3. Instalar as dependências necessárias
pip install -r requirements.txt

## 5. Ordem e Comandos de Execução (Como Gerar e Acessar o Banco)

Execute os scripts na seguinte ordem:
# Passo 1: Realizar a coleta na API Open-Meteo e salvar dados/clima_garca_bruto.json
python coleta.py

# Passo 2: Tratar e validar os dados com pandas, carregar sem duplicidades no DuckDB
# e exibir no terminal os resultados das consultas SQL e dos 3 KPIs
python banco.py

Nota sobre Idempotência: A tabela clima_diario utiliza chave primária composta (localidade, data_registro) e inserção INSERT OR REPLACE. Executar python banco.py repetidas vezes não gera registros duplicados.


## 6. Principais Limitações e Cuidados Éticos

**Natureza dos dados:** Os dados da API Histórica Open-Meteo provêm de modelos de reanálise atmosférica em grade (ERA5-Land / ECMWF) interpolados para a coordenada de Garça/SP, não devendo ser confundidos com medições diretas de uma estação meteorológica física instalada em uma propriedade rural específica.

**Análise histórica vs. Previsão:** Os dados refletem o diagnóstico histórico de 30 dias ocorridos e não configuram previsão do tempo para dias futuros.

**Ética e LGPD:** O projeto utiliza apenas coordenadas públicas da sede municipal de Garça/SP, sem coletar ou armazenar dados pessoais ou localização privada de produtores rurais.