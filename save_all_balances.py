import datetime as dt
import json
import time
import sys

from bitshares import BitShares
from bitshares.account import Account
from bitshares.wallet import Wallet
from bitsharesbase.account import BrainKey
from bitshares.blockchain import Blockchain
from bitsharesbase.chains import known_chains

web_socket = "ws://testnet-seed-6.gravityprotocol.org:4624"
# if len(sys.argv) > 1:
#     web_socket = sys.argv[1]
# print("------")
# print(sys.argv)
# print(len(sys.argv))
# print(sys.argv[0])
# print(web_socket)
# print("------")
file_name = "balances_" + web_socket.replace("ws://", "").replace(":", "_") + ".csv"
chain_id = "ab5071857c28ddbc872d0ca508725fa3006ea7bdfda10f707433021f570fc27e"
#"24dcea1ed640431ac857890d172c0bef103803a4956c4427704cf17439a62160"

#connect to the node with python-bitshares
known_chains["ZGV"]["chain_id"] = chain_id
testnet = BitShares(web_socket)
wallet = testnet.wallet
if not wallet.created():
    wallet.create("123")
wallet.unlock("123")
nathan = Account("nathan", bitshares_instance=testnet) # wallet.addPrivateKey("5K7kBd9GgVC5SLaHQVpA4kP63QfqtVccDTATiChZ2FSnKbVmnZZ")
print(nathan.balances)

#save initial balances
bc = Blockchain(testnet)
users = bc.get_all_accounts()
with open(file_name, "w") as f:
    for name in users:
        user = Account(name, bitshares_instance=testnet)
        balance = user.balances[0].amount if user.balances else 0
        # print(name)
        # print(balance)
        # print(user["poi"])
        f.write("%s;%f;%s\n" % (name, balance, user["activity_index"]))
