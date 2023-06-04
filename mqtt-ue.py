import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish

while(True):
    msg = subscribe.simple("free5gc/UE", hostname="10.0.0.218")
    msg = msg.payload.decode('utf-8')
    if(msg == "UE connected"):
        print("an UE has connect")
        publish.single("free5gc/DNS", "an UE has connect", hostname="10.0.0.218")
