import datetime as dt
import json
import time
import traceback

from bitshares import BitShares
from bitshares.account import Account
from bitshares.wallet import Wallet
from bitsharesbase.account import BrainKey
from bitshares.blockchain import Blockchain
from bitsharesbase.chains import known_chains

desired_time_range = 600 #10 minutes

#read input json
with open('data/input_package.json', 'r') as package_file:
    package_text = package_file.read()
package = json.loads(package_text)

#scale test start-end time to desired time range
package_start = dt.datetime.strptime(package["test_begin"],"%Y-%m-%dT%H:%M:%S")
package_end = dt.datetime.strptime(package["test_end"],"%Y-%m-%dT%H:%M:%S")
rt_start = dt.datetime.now()
time_scale = (package_end - package_start).total_seconds() / desired_time_range

#connect to the node with python-bitshares
known_chains["ZGV"]["chain_id"] = "60eea51a73bee66a4d744eada6f6bf180678bd63e6297f1ded36afb9872a0351"
testnet = BitShares("ws://localhost:8090")
wallet = testnet.wallet
if not wallet.created():
    wallet.create("123")
wallet.unlock("123")
nathan = Account("nathan", bitshares_instance=testnet)

#add nathans key if needed
nathan_public = "ZGV7EfcnKThkrhWcoDtXQyKE4fuhZVCriqGbnAUQQaLCaKD4jfNRY"
nathan_private = "5K8ohBujJnbkk7yKLHivNP2P5xBr314Qcq452uHCM9b1PkjdnwT"
if not wallet.getPrivateKeyForPublicKey(nathan_public):
    wallet.addPrivateKey(nathan_private)
    print("nathan private key added")

#parse transaction parameters from line
def parse_line(line):
    split = line.split(";")
    tran = {}
    tran["time"] = dt.datetime.strptime(split[0],"%Y-%m-%dT%H:%M:%S")
    tran["from"] = split[1]
    tran["to"] = split[2]
    tran["amount"] = float(split[3])
    tran["fee"] = float(split[4])
    return tran

def create_account(acc_name):
    print("new account " + acc_name)
        
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

    testnet.create_account(
        acc_name,
        registrar="nathan",
        referrer="nathan",
        owner_key=owner_public,
        active_key=active_public,
        memo_key=memo_public)
    print("account created ")

def run_transaction(tran):
    #"from" account have to exist already
    acc_from = Account(tran["from"], bitshares_instance=testnet)
    
    testnet.transfer(tran["to"], tran["amount"], "ZGV", account=acc_from)

#create all accounts (suppose that all new accounts are "to" accounts in the first file)
create_count = 0
csv = package["transaction_sets"][0]["csv_files"][0]
print(csv)
with open('data/' + csv) as f:
    for line in f:
        create_count = create_count + 1
        print(create_count)
        tran = parse_line(line)
        #create "to" account if it doesn't exist
        try:
            Account(tran["to"], bitshares_instance=testnet)
        except:        
            create_account(tran["to"])

#save initial balances
bc = Blockchain(testnet)
users = bc.get_all_accounts()
with open('balances.csv', "w") as f:
    for name in users:
        user = Account(name, bitshares_instance=testnet)
        balance = user.balances[0].amount if user.balances else 0
        f.write("%s;%f\n" % (name, balance))

tran_count = 0
#TODO: make suitable for multiple transaction_sets
for csv in package["transaction_sets"][0]["csv_files"]:
    print(csv)
    with open('data/' + csv) as f:
        for line in f:
            tran = parse_line(line)
            tran_count = tran_count + 1
            print(tran_count)
            print(tran)
            
            rt_delay = (tran["time"] - package_start).total_seconds() / time_scale
            rt_time = rt_start + dt.timedelta(seconds=rt_delay)

            if rt_time > dt.datetime.now():
                sleep_time = rt_time - dt.datetime.now()
                print("sleep for " + str(sleep_time))
                time.sleep(sleep_time.total_seconds())
            try:
                run_transaction(tran)
            except Exception as e:
                print(traceback.format_exc())
                
#retreive all distributed money back
csv = package["transaction_sets"][0]["csv_files"][0]
print(csv)
with open('data/' + csv) as f:
    for line in f:
        tran = parse_line(line)
        if tran["to"] == "nathan":
            continue            
        acc_to = Account(tran["to"], bitshares_instance=testnet)
        if not acc_to.balances:
            continue
        balance = acc_to.balances[0].amount
        if balance > 20:
            testnet.transfer("nathan", balance - 20, "ZGV", account=acc_to)