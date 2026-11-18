import json
import os

class IdempotencyGuard:
    def __init__(self, filepath: str = "data/observacoes_aceites.jsonl"):
        self.filepath = filepath
        self.chaves_conhecidas = set()
        
        # Garantir que a pasta existe logo no início
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._carregar_chaves()

    def _carregar_chaves(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                for linha in f:
                    if linha.strip():
                        try:
                            obs = json.loads(linha)
                            self.chaves_conhecidas.add(obs["event_key"])
                        except (json.JSONDecodeError, KeyError):
                            continue

    def processar(self, observacao: dict) -> str:
        chave = observacao.get("event_key")
        if not chave:
            raise ValueError("A observação não tem uma event_key.")
        
        chave = str(chave)
        if chave in self.chaves_conhecidas:
            return "Existing"

        self.chaves_conhecidas.add(chave)
        
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(observacao) + "\n")
            
        return "Inserted"

