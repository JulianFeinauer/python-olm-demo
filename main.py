from olm import Account, OutboundSession, InboundSession, OutboundGroupSession, InboundGroupSession, \
    OlmGroupSessionError

if __name__ == '__main__':
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

