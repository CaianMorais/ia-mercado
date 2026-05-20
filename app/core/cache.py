from functools import lru_cache
import requests

@lru_cache(maxsize=128)
def get_state_by_ddd(ddd: str) -> str:
    url_consulta_ddd = f"https://brasilapi.com.br/api/ddd/v1/{ddd}"
    try:
        response = requests.get(url_consulta_ddd, timeout=5)
        if response.status_code == 200:
            return response.json().get("state", "")
    except Exception as e:
        print(f"Erro ao consultar DDD {ddd}: {e}")
    return ""
