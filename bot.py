import datetime as dt
import json
import time
import random
from datetime import datetime
import traceback

from bitshares import BitShares
from bitshares.account import Account
from bitshares.wallet import Wallet
from bitsharesbase.account import BrainKey
from bitshares.blockchain import Blockchain
from bitsharesbase.chains import known_chains

web_socket = "ws://167.99.204.112:8090"
chain_id = "ab5071857c28ddbc872d0ca508725fa3006ea7bdfda10f707433021f570fc27e" 
known_chains["ZGV"]["chain_id"] = chain_id
testnet = BitShares(web_socket)
wallet = testnet.wallet
if not wallet.created():
    wallet.create("123")
wallet.unlock("123")

nathan_account = Account("nathan", bitshares_instance=testnet)
nathan_balance = nathan_account.balances[0].amount
print(nathan_account)



secret_passphrase = "write something here !!!!"
source_name = "your source account like g2390w9350c1220p0270"
source_private_key = "active private key 5..."
source_public_key = "active public key ZGV..."
#add the source key
if not wallet.getPrivateKeyForPublicKey(source_public_key):
    wallet.addPrivateKey(source_private_key)
    print("source private key added")

def get_name(acc_num):
    random.seed(str(acc_num) + secret_passphrase)
    digits = [str(random.randint(0,9)) for i in range(16)]
    acc_name = ("g" + ''.join(digits[0:4])
                 + "r" + ''.join(digits[4:8])
                 + "v" + ''.join(digits[8:12])
                 + "z" + ''.join(digits[12:16]))
    return acc_name

def get_acc(acc_num):
    name = get_name(acc_num)

    acc = {}
    acc["name"] = name
    return acc

def create_acc(acc_num):
    acc = get_acc(acc_num)
    owner_key = BrainKey(acc["name"] + secret_passphrase, 0)
    active_key = BrainKey(str(owner_key.get_private_key()), 0)
    memo_key = BrainKey(str(active_key.get_private_key()), 0)

    owner_private = str(owner_key.get_private_key())
    owner_public = "ZGV" + str(owner_key.get_public_key())[3:]
    active_private = str(active_key.get_private_key())
    active_public = "ZGV" + str(active_key.get_public_key())[3:]
    memo_private = str(memo_key.get_private_key())
    memo_public = "ZGV" + str(memo_key.get_public_key())[3:]

    if not wallet.getPrivateKeyForPublicKey(active_public):
        wallet.addPrivateKey(active_private)
        print("active_private added " + active_private)

    testnet.create_account(
        acc["name"],
        registrar=source_name,
        referrer=source_name,
        owner_key=owner_public,
        active_key=active_public,
        memo_key=memo_public)
    print(acc["name"] + " account created")
    acc["balance"] = 0
    return acc


source_acc = {}
source_acc["name"] = source_name
source_account = Account(source_name, bitshares_instance=testnet)
source_acc["balance"] = source_account.balances[0].amount
acc_list = [source_acc]

for acc_num in range(1,1234567890):
    acc = get_acc(acc_num)
    try:
        real_acc = Account(acc["name"], bitshares_instance=testnet)
    except:
        break
    if real_acc.balances:
        acc["balance"] = real_acc.balances[0].amount
    else:
        acc["balance"] = 0
    acc_list.append(acc)
    print(acc["name"] + " account found")

while len(acc_list) < 100:
    acc_num = len(acc_list)
    acc = create_acc(acc_num)
    acc_list.append(acc)

turn_counter = 0
while True:
    sender = max(acc_list, key=lambda x:x["balance"])
    random.seed(datetime.now())
    acc_count = len(acc_list)
    receiver = acc_list[random.randint(0, acc_count-1)]
    if sender["name"] == receiver["name"]:
        continue
    sender_acc = Account(sender["name"], bitshares_instance=testnet)
    receiver_acc = Account(receiver["name"], bitshares_instance=testnet)
    try:
        testnet.transfer(receiver["name"], sender["balance"] - 20, "ZGV", account=sender_acc)
    except:
        print(traceback.format_exc())
    print("%d transaction %s %s %d" % (turn_counter, sender["name"], receiver["name"], sender["balance"] - 20))
    sender_acc = Account(sender["name"], bitshares_instance=testnet)
    receiver_acc = Account(receiver["name"], bitshares_instance=testnet)
    sender["balance"] = sender_acc.balances[0].amount
    receiver["balance"] = receiver_acc.balances[0].amount

    turn_counter = turn_counter + 1
#    if turn_counter % 100 == 99:
#        acc = create_acc(len(acc_list))
#        acc_list.append(acc)

