import logging
import socket
from threading import Thread
import paho.mqtt.client as mqtt
from kubernetes import client, config, utils
from scapy.contrib.pfcp import *
import time




FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

LOCAL_DATA_HANDLER = lambda x:x
REMOTE_DATA_HANDLER = lambda x:x

BUFFER_SIZE = 2 ** 15

PFCP_ASSOCIATION_DATA = None
PFCP_SESSION_ESTABLISHMENT_DATA = None
PFCP_SESSION_MODIFICATION_DATA = None

PFCP_ASSOCIATION_RESENDING = False
PFCP_SESSION_ESTABLISHMENT_RESENDING = False
PFCP_SESSION_MODIFICATION_RESENDING = False

PFCP_PROXY_IP = "10.20.1.57"

UPF_IP = "10.20.1.58"

proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    

def pfcp_proxy(host, upfs):
    global proxy_socket

    global PFCP_ASSOCIATION_DATA
    global PFCP_SESSION_ESTABLISHMENT_DATA
    global PFCP_SESSION_MODIFICATION_DATA

    global PFCP_ASSOCIATION_RESENDING
    global PFCP_SESSION_ESTABLISHMENT_RESENDING
    global PFCP_SESSION_MODIFICATION_RESENDING

    global PFCP_PROXY_IP
    
    proxy_socket.bind(ip_to_tuple(host))
    smf = None
    upf_address = ip_to_tuple(upfs)

    while True:
        data, address = proxy_socket.recvfrom(BUFFER_SIZE)
        # print("-"*50)
        if smf == None:
            smf = address
        print("[PFCP Proxy] [info]"+str(PFCP(data)))

        if str(PFCP(data)[0]) == "PFCP / PFCPAssociationSetupRequest" or str(PFCP(data)[0]) == "PFCP / PFCPAssociationSetupResponse" :
            if address == smf:
                data = LOCAL_DATA_HANDLER(data)
                PFCP_ASSOCIATION_DATA = data
                proxy_socket.sendto(data, upf_address)         
            elif address == upf_address and PFCP_ASSOCIATION_RESENDING == False:
                proxy_socket.sendto(data, smf)
                smf = None
            elif address == upf_address and PFCP_ASSOCIATION_RESENDING == True:
                PFCP_ASSOCIATION_RESENDING = False

        elif str(PFCP(data)[0]) == "PFCP / PFCPSessionEstablishmentRequest" or str(PFCP(data)[0]) == "PFCP / PFCPSessionEstablishmentResponse":
            if address == smf:
                data = LOCAL_DATA_HANDLER(data)
                PFCP_SESSION_ESTABLISHMENT_DATA = data
                proxy_socket.sendto(data, upf_address)         
            elif address == upf_address and PFCP_SESSION_ESTABLISHMENT_RESENDING == False:
                pfcp = PFCP(data)
                pfcp[2].ipv4 = PFCP_PROXY_IP
                pfcp[4].ipv4 = PFCP_PROXY_IP
                proxy_socket.sendto(bytes(pfcp), smf)
                smf = None
            elif address == upf_address and PFCP_SESSION_ESTABLISHMENT_RESENDING == True:
                PFCP_SESSION_ESTABLISHMENT_RESENDING = False

        else:
            if address == smf:
                data = LOCAL_DATA_HANDLER(data)
                PFCP_SESSION_MODIFICATION_DATA = data
                proxy_socket.sendto(data, upf_address)         
            elif address == upf_address and PFCP_SESSION_MODIFICATION_RESENDING == False:
                proxy_socket.sendto(data, smf)
                smf = None
            elif address == upf_address and PFCP_SESSION_MODIFICATION_RESENDING == True:
                PFCP_SESSION_MODIFICATION_RESENDING = False
    
def resend_pfcp():
    print("[PFCP Proxy] [info] Resend PFCP Association Setup Request")
    PFCP_ASSOCIATION_RESENDING = True
    time.sleep(7)
    proxy_socket.sendto(PFCP_ASSOCIATION_DATA, (UPF_IP, 8805))
    print("[PFCP Proxy] [info] Resend PFCP Session Establishment Request")
    PFCP_SESSION_ESTABLISHMENT_RESENDING = True
    time.sleep(7)
    proxy_socket.sendto(PFCP_SESSION_ESTABLISHMENT_DATA, (UPF_IP, 8805))
    print("[PFCP Proxy] [info] Resend PFCP Session Modification Request")
    PFCP_SESSION_MODIFICATION_RESENDING = True
    time.sleep(7)
    proxy_socket.sendto(PFCP_SESSION_MODIFICATION_DATA, (UPF_IP, 8805))
    # print("resend pfcp done")
    

def ip_to_tuple(ip):
    ip, port = ip.split(':')
    return (ip, int(port))

def on_message(client, userdata, msg):
    print("[PFCP Proxy] [info] Get UPF error msg to PFCP proxy from UPF moniter")
    # print(client, userdata)
    # print(msg.topic+" "+ msg.payload.decode('utf-8'))
    # if msg.payload.decode('utf-8')[msg.payload.decode('utf-8')]
    resend_pfcp()

def on_connect(client, userdata, flags, rc):
    print("[PFCP Proxy] [info] Connected with result code "+str(rc))
    client.subscribe("upf/status")

def main():
    host = "10.20.1.57:8805"
    upfs = "10.20.1.58:8805"
    # pfcp_proxy(host, upfs)   
    t = Thread(target=pfcp_proxy, args=(host, upfs))
    t.start()
    print("[PFCP Proxy] [info] The PFCP Proxy is started on "+PFCP_PROXY_IP)
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("10.0.0.218", 1883, 60)
    client.loop_forever()
    print("[PFCP Proxy] [info] The MQTT is started")




if __name__ == '__main__':
    main()

    

    