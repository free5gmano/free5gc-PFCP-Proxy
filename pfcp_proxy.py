import configparser
import socket
from scapy.all import *
from scapy.contrib.pfcp import *
import time
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

LOCAL_DATA_HANDLER = lambda x:x
REMOTE_DATA_HANDLER = lambda x:x

BUFFER_SIZE = 2 ** 15

PFCP_ASSOCIATION_DATA = None
PFCP_SESSION_ESTABLISHMENT_DATA = None
PFCP_SESSION_MODIFICATION_DATA = None

PFCP_ASSOCIATION_RESENDING = False
PFCP_SESSION_ESTABLISHMENT_RESENDING = False
PFCP_SESSION_MODIFICATION_RESENDING = False
pfcp_config = configparser.ConfigParser()
pfcp_config.read('config.ini')
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
class Pfcp_proxy:
    def __init__ (self, host, upfs):
        self.host = host
        self.upfs = upfs

    def proxy_startup(self):
        global proxy_socket

        global PFCP_ASSOCIATION_DATA
        global PFCP_SESSION_ESTABLISHMENT_DATA
        global PFCP_SESSION_MODIFICATION_DATA

        global PFCP_ASSOCIATION_RESENDING
        global PFCP_SESSION_ESTABLISHMENT_RESENDING
        global PFCP_SESSION_MODIFICATION_RESENDING
        upf_ip = []
        PFCP_data_count = 0
        PFCP_modify_count = 0 
        PFCP_sess_count = 0
        proxy_socket.bind(self.ip_to_tuple(self.host))
        logging.info('%s %s', '[PFCP Proxy] The PFCP Proxy is started on', self.host)
        smf = None

        for i in self.upfs:
            upf_address = self.ip_to_tuple(i)
            upf_ip.append(self.ip_to_tuple(i)[0])
        while True: 
            data, address = proxy_socket.recvfrom(BUFFER_SIZE)

            if smf == None:
                smf = address
            logging.info('%s %s', "[PFCP Proxy]", str(PFCP(data)))

            if str(PFCP(data)[0]) == "PFCP / PFCPAssociationSetupRequest" or str(PFCP(data)[0]) == "PFCP / PFCPAssociationSetupResponse" :

                if address == smf:
                    data = LOCAL_DATA_HANDLER(data)
                    PFCP_ASSOCIATION_DATA = data
                    for i in self.upfs:
                        PFCP_data_count = PFCP_data_count + 1
                        proxy_socket.sendto(data, self.ip_to_tuple(i))      
                elif address[0] in upf_ip and PFCP_ASSOCIATION_RESENDING == False:
                    PFCP_data_count = PFCP_data_count - 1
                    if PFCP_data_count == 0:
                        proxy_socket.sendto(data, smf)
                        smf = None
                elif address == upf_address and PFCP_ASSOCIATION_RESENDING == True:
                    PFCP_ASSOCIATION_RESENDING = False

            elif str(PFCP(data)[0]) == "PFCP / PFCPSessionEstablishmentRequest" or str(PFCP(data)[0]) == "PFCP / PFCPSessionEstablishmentResponse":
                if(str(PFCP(data)[0]) == "PFCP / PFCPSessionEstablishmentRequest"):
                    logging.info("[PFCP Proxy] a UE has connected")
                    publish.single("free5gc/UE", "UE connected" , qos=0, hostname=pfcp_config['mqtt']['broker_ip'])
                if address == smf:
                    data = LOCAL_DATA_HANDLER(data)
                    PFCP_SESSION_ESTABLISHMENT_DATA = data
                    for i in self.upfs:
                        PFCP_sess_count = PFCP_sess_count + 1
                        proxy_socket.sendto(data, self.ip_to_tuple(i))         
                elif address[0] in upf_ip and PFCP_SESSION_ESTABLISHMENT_RESENDING == False:
                    PFCP_sess_count = PFCP_sess_count - 1
                    if PFCP_sess_count == 0:
                        pfcp = PFCP(data)
                        # pfcp[2].ipv4 = PFCP_PROXY_IP # when using ip in upf config 
                        pfcp[2].id = pfcp_config['pfcp']['proxy_host_fqdn'] # when using fqdn in upf config 
                        pfcp[4].ipv4 = pfcp_config['pfcp']['proxy_host']
                        proxy_socket.sendto(bytes(pfcp), smf)
                        smf = None
                elif address == upf_address and PFCP_SESSION_ESTABLISHMENT_RESENDING == True:
                    PFCP_SESSION_ESTABLISHMENT_RESENDING = False

            else:
                if address == smf:
                    data = LOCAL_DATA_HANDLER(data)
                    PFCP_SESSION_MODIFICATION_DATA = data
                    for i in self.upfs:
                        PFCP_modify_count = PFCP_modify_count + 1
                        proxy_socket.sendto(data, self.ip_to_tuple(i))         
                elif address[0] in upf_ip and PFCP_SESSION_MODIFICATION_RESENDING == False:
                    PFCP_modify_count = PFCP_modify_count - 1
                    if PFCP_modify_count == 0:
                        proxy_socket.sendto(data, smf)
                        smf = None
                elif address == upf_address and PFCP_SESSION_MODIFICATION_RESENDING == True:
                    PFCP_SESSION_MODIFICATION_RESENDING = False

    def resend_pfcp(self):
        logging.info("[PFCP Proxy] Resend PFCP Association Setup Request")
        PFCP_ASSOCIATION_RESENDING = True
        time.sleep(7)
        proxy_socket.sendto(PFCP_ASSOCIATION_DATA, (self.ip_to_tuple(self.upfs[0]), 8805))
        logging.info("[PFCP Proxy] Resend PFCP Session Establishment Request")
        PFCP_SESSION_ESTABLISHMENT_RESENDING = True
        time.sleep(7)
        proxy_socket.sendto(PFCP_SESSION_ESTABLISHMENT_DATA, (self.ip_to_tuple(self.upfs[0]), 8805))
        logging.info("[PFCP Proxy] Resend PFCP Session Modification Request")
        PFCP_SESSION_MODIFICATION_RESENDING = True
        time.sleep(7)
        proxy_socket.sendto(PFCP_SESSION_MODIFICATION_DATA, (self.ip_to_tuple(self.upfs[0]), 8805))
        # print("resend pfcp done")
    def on_message(self,client, userdata, msg):
        logging.info("[PFCP Proxy] Get UPF error msg to PFCP proxy from UPF moniter")
        self.resend_pfcp()

    def on_connect(self, client, userdata, flags, rc):
        logging.info("[PFCP Proxy] mqtt Connected with result code "+str(rc))
        client.subscribe("upf/status")

    def ip_to_tuple(self,ip):
        host = ip.split(':')[0]
        port = ip.split(':')[1]
        return (host, int(port))



    

    
