import argparse
import datetime as dt
import json
import time
import sys

from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC

from bitshares import BitShares
from bitshares.account import Account
from bitshares.wallet import Wallet
from bitsharesbase.account import BrainKey
from bitshares.blockchain import Blockchain
from bitsharesbase.chains import known_chains

# parse arguments
parser = argparse.ArgumentParser(description='Scan all accounts and save current balance, activity and emission values')
parser.add_argument('-ws', '--web-socket', help='gravity node rpc web socket', required=True)
args = parser.parse_args()
web_socket = args.web_socket

# set chain_id
ws = GrapheneWebsocketRPC(web_socket,"","")
chain_id = ws.get_chain_properties()["chain_id"]
known_chains["ZGV"]["chain_id"] = chain_id

#connect to the node with python-bitshares
testnet = BitShares(web_socket)
wallet = testnet.wallet
if not wallet.created():
    wallet.create("123")
wallet.unlock("123")

head_block = ws.get_dynamic_global_properties()["head_block_number"]

file_name = "balances_" + web_socket.replace("ws://", "").replace(":", "_") + "_" + str(head_block) + ".csv"

#save initial balances
bc = Blockchain(testnet)
users = bc.get_all_accounts()
with open(file_name, "w") as f:
    for name in users:
        user = Account(name, bitshares_instance=testnet)
        balance = user.balances[0].amount if user.balances else 0
        f.write("%s;%f;%s;%s\n" % (name, balance, user["activity_index"], user["emission_volume"]))
