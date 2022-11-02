# XIQ WiNG AP CCG to Location Mapper
### XIQ_AP_ccg_location_map.py

## Purpose
This script can be used to assign floors to WiNG APs based on the Cloud Config Group (CCG) the AP is in. When a WiNG controller is onboarded into XIQ, each online device will be added to XIQ. Each device will be assigned a Cloud Config Group with the name of the rf-domain the AP is part of. The locations, buildings, and floors will need to be previously created with the [XIQ_wing_migrate.py](https://github.com/timjsmith24/XIQ_Wing_location_migration) script. This script will create a building for each rf-domain, and will create floors based on the rf-domain configuration. If there are no floors configured in the rf-domain a 'floor1' will be created in XCQ under the building (rf-domain).
>NOTE: Any device that is online in XIQ and is in the tech-dump when the XIQ_wing_migrate.py script is ran will be moved to the correct floors by that script. This script is to be used for any APs that are not online in XIQ when the script is ran.
>NOTE: Also note that this script will not know if the AP is placed on a specific floor with in the WiNG config. These APs will be moved into the bottom floor of the building (rf-domain) that matches the name of the CCG they are part of.

## Information
### Needed files

The XIQ_AP_ccg_location_map.py script uses several other files. If these files are missing the script will not function.
In the same folder as the XIQ_AP_ccg_location_map.py script there should be an /app/ folder. Inside of this folder should be a ccg_logger.py and xiq_ccg_api.py scripts. After running the script a new file 'ccg_location_map.log' will be created.

### Locations

The script will preform an API call to get the location tree information. This is then used to assign APs to the floor based on the Building (rf-domain name). If there are more then 1 floor associated to the building, the devices will be placed on the bottom floor.

### CCGs

The script will preform API call(s) to collect the CCG information. The API allows for the collection of 100 CCGs at one time. Each CCG will include the name of the CCG as well as a list of device ids that are part of the group.
>NOTE: there is no paging available for the device id lists. Engineering has stated they support up to 1000 devices, but I have not tested this. XIQ needs to respond within 60 secs or the API call will fail. If this is an issue, the page limit can be adjusted to collect less CCGs at once.

### Devices

The script will collect all devices associated with the XIQ instance. The API call that is used will return just the location information and the device ID. This script does not collect the names, models, or other information about the devices. Once all devices are collected, all devices that have no location assigned to them will be filtered out. Using the CCG data pulled, the device ids are mapped to the CCG they are in. Then using the name 'RFD-' is removed for the CCG name and then checked against the names of building in the location data. If a match is found the associated floors of the building are pulled from the data and used in the API call to move devices. 
>NOTE: a single API call is used per location adding multiple devices at one. Engineering has stated they support up to 1000 devices at once, but I have not tested this. If there is an issue, a paging system may need to be added to the script.
>NOTE: XY coordinates are not adjusted for the devices. Each device will be placed at 0,0 (top left corner of the map)

## Running the script

When running the script a prompt will display asking for your XIQ login credentials.
> NOTE: you can by pass this section by entering a valid API Token to line 19 of the XIQ_AP_ccg_location_map.py script
>  - if the added token isn't valid you will see the script fail to gather location tree info with a HTTP Status Code: 401

### messages
Status messages will be printed on the screen as the script collects the data. Once all the data is collected any issue with the mapping of CCGs and locations will be printed on the screen and logged in the log file with ERROR level. If devices are found that can be moved they will print and be logged as INFO messages.
Any issues with API calls will also print to the screen and be logged.
If any API call fail the script will automatically attempt up to 4 additional times.

### flags
There is an optional flag that can be added when the script is ran.
```
--external
```
This flag will allow you to create the locations and assign the devices to locations on an XIQ account you are an external user on. After logging in with your XIQ credentials the script will give you a numeric option of each of the XIQ instances you have access to. Choose the one you would like to use.
```

## requirements
There are additional modules that need to be installed in order for this script to function. They are listed in the requirements.txt file and can be installed with the command 'pip install -r requirements.txt' if using pip.