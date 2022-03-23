import base64
import json
import random
import threading
from time import sleep

from olm import Account, OutboundSession, InboundSession, OutboundGroupSession, InboundGroupSession, \
    OlmGroupSessionError
from paho.mqtt import client as mqtt_client

#mqtt pub -h mqtt-endpoint-drogue-dev.apps.wonderful.iot-playground.org -p 443 -u 'device1@example-app' -pw 'hey-rodney' -s -t temp -m '{"temp":42}'

# https://console-drogue-dev.apps.wonderful.iot-playground.org/
# mqtt-integration-drogue-dev.apps.wonderful.iot-playground.org

# broker = 'mqtt.sandbox.drogue.cloud'
broker = 'mqtt-endpoint-drogue-dev.apps.wonderful.iot-playground.org'
port = 443
topic = "secure"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'python-sender@e2e-demo'
password = 'secret'

# drg create app e2e-demo
# drg create device --app e2e-demo python-sender --spec '{"credentials":{"credentials":[{"pass":"secret"}]}}'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.tls_set_context(context=None)
    # client.tls_insecure_set(True)
    client.connect(broker, port)
    return client


def demo_1():
    alice = Account()
    bob = Account()
    bob.generate_one_time_keys(1)
    id_key = bob.identity_keys["curve25519"]
    one_time = list(bob.one_time_keys["curve25519"].values())[0]
    alice_session = OutboundSession(alice, id_key, one_time)

    message = alice_session.encrypt("It's a secret to everybody")
    print(message.ciphertext)

    bob_session = InboundSession(bob, message)
    reconstructed = bob_session.decrypt(message)

    print(reconstructed)

    response = bob_session.encrypt("Hey Alice")
    print(alice_session.decrypt(response))

    # Try to do a MEGOLM session
    sender = OutboundGroupSession()
    secret_session_key = sender.session_key

    group_messages = []
    for i in range(1,100):
        group_messages.append(sender.encrypt(f"Hallo da draußen {i}/99"))
    print(group_messages)

    # One receiver
    receiver1 = InboundGroupSession(secret_session_key)

    for msg in group_messages:
        print(receiver1.decrypt(msg))

    # Invite someone else
    key_50 = receiver1.export_session(50)

    receiver2 = InboundGroupSession.import_session(key_50)

    for msg in group_messages:
        try:
            print(receiver2.decrypt(msg))
        except OlmGroupSessionError:
            print(" - secured - ")

# token = "drg_IJBuCw_yC63fB2B4Xf89DEDt8gzyKyr2SNAVK37lzgr"
# integration_url = "mqtt-integration.sandbox.drogue.cloud"
integration_url = "mqtt-integration-drogue-dev.apps.wonderful.iot-playground.org"
token = "drg_vBYwfh_PR9OxXSVHaodVSxu1FFEqIpUHiQNKP2xhNSR"

secret_session_key = None

def create_receiver():
    client = mqtt_client.Client("my-consumer")
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe("app/e2e-demo", qos=0)
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_subscribe(client, userdata, mid, granted_qos):
        print(f"Subscribed to {mid}")

    # global secret_session_key
    receiver = None

    def on_message(client, userdata, message):
        nonlocal receiver
        if not receiver:
            receiver = InboundGroupSession(secret_session_key)
        json_body = json.loads(message.payload)
        payload = base64.b64decode(json_body["data_base64"])
        # print(f"Got message: {json_body}")
        # print(f"Encrpyted Payload: {payload}")
        msg = receiver.decrypt(payload)
        print(f"Received and decoded: {msg[0]}")

    # Set Connecting Client ID
    client.username_pw_set("julianfeinauer", token)
    # client.username_pw_set(access_token, password=None)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.tls_set_context(context=None)
    # client.tls_insecure_set(True)
    client.connect(integration_url, port)
    return client

if __name__ == '__main__':

    # # Read a message
    # old_session_key = "AgAAAABYnuzL1as6uC+pfl/IkxeMhyJyKUOqt4k0lPWVNrfXt41C/YtBXo4OKhCuSyj+Les4Qo+8UbY815lcE3hEPwb/nzGdfbCjCpfM0WIYdzeBbpcOjUF/6oDFzRBMhbmJTXI+ozmdr1mCrhJGxYPiQA5cnW2gyJXu43ygMw1TLBm25pcF5i3PTtFKb7kQnhFi4bnbpajrFGpAtKHMFVwoNCax0TavMEVaLK3lPQ3ooGg4J+8cFXKniqWIHLhZ/PqdDGUKSEyVc+Ob5JORe78pT8j8ihDU6aXN2rg+ZBEwHvI3Ag"
    # receiver = InboundGroupSession.import_session(old_session_key)
    #
    # msg = "QXdoZEVpRFZVOTBTdHY5K2F2a0tTcTZvOGZqdUFQbUVjUU5JcFRkRFViYUNCSTNmU0ZJSWtyWHMvZVkwUGhsMTJ0ckM2Z01WY3VXc3BVTDZUKzdKVXY0V1JlSHJZMWM2WFhSaGZiSms4WHRFTDF0ekhRRFRPTE5ENVhySFlWYWRPV0FKeFozUjFsWUxMR281QUE="
    # receiver.decrypt(base64.b64decode(msg))

    receiver = create_receiver()
    thread = threading.Thread(target=receiver.loop_forever)
    thread.start()

    client = connect_mqtt()
    client: mqtt_client.Client
    client.loop_start()

    sleep(1)

    sender = OutboundGroupSession()

    secret_session_key = sender.session_key

    print(f"Sesson Key: {sender.session_key}")

    group_messages = []
    for i in range(1, 100):
        sleep(1)
        msg = sender.encrypt(f"Hallo da draußen {i}/99")
        print(f"Encrypted and sent: {msg}")
        result = client.publish(topic, msg)





