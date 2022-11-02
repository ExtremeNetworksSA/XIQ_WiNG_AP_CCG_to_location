#!/usr/bin/env python3
import logging
import argparse
from math import floor
import sys
import os
import sys
import inspect
import getpass
import json
import pandas as pd
from pprint import pprint as pp
from app.ccg_logger import logger
from app.xiq_ccg_api import XIQ
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
logger = logging.getLogger('CCG_Updater.Main')


XIQ_API_token = ''

pageSize = 100


parser = argparse.ArgumentParser()
parser.add_argument('--external',action="store_true", help="Optional - adds External Account selection, to use an external VIQ")
args = parser.parse_args()

PATH = current_dir

# Git Shell Coloring - https://gist.github.com/vratiu/9780109
RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RESET = "\033[0;0m"

## XIQ EXPORT
if XIQ_API_token:
    x = XIQ(token=XIQ_API_token)
else:
    print("Enter your XIQ login credentials")
    username = input("Email: ")
    password = getpass.getpass("Password: ")
    x = XIQ(user_name=username,password = password)
#OPTIONAL - use externally managed XIQ account
if args.external:
    accounts, viqName = x.selectManagedAccount()
    if accounts == 1:
        validResponse = False
        while validResponse != True:
            response = input("No External accounts found. Would you like to import data to your network?")
            if response == 'y':
                validResponse = True
            elif response =='n':
                sys.stdout.write(RED)
                sys.stdout.write("script is exiting....\n")
                sys.stdout.write(RESET)
                raise SystemExit
    elif accounts:
        validResponse = False
        while validResponse != True:
            print("\nWhich VIQ would you like to import the floor plan and APs too?")
            accounts_df = pd.DataFrame(accounts)
            count = 0
            for df_id, viq_info in accounts_df.iterrows():
                print(f"   {df_id}. {viq_info['name']}")
                count = df_id
            print(f"   {count+1}. {viqName} (This is Your main account)\n")
            selection = input(f"Please enter 0 - {count+1}: ")
            try:
                selection = int(selection)
            except:
                sys.stdout.write(YELLOW)
                sys.stdout.write("Please enter a valid response!!")
                sys.stdout.write(RESET)
                continue
            if 0 <= selection <= count+1:
                validResponse = True
                if selection != count+1:
                    newViqID = (accounts_df.loc[int(selection),'id'])
                    newViqName = (accounts_df.loc[int(selection),'name'])
                    x.switchAccount(newViqID, newViqName)


print("Collecting Location information...")
# Collect Locations
location_df = x.gatherLocations()
location_df.set_index('id',inplace=True)
#print(location_df)

print("Collecting CCGs...")
## Collect CCGs
ccg_data = x.collectCCG(pageSize)
#pp(ccg_data)
ccg_df = pd.DataFrame(columns = ['device_id', 'ccg_id', 'ccg_name'])
for ccg in ccg_data:
    if ccg['device_ids']:
        for device_id in ccg['device_ids']:
            ccg_df = pd.concat([ccg_df,pd.DataFrame([{'device_id': device_id, 'ccg_id': ccg['id'], 'ccg_name': ccg['name']}])])
#ccg_df = pd.DataFrame(ccg_data)
ccg_df.set_index('device_id',inplace=True)
ccg_devices = ccg_df.index.tolist()

print("Collecting Devices...")
device_data = x.collectDevices(pageSize)
device_df = pd.DataFrame(device_data)
device_df.set_index('id',inplace=True)
device_df = device_df[pd.isnull(device_df['location_id'])]
print(f"Found {len(device_df.index)} Devices without locations")
device_list = device_df.index.tolist()
set_location = {}
for device_id in device_list:
    #sys.stdout.write(RED)
    if device_id not in ccg_devices:
        logger.warning(f"device {device_id} is not associated with a Cloud Config Group!!")
    else:
        ccg_name = ccg_df.loc[device_id, 'ccg_name']
        if not isinstance(ccg_name, str):
            logger.warning(f"Device {device_id} is in multiple Cloud Config Groups!!")
        else:
            if "RFD-" not in ccg_name:
                logger.warning(f"Device {device_id} is in CCG {ccg_name} which is not an WiNG RFD created CCG!!")
            else:
                rfd_name = ccg_name.replace("RFD-","")
                if rfd_name in location_df['name'].tolist():
                    filt = (location_df['parent'] == rfd_name)
                    floor = location_df.loc[filt].index.tolist()[-1]
                    #sys.stdout.write(GREEN)
                    logger.info(f"Device {device_id} will be added to {rfd_name} on floor '{location_df.loc[floor,'name']}'")
                    if rfd_name not in set_location:
                        set_location[rfd_name] = {"devices":{"ids":[device_id]},"device_location":{"location_id":floor,"x":0,"y":0,"latitude":0,"longitude":0}}
                    else:
                        set_location[rfd_name]["devices"]["ids"].append(device_id)
                else:
                    logger.warning(f"Can't move device {device_id}. There is not a building with the name {rfd_name}!!")

    #sys.stdout.write(RESET)

for rfd in set_location:
    print(f"Moving APs to {rfd}...", end="")
    response = x.changeAPLocation(set_location[rfd])
    print(response)
