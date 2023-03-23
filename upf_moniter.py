import paho.mqtt.client as mqtt
import json
import time
from kubernetes import client, config, utils
import paho.mqtt.publish as publish

config.load_kube_config()
v1 = client.CoreV1Api()
k8s_client = client.ApiClient()
k8s_api = client.ExtensionsV1beta1Api(k8s_client)

client = mqtt.Client()
# client.connect("10.0.0.218", 1883, 60)
BORKER_IP = "10.0.0.218"
UPF_IP = "10.20.1.58"

def send_upf_err_msg():
    payload = {'upf_status' : "upf_err_ip:10.20.1.58"}
    publish.single("upf/status", json.dumps(payload), hostname=BORKER_IP)
    print("[upf moniter] [info] Send UPF error msg to PFCP proxy")

def restart_upf():
    print("[upf moniter] [info] The UPF restart")
    utils.create_from_yaml(k8s_client, "/home/ubuntu/3.2.1cni_nodeport_up/02-free5gc-upf.yaml")
    print("[upf moniter] [info] UPF restart done")

def upf_moniter():
    print("[upf moniter] [info] The UPF moniter is started on "+UPF_IP)
    while True:
        time.sleep(10)
        ret = v1.list_namespaced_pod("default")
        if len(ret.items) == 0:
            # send_upf_err_msg()
            restart_upf()
            send_upf_err_msg()
        else:
            for i in ret.items:
                if i.metadata.name.find("free5gc-upf") != -1:
                    if i.status.phase != "Running":
                        restart_upf()
                        send_upf_err_msg()

def main():
    upf_moniter()

if __name__ == '__main__':
    main()
                        