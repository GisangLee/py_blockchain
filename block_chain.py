import logging, sys, time, json, hashlib
import utils

MINING_DFFICULTY = 3
MINING_SENDER = "Dude"
MINING_REWARD = 100.0

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

logging.info("test")
print("test2")


class BlockChain(object):

    def __init__(self, blockchain_address=None):
        self.transaction_pool = []
        self.chain = []
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address

    def create_block(self, nonce, previous_hash):

        block = utils.sorted_dict_by_key({
            "timestamp": time.time(),
            "transactions": self.transaction_pool,
            "nonce": nonce,
            "previous_hash": previous_hash
        })

        self.chain.append(block)
        self.transaction_pool = []

        return block

    def hash(self, block):
        sorted_block_json = json.dumps(block, sort_keys=True)

        return hashlib.sha256(sorted_block_json.encode()).hexdigest()

    def add_transaction(self, sender_blockchain_address, recipient_blockchain_address, value):

        transaction = utils.sorted_dict_by_key({
            "sender_blockchain_address": sender_blockchain_address,
            "recipient_blockchain_address": recipient_blockchain_address,
            "value": float(value)
        })

        self.transaction_pool.append(transaction)
        return True

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


if __name__ == "__main__":
    my_blockchain_address = "123dsad48yq8e9sadsajd1lej28ye"
    block_chain = BlockChain(blockchain_address=my_blockchain_address)
    utils.pprint(block_chain.chain)

    block_chain.add_transaction("Dude", "Alice", 2.0)
    block_chain.mining()
    utils.pprint(block_chain.chain)

    block_chain.add_transaction("Bob", "Carl", 3.4)
    block_chain.add_transaction("X", "Y", 1.4)
    block_chain.mining()
    utils.pprint(block_chain.chain)

    print("my", block_chain.calc_total_amount(my_blockchain_address))
    print("Bob", block_chain.calc_total_amount("Bob"))
    print("Y", block_chain.calc_total_amount("Y"))