from datetime import datetime
from pathlib import Path
import json
import sys
import requests

# Configurações do recorte do projeto: Garça - SP (30 dias)
LOCALIDADE = "Garça - SP"
URL_API_HISTORICA = "https://archive-api.open-meteo.com/v1/archive"

PARAMETROS = {
    "latitude": -22.2106,
    "longitude": -49.6561,
    "start_date": "2026-03-01",
    "end_date": "2026-03-30",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    "timezone": "America/Sao_Paulo",
}

PASTA_DADOS = Path("dados")
ARQUIVO_JSON_BRUTO = PASTA_DADOS / "clima_garca_bruto.json"


def executar_coleta() -> None:
    print("=" * 72)
    print("OBSERVATÓRIO CLIMÁTICO LOCAL — ETAPA 1: COLETA DE DADOS (OPEN-METEO)")
    print("=" * 72)
    print(f"Localidade       : {LOCALIDADE}")
    print(f"Coordenadas      : Lat {PARAMETROS['latitude']} | Lon {PARAMETROS['longitude']}")
    print(f"Período (30 dias): {PARAMETROS['start_date']} até {PARAMETROS['end_date']}")
    print(f"Variáveis        : {PARAMETROS['daily']}")
    print(f"Fuso Horário     : {PARAMETROS['timezone']}")
    print(f"Data/Hora Coleta : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 72)

    try:
        resposta = requests.get(URL_API_HISTORICA, params=PARAMETROS, timeout=30)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as erro:
        print(f"[ERRO] Falha ao consultar a API Open-Meteo: {erro}")
        sys.exit(1)

    dados_json = resposta.json()

    if "daily" not in dados_json or "time" not in dados_json["daily"]:
        print("[ERRO] Resposta da API não contém o objeto 'daily' esperado.")
        sys.exit(1)

    # Preservação da resposta original em JSON sem alterações
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_JSON_BRUTO, "w", encoding="utf-8") as arquivo:
        json.dump(dados_json, arquivo, ensure_ascii=False, indent=2)

    qtd_dias = len(dados_json["daily"]["time"])
    print(f"[SUCESSO] Status HTTP {resposta.status_code} - Coleta concluída!")
    print(f"[SUCESSO] Total de dias retornados pela API: {qtd_dias} registros.")
    print(f"[SUCESSO] JSON original preservado em: {ARQUIVO_JSON_BRUTO.resolve()}")
    print("=" * 72)


if __name__ == "__main__":
    executar_coleta()
