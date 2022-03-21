from olm import Account, OutboundSession, InboundSession

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

