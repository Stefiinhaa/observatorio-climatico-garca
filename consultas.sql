-- ============================================================================
-- consultas.sql — Consultas Analíticas e Cálculo de KPIs no DuckDB
-- ============================================================================

-- 1. Consulta Analítica 1 (PA1):
-- Quais foram os extremos térmicos e os dias de maior amplitude térmica em Garça/SP?
SELECT
    localidade,
    data_registro,
    temp_max_c,
    temp_min_c,
    temp_media_c,
    amplitude_termica_c
FROM clima_diario
ORDER BY amplitude_termica_c DESC, temp_max_c DESC
LIMIT 5;

-- 2. Consulta Analítica 2 (PA2):
-- Quais foram os dias mais chuvosos do período de 30 dias e qual sua participação no total?
SELECT
    localidade,
    data_registro,
    precipitacao_mm,
    temp_max_c,
    temp_min_c,
    ROUND(
        (precipitacao_mm / NULLIF((SELECT SUM(precipitacao_mm) FROM clima_diario), 0)) * 100,
        1
    ) AS percentual_acumulado_mes
FROM clima_diario
WHERE precipitacao_mm > 0
ORDER BY precipitacao_mm DESC
LIMIT 5;

-- 3. Consulta Analítica 3 (PA3):
-- Qual a relação entre a ocorrência de chuva significativa (>= 1,0 mm) e as temperaturas/amplitudes?
SELECT
    CASE
        WHEN precipitacao_mm >= 1.0 THEN 'Dia Chuvoso (>= 1,0 mm)'
        ELSE 'Dia Seco (< 1,0 mm)'
    END AS condicao_hidrica,
    COUNT(*) AS total_dias,
    ROUND(AVG(temp_max_c), 2) AS media_temp_max_c,
    ROUND(AVG(temp_min_c), 2) AS media_temp_min_c,
    ROUND(AVG(amplitude_termica_c), 2) AS media_amplitude_termica_c,
    ROUND(SUM(precipitacao_mm), 1) AS precipitacao_acumulada_mm
FROM clima_diario
GROUP BY condicao_hidrica
ORDER BY total_dias DESC;

-- 4. Consulta Consolidada dos Três Indicadores-Chave (KPIs):
SELECT
    ROUND(AVG(temp_media_c), 2) AS kpi1_temperatura_media_periodo_c,
    ROUND(MAX(temp_max_c), 2) AS kpi1_temperatura_maxima_absoluta_c,
    ROUND(MIN(temp_min_c), 2) AS kpi1_temperatura_minima_absoluta_c,
    ROUND(AVG(amplitude_termica_c), 2) AS kpi1_amplitude_termica_media_c,
    ROUND(SUM(precipitacao_mm), 1) AS kpi2_precipitacao_acumulada_30d_mm,
    COUNT(*) FILTER (WHERE precipitacao_mm < 1.0) AS kpi3_qtd_dias_secos,
    ROUND((COUNT(*) FILTER (WHERE precipitacao_mm < 1.0) * 100.0) / COUNT(*), 1) AS kpi3_percentual_dias_secos,
    COUNT(*) FILTER (WHERE precipitacao_mm >= 1.0) AS kpi3_qtd_dias_chuvosos,
    ROUND((COUNT(*) FILTER (WHERE precipitacao_mm >= 1.0) * 100.0) / COUNT(*), 1) AS kpi3_percentual_dias_chuvosos
FROM clima_diario;