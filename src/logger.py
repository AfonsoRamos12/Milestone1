import json
import os
from datetime import datetime, timezone

class ReceiptLogger:
    def __init__(self, filepath: str = "data/receipt_log.jsonl"):
        self.filepath = filepath
        
        # Garantir que a pasta 'data' existe
        pasta_destino = os.path.dirname(self.filepath)
        if pasta_destino:
            os.makedirs(pasta_destino, exist_ok=True)

    def registar(self, topico: str, payload: dict, received_at_local: str = None):
        """
        Guarda a tentativa de receção no ficheiro append-only.
        """
        # Se não for passado o tempo local, gera agora
        if not received_at_local:
            received_at_local = datetime.now(timezone.utc).isoformat()

        registo = {
            "topico": topico,
            "received_at_local": received_at_local,
            "payload_bruto": payload
        }
        
        try:
            # Abre o ficheiro em modo 'append' (adiciona ao fim)
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(registo) + "\n")
        except Exception as e:
            print(f"[ERRO] Falha ao gravar no Receipt Logger: {e}")

    def ler_todas_as_tentativas(self) -> list[dict]:
        """
        Lê todas as tentativas gravadas (útil para o script de Replay).
        """
        tentativas = []
        if not os.path.exists(self.filepath):
            return tentativas
            
        with open(self.filepath, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    if linha.strip():
                        tentativas.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue
        return tentativas
