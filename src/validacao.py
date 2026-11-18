from math import isfinite
import json
from .erros import ErroValidacao
from collections.abc import Mapping
from datetime import datetime, timezone

def normalizar_valor(valor: object, nome_campo: str) -> int | float | None:
    """Valida apenas campos numéricos (int, float) ou None."""
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroValidacao(nome_campo, "tipo_invalido")
    if isinstance(valor, float) and not isfinite(valor):
        raise ErroValidacao(nome_campo, "nao_finito")
    return valor

def normalizar_payload(payload: Mapping[str, object], metadados: Mapping[str, object]) -> list[dict]:
    """
    Valida o payload (números) e os metadados (textos), e devolve a lista de observações.
    """
    if not isinstance(payload, Mapping) or not isinstance(metadados, Mapping):
        raise ErroValidacao("mensagem", "formato_invalido")

    # 1. Validar a presença dos campos numéricos do Payload
    campos_payload = ["temperature", "humidity", "co2"]
    for campo in campos_payload:
        if campo not in payload:
            raise ErroValidacao(campo, "campo_em_falta")

    # 2. Validar a presença dos campos de texto (Metadados)
    campos_meta = ["device_id", "received_at", "quality", "event_key", "source_kind", "acquisition_mode"]
    for campo in campos_meta:
        if campo not in metadados:
            raise ErroValidacao(campo, "campo_em_falta")

    # 3. Processar e juntar os dados
    unidades = {"temperature": "C", "humidity": "%", "co2": "ppm"}
    observacoes = []

    for campo in campos_payload:
        # CORREÇÃO: Só aplicamos normalizar_valor aos números!
        valor_validado = normalizar_valor(payload[campo], campo)

        # Juntamos o payload validado com os metadados (strings)
        observacao = {
            "device_id": metadados["device_id"],
            "received_at": metadados["received_at"],
            "measured_at": datetime.now(timezone.utc).isoformat(), # Pode ser None
            "quantity": campo,
            "unit": unidades[campo],
            "value": valor_validado,
            "quality": metadados["quality"], 
            "event_key": metadados["event_key"],
            "source_kind": metadados["source_kind"],
            "acquisition_mode": metadados["acquisition_mode"]
        }
        print("Payload:")
        print(json.dumps(payload,indent=2))
        print("Metadados:")
        print(json.dumps(observacao,indent=2))
        observacoes.append(observacao)

    return observacoes
