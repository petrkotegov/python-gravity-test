from datetime import datetime as dt
import collections as c
import json
import os
import re

def read_time(str_time):
    return dt.strptime(str_time, '%d-%m-%Y %H:%M:%S')

def read_param(line):
    parts = line.replace(' ','').split('=')
    if '.' in parts[1]:
        value = float(parts[1])
    else:
        value = int(parts[1])
    return [parts[0], value]

#read transaction log
block_times = []
transactions = []
with open('logs/transaction.log') as f:
    for line in f:
        if line.startswith('--------------- transactions started at '):
            block_time = read_time(line[40:59])
            block_times.append(block_time)
        if re.match('^\d\d-\d\d-\d\d', line):
            tran = line.replace('\n','').split(';')
            tran[0] = read_time(tran[0])
            transactions.append(tran)

#read activity log
activity = []
with open('logs/activity.log') as f:
    for line in f:
        line = line.replace('\n', '')
        if line.startswith('--------------- activity calculation started at'):
            activity.append({})
            activity_time = read_time(line[47:66])
            activity[-1]["timestamp"] = activity_time
            activity[-1]["params"] = {}
            continue
        if '=' in line:
            param = read_param(line)
            activity[-1]["params"][param[0]] = param[1]
            continue
        if line.startswith('name;activity_index'):
            activity[-1]["results"] = []
            continue
        if ';' in line:
            activity[-1]["results"].append(line)
            
#read emission log
emission = []
with open('logs/emission.log') as f:
    for line in f:
        line = line.replace('\n', '')
        if line.startswith('--------------- emission started at '):
            emission.append({})
            emission_time = read_time(line[36:55])
            emission[-1]["timestamp"] = emission_time
            emission[-1]["params"] = {}
            continue
        if '=' in line:
            param = read_param(line)
            emission[-1]["params"][param[0]] = param[1]
            continue
        if line.startswith('name;balance;balance_share'):
            emission[-1]["results"] = []
            continue
        if ';' in line:
            emission[-1]["results"].append(line)

#re-creation of the input package
if not os.path.exists('re-data'):
    os.mkdir('re-data')

#input_package.json file
ip = c.OrderedDict()

ip["test_begin"] = block_times[0].isoformat()
ip["test_end"] = block_times[-1].isoformat()

ip["transaction_sets"] = [c.OrderedDict()]
ip["transaction_sets"][0]["name"] = "testnet replay"
ip["transaction_sets"][0]["csv_files"] = ["transactions.csv"]

ip["initial_balance"] = c.OrderedDict()
ip["initial_balance"]["csv_files"] = ["balance.csv"]

ip["block_times"] = "block_times.csv"
ip["activity_times"] = "activity_times.csv"
ip["emission_times"] = "emission_times.csv"

params = activity[0]["params"]
ip["poi"] = c.OrderedDict()
ip["poi"]["last_poi_processing_time"] = activity[0]["timestamp"].isoformat()
ip["poi"]["poi_period"] = params["activity_period"]
ip["poi"]["total_handled_blocks_count"] = 0
ip["poi"]["poi_weight"] = params["activity_weight"]

ip["poi"]["parameters"] = c.OrderedDict()
ip["poi"]["parameters"]["account_amount_threshold"] = params["account_amount_threshold"]
ip["poi"]["parameters"]["transaction_amount_threshold"] = params["transaction_amount_threshold"]
ip["poi"]["parameters"]["outlink_weight"] = params["outlink_weight"]
ip["poi"]["parameters"]["interlevel_weight"] = params["interlevel_weight"]
ip["poi"]["parameters"]["score_weight_o"] = params["score_weight_o"]
ip["poi"]["parameters"]["score_weight_i"] = params["score_weight_i"]
ip["poi"]["parameters"]["clustering_m"] = params["clustering_m"]
ip["poi"]["parameters"]["clustering_e"] = params["clustering_e"]
ip["poi"]["parameters"]["decay_period"] = params["decay_period"]
ip["poi"]["parameters"]["decay_koefficient"] = params["decay_koefficient"]
ip["poi"]["parameters"]["num_threads"] = params["num_threads"]

params = emission[0]["params"]
ip["emission"] = c.OrderedDict()
ip["emission"]["last_emission_processing_time"] = emission[0]["timestamp"].isoformat()
ip["emission"]["emission_period"] = params["emission_period"]
ip["emission"]["emission_koefficient"] = params["emission_koefficient"]

ip["emission"]["parameters"] = c.OrderedDict()
ip["emission"]["parameters"]["emission_limit"] = params["emissionLimit"]
ip["emission"]["parameters"]["activyty_scale"] = params["activytyScale"]

json_data = json.dumps(ip, indent=4, sort_keys=False)
print(json_data)
with open("re-data/input_package.json", "w") as text_file:
    print(json_data, file=text_file)

#transactions
with open("re-data/transactions.csv", "w") as t_file:
    for tr in transactions:
        line = tr[0].isoformat() + ";" + ";".join(tr[1:])
        t_file.write("%s\n" % line)

#balances
with open("re-data/balances.csv", "w") as b_file:
    b_file.write("nathan;10000000000")

#block times
with open("re-data/block_times.csv", "w") as bt_file:
    for bt in block_times:
        bt_file.write("%s\n" % bt.isoformat())

#activity times
with open("re-data/activity_times.csv", "w") as at_file:
    for a in activity:
        at_file.write("%s\n" % a["timestamp"].isoformat())

#emission times
with open("re-data/emission_times.csv", "w") as et_file:
    for e in emission:
        et_file.write("%s\n" % e["timestamp"].isoformat())

#results
if not os.path.exists('results'):
    os.mkdir('results')

#results_package.json
rp = c.OrderedDict()
rp["activities"] = []
for a in activity:
    act = c.OrderedDict()
    act["timestamp"] = a["timestamp"].isoformat()
    csv = "activity_" + a["timestamp"].strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    act["csv"] = csv
    rp["activities"].append(act)
    with open("results/" + csv, "w") as acsv:
        for line in a["results"]:
            acsv.write("%s\n" % line)
rp["emissions"] = []
for e in emission:
    em = c.OrderedDict()
    em["timestamp"] = e["timestamp"].isoformat()
    params = e["params"]
    em["current_activity"] = params["current_activity"]
    em["last_peak_activity"] = params["last_peak_activity"]
    em["current_supply"] = params["current_supply"]
    em["current_emission"] = params["current_emission"]
    csv = "emission_" + e["timestamp"].strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    em["csv"] = csv
    rp["emissions"].append(em)
    with open("results/" + csv, "w") as ecsv:
        for line in e["results"]:
            ecsv.write("%s\n" % line)

json_data = json.dumps(rp, indent=4, sort_keys=False)
print(json_data)
with open("results/result_package.json", "w") as text_file:
    print(json_data, file=text_file)