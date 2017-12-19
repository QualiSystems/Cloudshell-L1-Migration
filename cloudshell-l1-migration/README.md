Cloudshell-L1-Migration tool

Written in Python 2.7.10


Introduction
======================
This tool is intended to simplify the process of migration between old L1 shells to alternate ones.
!!! IMPORTANT: The new L1 shell should be manually installed prior to using the tool.

Requirements
======================
1. Windows CloudShell 7 or higher
1. New L1 driver already installed (no need for creating any resources using it)

Installation
======================
Install the package py using pip and pointing to the tool's zip path. You may use one of the following:

>>pip install <ToolPath>.
>>python -m pip install <ToolPath>.

You may either use the Execution Server's Python interpreter or one of your own.

'cloudshell-l1-migration' folder will be created under your Python interpreter's Lib/site-packages directory,
navigate using cmd to the created directory.


Usage:
======================
1. Configure Cloudshell credentials: In order to use the tool, the user must configure his credentials:

>> python main.py --credentials host <CSHost>
  
>> python main.py --credentials username <CSUserName>
  
>> python main.py --credentials password <CSPassword>
  
>> python main.py --credentials domain <CSDomain>
  
You may see the current credentials by running >> python main.py --credentials show

2. Assert old MRV resources to be converted - two options:
a. Manual insertion - add resources one by one:

>> python main.py --resources add <ResourceName>
  
You may delete a resource name:
--resources delete <ResourceName>
b. Supplying a file:
You may enter a path to a text file with the resource names splitted by comma (example: resource_a,resource_b,resource_c):
Be aware that the previous resource names will be deleted.
  
>> python main.py --resources /f <FullFilePath>

3. Configuring the new shell: The user may configure which shell is the new shell (family, model, driver):

>> python main.py --new-resource family <ResourceFamily>
  
>> python main.py --new-resource model <ResourceModel>
  
>> python main.py --new-resource model <ResourceDriver>
  
You may see the current configuration by running:

>> python main.py --new-resource show

4. Convert:

>> python main.py convert
