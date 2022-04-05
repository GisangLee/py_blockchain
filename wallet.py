import codecs, hashlib, base58
from ecdsa import NIST256p, SigningKey
import utils

class Wallet(object):

    def __init__(self):
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()
        self._blockchain_address = self.generate_blockchain_address()

    @property
    def private_key(self):
        return self._private_key.to_string().hex()

    @property
    def public_key(self):
        return self._public_key.to_string().hex()

    @property
    def blockchain_address(self):
        return self._blockchain_address

    def generate_blockchain_address(self):

        # 2 SHA256 for Public Key
        public_key_bytes = self._public_key.to_string()
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()

        # 3 Ripemd160 for SHA256
        ripemd160_bpk = hashlib.new('ripemd160')
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()
        ripemd160_bpk_hex = codecs.encode(ripemd160_bpk_digest, "hex")

        # 4 Add Netwrok bytes
        network_bytes = b'00'
        network_bitcoin_public_key = network_bytes + ripemd160_bpk_hex
        network_bitcoin_public_key_byte = codecs.decode(network_bitcoin_public_key, "hex")

        # 5 Double SHA256
        sha256_bpk = hashlib.sha256(network_bitcoin_public_key_byte)
        sha256_bpk_digest = sha256_bpk.digest()
        sha256_2_nbpk = hashlib.sha256(sha256_bpk_digest)
        sha256_2_nbpk_digest = sha256_2_nbpk.digest()
        sha256_2_nbpk_hex = codecs.encode(sha256_2_nbpk_digest, "hex")

        # 6 Check sum
        check_sum = sha256_2_nbpk_hex[:8]

        # 7 Concat check_sum and public key
        address_hex = (network_bitcoin_public_key + check_sum).decode("utf-8")
        #address_hex = bytes(address_hex, encoding='utf-8')

        # 8 Encoding the key with Base58
        #blockchain_address = base64.b64encode(address_hex).decode("utf-8")
        blockchain_address = base58.b58encode(address_hex).decode("utf-8")

        return blockchain_address



class Transaction(object):

    def __init__(self, sender_private_key, sender_public_key, sender_blockchain_address, recipient_blockchain_address, value):
        self.sender_private_key = sender_private_key
        self.sender_public_key = sender_public_key
        self.sender_blockchain_address = sender_blockchain_address
        self.recipient_blockchain_address = recipient_blockchain_address
        self.value = value

    def generate_signature(self):
        sha256 = hashlib.sha256()
        transaction = utils.sorted_dict_by_key({
            "sender_blockchain_address": self.sender_blockchain_address,
            "recipient_blockchain_address": self.recipient_blockchain_address,
            "value": float(self.value)
        })

        sha256.update(str(transaction).encode("utf-8"))
        message = sha256.digest()

        private_key = SigningKey.from_string(
            bytes().fromhex(self.sender_private_key),
            curve=NIST256p
        )

        private_key_sign = private_key.sign(message)
        signature = private_key_sign.hex()

        return signature













if __name__ == "__main__":
    wallet = Wallet()
    print(wallet.private_key)
    print(wallet.public_key)
    print(wallet._blockchain_address)

    t = Transaction(wallet.private_key, wallet.public_key, wallet.blockchain_address, "Bob", 2.4)

    print(t.generate_signature())