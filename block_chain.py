import logging, sys, time, json, hashlib, contextlib, threading, requests
import utils
from ecdsa import NIST256p, VerifyingKey

MINING_DFFICULTY = 3
MINING_SENDER = "Dude"
MINING_REWARD = 1.0
MINING_TIMER_SEC = 20

BLOCKCHAIN_PORT_RANGE = (5000, 5003)
NEIGHBORS_IP_RANGE_NUM = (0, 1)
BLOCKCHAIN_NEIGHBORS_SYNC_TIME_SEC = 20

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


class BlockChain(object):

    def __init__(self, blockchain_address=None, port=None):
        self.transaction_pool = []
        self.chain = []
        self.neighbors = []
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address
        self.port = port
        self.mining_semaphore = threading.Semaphore(1)
        self.sync_neighbors_semaphore = threading.Semaphore(1)

    def set_neighbors(self):

        self.neighbors = utils.find_neighbors(
            utils.get_host(),
            self.port,
            NEIGHBORS_IP_RANGE_NUM[0],
            NEIGHBORS_IP_RANGE_NUM[1],
            BLOCKCHAIN_PORT_RANGE[0],
            BLOCKCHAIN_PORT_RANGE[1]
        )

        logger.info({
            "action": "set_neighbors",
            "neighbors": self.neighbors
        })

    def sync_neighbors(self):
        is_aquire = self.sync_neighbors_semaphore.acquire(blocking=False)

        if is_aquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self.sync_neighbors_semaphore.release)
                self.set_neighbors()
                loop = threading.Timer(BLOCKCHAIN_NEIGHBORS_SYNC_TIME_SEC, self.set_neighbors)

                loop.start()

    def create_block(self, nonce, previous_hash):

        block = utils.sorted_dict_by_key({
            "timestamp": time.time(),
            "transactions": self.transaction_pool,
            "nonce": nonce,
            "previous_hash": previous_hash
        })

        self.chain.append(block)
        self.transaction_pool = []

        for node in self.neighbors:
            requests.delete(f"http://{node}/transactoins")

        return block

    def hash(self, block):
        sorted_block_json = json.dumps(block, sort_keys=True)

        return hashlib.sha256(sorted_block_json.encode()).hexdigest()

    def add_transaction(self, sender_blockchain_address, recipient_blockchain_address, value, sender_public_key=None, signature=None):

        transaction = utils.sorted_dict_by_key({
            "sender_blockchain_address": sender_blockchain_address,
            "recipient_blockchain_address": recipient_blockchain_address,
            "value": float(value)
        })

        if sender_blockchain_address == MINING_SENDER:
            self.transaction_pool.append(transaction)
            return True
        
        if self.verify_transaction_signature(sender_public_key, signature, transaction):
            self.transaction_pool.append(transaction)

            # if self.calc_total_amount(sender_blockchain_address) < float(value):
            #     logger.error({
            #         "action": "add_transaction_error",
            #         "error": "no value"
            #     })
            #     return False

            return True

        return False

    def create_transaction(
            self,
            sender_blockchain_address,
            recipient_blockchain_address,
            sender_public_key,
            value,
            signature
    ):

        is_transacted = self.add_transaction(sender_blockchain_address, recipient_blockchain_address, value, sender_public_key, signature)

        # TODO
        # Sync

        if is_transacted:
            for node in self.neighbors:

                requests.put(
                    f"http://{node}/transactions",
                    json={
                        "sender_blockchain_address": sender_blockchain_address,
                        "recipient_blockchain_address": recipient_blockchain_address,
                        "value": value,
                        "sender_public_key": sender_public_key,
                        "signature": signature,
                    }
                )

        return is_transacted

    def verify_transaction_signature(self, sender_public_key, signature, transaction):
        sha256 = hashlib.sha256()
        sha256.update(str(transaction).encode("utf-8"))
        message = sha256.digest()
        signature_bytes = bytes().fromhex(signature)
        verifying_key = VerifyingKey.from_string(
            bytes().fromhex(sender_public_key),
            curve=NIST256p
        )

        verified_key = verifying_key.verify(signature_bytes, message)

        return verified_key

    def valid_proot(self, transactions, previous_hash, nonce, difficulty=MINING_DFFICULTY):
        guess_block = utils.sorted_dict_by_key({
            "transaction": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce  
        })

        guess_hash = self.hash(guess_block)

        return guess_hash[:difficulty] == "0"*difficulty


    def proof_of_work(self):
        transaction = self.transaction_pool.copy()
        previous_hash = self.hash(self.chain[-1])
        nonce = 0

        while self.valid_proot(transaction, previous_hash, nonce) is False:
            nonce += 1

        return nonce

    def mining(self):

        if not self.transaction_pool:
            return False

        self.add_transaction(
            sender_blockchain_address=MINING_SENDER,
            recipient_blockchain_address=self.blockchain_address,
            value=MINING_REWARD
        )

        nonce = self.proof_of_work()
        previous_hash = self.hash(self.chain[-1])

        self.create_block(nonce, previous_hash)

        logger.info({
            "action": 'mining',
            "status": "success"
        })

        return True

    def start_mining(self):
        is_aquire = self.mining_semaphore.acquire(blocking=False)

        if is_aquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self.mining_semaphore.release)
                self.mining()
                loop = threading.Timer(MINING_TIMER_SEC, self.start_mining)
                loop.start()

    def calc_total_amount(self, blockchain_address):
        total_amount = 0.0

        for block in self.chain:
            for transaction in block['transactions']:
                value = float(transaction["value"])

                if blockchain_address == transaction["recipient_blockchain_address"]:
                    total_amount += value
                
                if blockchain_address == transaction["sender_blockchain_address"]:
                    total_amount -= value
        return total_amount
