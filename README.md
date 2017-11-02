Cloudshell-L1-Migration tool

Written in Python 2.7.10

This tool is intended to simplify the process of migration between old L1 shells to alternate ones.
In order to use the tool, you may either double click "run.bat" file, or use the command line: >>python mrv_converter.py.
A simple Tkinter GUI will pop up. 

IMPORTANT: The new shell should be manually installed prior to using the script.

The GUI is consisted of four buttons:
1. Credentials: You may enter you credentials for Cloudshell. They are then saved inside forms/credentials.json for the script to use.
2. Resources: You may enter here the names of the old MRV resources that need to be replaced with the new shell (case sensitive). The names are then saved under forms/resource_names.json for the script to use.
3. New Resource: Here you should specify the new resource family, model and driver, and then click "Save" The names are then saved under forms/resource_names.json for the script to use. The data is then saved under forms/new_resource.json for the script to use.

After configuring your data, press "Convert" button. Then, these steps will execute:
1. The script will iterate through all the active reservations, and for each reservation will keep the "relevant" logical routes. "Relevant" logical routes are logical routes that their physical layer go through one of the resources mentioned in the Resources configuration.
2. For each resource mentioned in the New Resource configuration, the script will create a new resource according to the resource template specified in the "New Resource" configuration.
3. For each resource, the script will migrate the physical connections from the old resource to the new one.
4. For each "Relevant Route", the script will remove the route and recreate it, so its physical layer goes through the new resource.
