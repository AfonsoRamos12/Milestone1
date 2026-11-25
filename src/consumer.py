import json
import logging
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
    
from .validacao import normalizar_payload
from .idempotency import IdempotencyGuard
from .logger import ReceiptLogger
from .erros import ErroValidacao
import os
from dotenv import load_dotenv

# Carrega as variáveis do ficheiro .env
load_dotenv()
print("Topico:",os.getenv("MQTT_TOPIC"))

    
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
    
class ConsumidorMQTT:
        def __init__(self, config: dict):
            self.config = config
            self.logger_rececao = ReceiptLogger()
            self.guard = IdempotencyGuard()
            
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.username_pw_set(config['mqtt_username'], config['mqtt_password'])
            self.client.on_connect = self._on_connect
            self.client.on_subscribe = self._on_subscribe
            self.client.on_message = self._on_message
    
        def _on_connect(self, client, userdata, flags, reason_code, properties):
            print(self.config['mqtt_topic'])
            if reason_code == 0:
                print("teste")
                client.subscribe(self.config['mqtt_topic'])
                logger.info("Ligado ao TTN.")
        def _on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Se chegarmos aqui, o TTN aceitou a nossa subscrição!
            if reason_code_list[0].is_failure:
                print(f"❌ O TTN REJEITOU A SUBSCRICAO! Motivo: {reason_code_list[0]}")
            else:
                print("✅ TTN ACEITOU A SUBSCRICAO! A aguardar mensagens...")

        def _on_message(self, client, userdata, msg):
           
            try:
                # 1. Descodifica o JSON completo do TTN
                envelope = json.loads(msg.payload.decode('utf-8'))
                print(envelope)
                
    
                # 2. Extrai os dados do TTN
                device_id = envelope.get("end_device_ids", {}).get("device_id") # None se não existir
                uplink = envelope.get("uplink_message", {})
                f_cnt = uplink.get("f_cnt", 0)
                received_at_ttn = uplink.get("received_at")
                payload = uplink.get("decoded_payload", {})
            
    
                if not payload:
                    logger.warning("Mensagem ignorada: Sem payload.")
                    
                    return
                    
    
                # 3. Constrói os metadados (Aqui o Consumidor gera a event_key e a quality provisória)
                # Se o device_id ou o received_at faltarem no TTN, ficam como None. O validador vai rejeitar!
                metadados = {
                    "device_id": device_id,
                    "received_at": received_at_ttn,
                    "measured_at": payload.get("time"),
                    "quality": "1", # Vai ser sobrescrito se o valor for nulo, mas é exigido pelo contrato
                    "event_key": f"{device_id}_{f_cnt}_temp", # Chave provisória, será atualizada
                    "source_kind": "real",
                    "acquisition_mode": "live"
                }
                
                print(f"[MSG] topico={msg.topic}")
                print(f"  payload   = {json.dumps(payload, indent=2, default=str)}")
                print(f"  metadados = {json.dumps(metadados, indent=2, default=str)}")

                # 4. Validar tudo (Payload + Metadados)
                
                observacoes = normalizar_payload(payload=payload, metadados=metadados)
                
                # 5. Processar as observações validadas
                for obs in observacoes:
                    # Ajusta a quality e event_key específicas para esta grandeza
                    obs["quality"] = '0' if obs["value"] is None else '1'
                    obs["event_key"] = f"{device_id}_{f_cnt}_{obs['quantity']}"
    
    
    
                    # Registo no Logger
                    self.logger_rececao.registar(msg.topic, obs, datetime.now(timezone.utc).isoformat())
                    
                    # Idempotência
                    estado = self.guard.processar(obs)
                    logger.info(f"{obs['quantity']}: {estado} (Chave: {obs['event_key']})")
    
            except json.JSONDecodeError:
                logger.error("Falha ao descodificar JSON do TTN.")
            except ErroValidacao as e:
                # Captura o erro e rejeita a mensagem sem crashar
                logger.warning(f"[REJEITADO] Contrato falhou: {e}")
            except Exception as e:
                import traceback
                
                logger.error(f"Erro inesperado: {e}")
                traceback.print_exc()
    
        def iniciar(self):
            self.client.connect(self.config['mqtt_host'], int(self.config['mqtt_port']), 60)
            self.client.loop_forever()
        
if __name__ == "__main__":
      
    
    configuracao = {
        "mqtt_host": os.getenv("MQTT_HOST"),
        "mqtt_port": os.getenv("MQTT_PORT"),
        "mqtt_username": os.getenv("MQTT_USERNAME"),
        "mqtt_password": os.getenv("MQTT_PASSWORD"),
        "mqtt_topic": os.getenv("MQTT_TOPIC")
        }
    if not all(configuracao.values()):
        logger.error("Faltam variáveis no ficheiro .env")
    else:
        ConsumidorMQTT(configuracao).iniciar()
    
    
    
    
    
    
    
