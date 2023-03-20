from scapy.all import *

def main (x):
    try:
        pktParsed = Ether(str(x))
        if pktParsed[UDP].dport != 8805:
            return
        else:
            MACsrc = pktParsed[Ether].src
            MACdst = pktParsed[Ether].dst
            IPsrc = pktParsed[IP].src
            IPdst = pktParsed[IP].dst
            print(IPsrc)
            print(IPdst)
            TCPsrc = pktParsed[UDP].sport
            TCPdst = pktParsed[UDP].dport
            b = IP(src = IPdst, dst = IPsrc)
            sendp(b, iface="eno1")
    except:
        return
    
if __name__ == "__main__":
    sniff(iface="eno1", prn=lambda x: main(x))

