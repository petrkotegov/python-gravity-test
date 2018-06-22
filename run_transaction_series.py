import argparse
import datetime as dt
import json
import time
import random
import traceback

from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC

from bitshares import BitShares
from bitshares.account import Account
from bitshares.wallet import Wallet
from bitsharesbase.account import BrainKey
from bitshares.blockchain import Blockchain
from bitsharesbase.chains import known_chains

# parse arguments
parser = argparse.ArgumentParser(description='Runs a sequence of random transactions on the selected node')
parser.add_argument('-ws', '--web-socket', help='gravity node rpc web socket', required=True)
parser.add_argument('-a', '--accounts', type=int, help='number of accounts', required=True)
parser.add_argument('-t', '--transactions', type=int, help='number of transactions', required=True)
parser.add_argument('-p', '--prefix', type=int, help='numeric prefix to account set from 0 to 9999', required=True)
parser.add_argument('-is', '--initial-supply', type=int, help='initial ZGV supply for every created account', required=True)
args = parser.parse_args()
web_socket = args.web_socket
accs_count = args.accounts
tran_count = args.transactions
prefix = args.prefix
init_supply = args.initial_supply

# source account settings
source_name = "nathan"
source_private_key = "5K8ohBujJnbkk7yKLHivNP2P5xBr314Qcq452uHCM9b1PkjdnwT"
source_public_key = "ZGV7EfcnKThkrhWcoDtXQyKE4fuhZVCriqGbnAUQQaLCaKD4jfNRY"

# set chain_id
ws = GrapheneWebsocketRPC(web_socket,"","")
chain_id = ws.get_chain_properties()["chain_id"]
known_chains["ZGV"]["chain_id"] = chain_id

# connect to node, create the wallet
testnet = BitShares(web_socket)
wallet = testnet.wallet
if not wallet.created():
    wallet.create("123")
wallet.unlock("123")
source_account = Account(source_name, bitshares_instance=testnet)

#generate the account name
def get_name(acc_num):
    acc_name = ("g0000r0000v" + str(prefix).zfill(4)
                 + "z" + str(acc_num).zfill(4))
    return acc_name

#create the account if there is no account yet
def create_account(acc_name):
        
    #get account if it exist
    try:
        acc = Account(acc_name, bitshares_instance=testnet)
        print("account exists " + acc_name)
    except:
        acc = None
        print("account doesn't exist " + acc_name)
    
    #check if we already have the active private key
    if acc is not None:
        active_public = acc["active"]["key_auths"][0][0]
        active_private = wallet.getPrivateKeyForPublicKey(active_public)
        if active_private is not None:
            print("active_private is already added")
            return
            
    #keys are generated from brain key which is equal to account name
    owner_key = BrainKey(acc_name, 0)
    active_key = BrainKey(str(owner_key.get_private_key()), 0)
    memo_key = BrainKey(str(active_key.get_private_key()), 0)

    owner_private = str(owner_key.get_private_key())
    owner_public = "ZGV" + str(owner_key.get_public_key())[3:]
    active_private = str(active_key.get_private_key())
    active_public = "ZGV" + str(active_key.get_public_key())[3:]
    memo_private = str(memo_key.get_private_key())
    memo_public = "ZGV" + str(memo_key.get_public_key())[3:]

    #private active key is added to the local key storage
    if not wallet.getPrivateKeyForPublicKey(active_public):
        wallet.addPrivateKey(active_private)
        print("active_private added " + active_private)

    #return if account already exists
    if acc is not None:
        return;    

    #create account
    testnet.create_account(
        acc_name,
        registrar=source_name,
        referrer=source_name,
        owner_key=owner_public,
        active_key=active_public,
        memo_key=memo_public)
    print("account created " + acc_name)

    #transfer initial supply to the account 
    testnet.transfer(acc_name, init_supply, "ZGV", account=source_account)


#create the required number of accounts
for i in range(accs_count):
    acc_name = get_name(i)
    create_account(acc_name)

#make the required number of transactions
random.seed(dt.datetime.now())
for i in range(tran_count):
    
    #sender is picked random
    sender = get_name(random.randint(0, accs_count - 1))

    #receiver is picked random until it is different from sender
    receiver = sender
    while receiver == sender:
        receiver = get_name(random.randint(0, accs_count - 1))
    
    #transaction amount is the random part of the sender's balance
    sender_acc = Account(sender, bitshares_instance=testnet)
    sender_balance = sender_acc.balances[0].amount
    amount = sender_balance * random.random()
    
    try:
        print("transfer " + str(amount) + " from " + sender + " to " + receiver)
        testnet.transfer(receiver, amount, "ZGV", account=sender_acc)
    except Exception as e:
        print(traceback.format_exc())