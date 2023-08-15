import logging, configparser , json
from threading import Thread
import paho.mqtt.client as mqtt
from gtp_proxy import Gtpu_proxy
from pfcp_proxy import Pfcp_proxy
from test import CustomFormatter

proxy_config = configparser.ConfigParser()
proxy_config.read('config.ini')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(CustomFormatter())
logger.addHandler(console_log)

def main():
    host = proxy_config['pfcp']['proxy_host'] + ":" + proxy_config['pfcp']['port']
    gtpu_host = proxy_config['gtpu']['proxy_host'] + ":" + proxy_config['gtpu']['port']
    upfs = json.loads(proxy_config['upf']['ip'])
    total_upfs = int(proxy_config['upf']['numbers']) - 1
    pfcp_proxy = Pfcp_proxy(host, upfs)
    gtpu_proxy = Gtpu_proxy(gtpu_host, total_upfs, upfs)
    print(total_upfs)
    logging.warning("script starting")
    t = Thread(target=pfcp_proxy.proxy_startup)
    t_gtpu = Thread(target=gtpu_proxy.gtpu_proxy_startup)
    t.start()
    t_gtpu.start()
    client = mqtt.Client()
    client.on_connect = pfcp_proxy.on_connect
    client.on_message = pfcp_proxy.on_message
    mqtt_broker_ip = proxy_config['mqtt']['broker_ip']
    mqtt_port = int(proxy_config['mqtt']['port'])
    client.connect(mqtt_broker_ip, mqtt_port, 60)
    client.loop_forever()
    logging.info("[PFCP Proxy] [info] The MQTT is started")

if __name__ == '__main__':
    main()

    

    
