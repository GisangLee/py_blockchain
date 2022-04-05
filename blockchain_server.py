from flask import Flask, jsonify
import block_chain, wallet

app = Flask(__name__)

cache = {}

def get_blockchain():
    cached_blockchain = cache.get("blockchain")

    if not cached_blockchain:
        miners_wallet = wallet.Wallet()

        cache["blockchain"] = block_chain.BlockChain(
            blockchain_address=miners_wallet.blockchain_address,
            port=app.config['port']
        )

        app.logger.warning({
            "private_key": miners_wallet.private_key,
            "public_key": miners_wallet.public_key,
            "blockchain_address": miners_wallet.blockchain_address
        })

    return cache["blockchain"]

@app.route("/chain", methods=["GET"])
def get_chain():
    blockChain = get_blockchain()
    res = {
        "chain": blockChain.chain
    }
    return jsonify(res), 200

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5001, type=int, help="port to listen on")

    args = parser.parse_args()
    port = args.port
    
    app.config['port'] = port
    app.run(host="0.0.0.0", port=port, threaded=True, debug=True)
