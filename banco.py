from pathlib import Path
import json
import sys
import duckdb
import pandas as pd

LOCALIDADE = "Garça - SP"
PASTA_DADOS = Path("dados")
ARQUIVO_JSON_BRUTO = PASTA_DADOS / "clima_garca_bruto.json"
ARQUIVO_BANCO_DUCKDB = PASTA_DADOS / "observatorio_garca.duckdb"


def carregar_e_tratar_dados() -> pd.DataFrame:
    if not ARQUIVO_JSON_BRUTO.exists():
        print(f"[ERRO] Arquivo {ARQUIVO_JSON_BRUTO} não encontrado. Execute 'python coleta.py' primeiro.")
        sys.exit(1)

    with open(ARQUIVO_JSON_BRUTO, "r", encoding="utf-8") as f:
        bruto = json.load(f)

    df = pd.DataFrame(bruto["daily"])

    # 1. Padronização dos nomes das colunas
    df = df.rename(
        columns={
            "time": "data_registro",
            "temperature_2m_max": "temp_max_c",
            "temperature_2m_min": "temp_min_c",
            "precipitation_sum": "precipitacao_mm",
        }
    )

    # 2. Conversão e validação de datas e tipos numéricos
    df["data_registro"] = pd.to_datetime(df["data_registro"], format="%Y-%m-%d", errors="raise").dt.date
    df["temp_max_c"] = pd.to_numeric(df["temp_max_c"], errors="coerce")
    df["temp_min_c"] = pd.to_numeric(df["temp_min_c"], errors="coerce")
    df["precipitacao_mm"] = pd.to_numeric(df["precipitacao_mm"], errors="coerce")

    # Inserção da localidade e cálculo de colunas analíticas derivadas
    df.insert(0, "localidade", LOCALIDADE)
    df["temp_media_c"] = ((df["temp_max_c"] + df["temp_min_c"]) / 2.0).round(2)
    df["amplitude_termica_c"] = (df["temp_max_c"] - df["temp_min_c"]).round(2)

    # Ordenação cronológica
    df = df.sort_values("data_registro").reset_index(drop=True)

    # 3. Verificações de qualidade (sem substituir valores ausentes por zero!)
    total_registros = len(df)
    duplicados = int(df.duplicated(subset=["localidade", "data_registro"]).sum())
    nulos_por_coluna = df[["temp_max_c", "temp_min_c", "precipitacao_mm"]].isna().sum().to_dict()
    inconsistencias_temp = int((df["temp_max_c"] < df["temp_min_c"]).sum())
    inconsistencias_chuva = int((df["precipitacao_mm"] < 0).sum())
    dias_cobertura = (df["data_registro"].max() - df["data_registro"].min()).days + 1

    print("=" * 72)
    print("ETAPA 2: RELATÓRIO DE TRATAMENTO E QUALIDADE DOS DADOS (PANDAS)")
    print("=" * 72)
    print(f"Total de registros lidos        : {total_registros} linhas")
    print(f"Período coberto                 : {df['data_registro'].min()} a {df['data_registro'].max()} ({dias_cobertura} dias)")
    print(f"Registros duplicados            : {duplicados}")
    print(f"Valores ausentes (NaN/NULL)     : {nulos_por_coluna}")
    print(f"Inconsistências (Tmax < Tmin)   : {inconsistencias_temp}")
    print(f"Inconsistências (Chuva < 0 mm)  : {inconsistencias_chuva}")
    print("Nota metodológica: Valores ausentes NÃO são substituídos por zero.")

    if duplicados > 0:
        df = df.drop_duplicates(subset=["localidade", "data_registro"], keep="last")

    return df[
        [
            "localidade",
            "data_registro",
            "temp_max_c",
            "temp_min_c",
            "temp_media_c",
            "amplitude_termica_c",
            "precipitacao_mm",
        ]
    ]


def salvar_no_duckdb(df_tratado: pd.DataFrame) -> None:
    conexao = duckdb.connect(str(ARQUIVO_BANCO_DUCKDB))

    # Criação da tabela principal com Chave Primária Composta para evitar duplicações
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS clima_diario (
            localidade VARCHAR NOT NULL,
            data_registro DATE NOT NULL,
            temp_max_c DOUBLE,
            temp_min_c DOUBLE,
            temp_media_c DOUBLE,
            amplitude_termica_c DOUBLE,
            precipitacao_mm DOUBLE,
            PRIMARY KEY (localidade, data_registro)
        );
        """
    )

    # Carga idempotente: INSERT OR REPLACE garante que rodar várias vezes não duplica linhas
    conexao.register("df_view", df_tratado)
    conexao.execute("INSERT OR REPLACE INTO clima_diario SELECT * FROM df_view;")

    contagem_banco = conexao.execute("SELECT COUNT(*) FROM clima_diario;").fetchone()[0]
    print("-" * 72)
    print(f"[SUCESSO] Banco DuckDB atualizado em: {ARQUIVO_BANCO_DUCKDB.resolve()}")
    print(f"[SUCESSO] Total de registros na tabela 'clima_diario': {contagem_banco} (sem duplicatas)")
    print("-" * 72)
    print("Amostra dos 5 primeiros registros carregados na tabela 'clima_diario':")
    amostra = conexao.execute("SELECT * FROM clima_diario ORDER BY data_registro LIMIT 5;").df()
    print(amostra.to_string(index=False))

    print("\n" + "=" * 72)
    print("ETAPA 3: RESULTADOS DAS CONSULTAS SQL E INDICADORES (KPIs)")
    print("=" * 72)

    print("\n[CONSULTA SQL 1 - PA1] Top 5 dias de maior amplitude térmica e extremos:")
    q1 = conexao.execute(
        """
        SELECT data_registro, temp_max_c, temp_min_c, temp_media_c, amplitude_termica_c
        FROM clima_diario
        ORDER BY amplitude_termica_c DESC, temp_max_c DESC
        LIMIT 5;
        """
    ).df()
    print(q1.to_string(index=False))

    extremos = conexao.execute(
        """
        SELECT
            (SELECT temp_max_c FROM clima_diario ORDER BY temp_max_c DESC LIMIT 1) AS maior_temp_max_c,
            (SELECT data_registro FROM clima_diario ORDER BY temp_max_c DESC LIMIT 1) AS data_maior_max,
            (SELECT temp_min_c FROM clima_diario ORDER BY temp_min_c ASC LIMIT 1) AS menor_temp_min_c,
            (SELECT data_registro FROM clima_diario ORDER BY temp_min_c ASC LIMIT 1) AS data_menor_min;
        """
    ).df()
    print("\nExtremos absolutos do período de 30 dias:")
    print(extremos.to_string(index=False))

    print("\n[CONSULTA SQL 2 - PA2] Top 5 dias mais chuvosos em Garça/SP:")
    q2 = conexao.execute(
        """
        SELECT data_registro, precipitacao_mm, temp_max_c, temp_min_c,
               ROUND((precipitacao_mm / NULLIF((SELECT SUM(precipitacao_mm) FROM clima_diario), 0)) * 100, 1) AS pct_chuva_total
        FROM clima_diario
        WHERE precipitacao_mm > 0
        ORDER BY precipitacao_mm DESC
        LIMIT 5;
        """
    ).df()
    print(q2.to_string(index=False))

    print("\n[CONSULTA SQL 3 - PA3] Comportamento térmico entre Dias Chuvosos vs. Dias Secos:")
    q3 = conexao.execute(
        """
        SELECT CASE WHEN precipitacao_mm >= 1.0 THEN 'Dia Chuvoso (>= 1,0 mm)'
                    ELSE 'Dia Seco (< 1,0 mm)' END AS condicao_hidrica,
               COUNT(*) AS qtd_dias,
               ROUND(AVG(temp_max_c), 2) AS media_temp_max_c,
               ROUND(AVG(temp_min_c), 2) AS media_temp_min_c,
               ROUND(AVG(amplitude_termica_c), 2) AS media_amplitude_c,
               ROUND(SUM(precipitacao_mm), 1) AS chuva_acumulada_mm
        FROM clima_diario
        GROUP BY condicao_hidrica
        ORDER BY qtd_dias DESC;
        """
    ).df()
    print(q3.to_string(index=False))

    print("\n[RESUMO DOS 3 INDICADORES]:")
    kpis = conexao.execute(
        """
        SELECT
            ROUND(AVG(temp_media_c), 2) AS kpi1_temp_media_periodo_c,
            ROUND(MAX(temp_max_c), 2) AS kpi1_temp_max_absoluta_c,
            ROUND(MIN(temp_min_c), 2) AS kpi1_temp_min_absoluta_c,
            ROUND(AVG(amplitude_termica_c), 2) AS kpi1_amplitude_media_c,
            ROUND(SUM(precipitacao_mm), 1) AS kpi2_precipitacao_total_mm,
            ROUND(MAX(precipitacao_mm), 1) AS kpi2_maior_chuva_diaria_mm,
            COUNT(*) FILTER (WHERE precipitacao_mm < 1.0) AS kpi3_dias_secos,
            ROUND((COUNT(*) FILTER (WHERE precipitacao_mm < 1.0) * 100.0) / COUNT(*), 1) AS kpi3_pct_secos,
            COUNT(*) FILTER (WHERE precipitacao_mm >= 1.0) AS kpi3_dias_chuvosos,
            ROUND((COUNT(*) FILTER (WHERE precipitacao_mm >= 1.0) * 100.0) / COUNT(*), 1) AS kpi3_pct_chuvosos
        FROM clima_diario;
        """
    ).df()
    print(kpis.to_string(index=False))
    print("=" * 72)

    conexao.close()


if __name__ == "__main__":
    df_limpo = carregar_e_tratar_dados()
    salvar_no_duckdb(df_limpo)