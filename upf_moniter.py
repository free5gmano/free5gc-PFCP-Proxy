import paho.mqtt.client as mqtt
import json
import time
from kubernetes import client, config, utils

config.load_kube_config()
v1 = client.CoreV1Api()
k8s_client = client.ApiClient()
k8s_api = client.ExtensionsV1beta1Api(k8s_client)

client = mqtt.Client()
client.username_pw_set("try","xxxx")
client.connect("10.0.0.218", 1883, 60)

def send_upf_err_msg():
    payload = {'upf_status' : "upf_err_ip:10.20.1.58"}
    print (json.dumps(payload))
    client.publish("upf/status", json.dumps(payload))
    print("send err msg done.")

def restart_upf():
    utils.create_from_yaml(k8s_client, "/home/ubuntu/3.2.1cni_nodeport_up/02-free5gc-upf.yaml")

while True:
    time.sleep(10)
    ret = v1.list_namespaced_pod("default")
    if len(ret.items) == 0:
        # send_upf_err_msg()
        restart_upf()
        print("restart upf done")
        send_upf_err_msg()
    else:
        for i in ret.items:
            if i.metadata.name.find("free5gc-upf") != -1:
                if i.status.phase != "Running":
                    restart_upf()
                    print("restart upf done")
                    send_upf_err_msg()
                    