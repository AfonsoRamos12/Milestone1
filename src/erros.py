# src/erros.py

class ErroValidacao(Exception):
	"""Exceção . . ."""
	def __init__(self, campo: str, motivo: str) -> None:
		self.campo = campo
		self.motivo = motivo
		super().__init__(f"Campo'{campo}'rejeitado. Motivo:{motivo}")
	
	
	
