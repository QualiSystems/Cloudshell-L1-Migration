Cloudshell-L1-Migration tool

Written in Python 2.7.10


Introduction
======================
This tool is intended to simplify the process of migration between old L1 shells to alternate ones.
!!! IMPORTANT: The new L1 shell should be manually installed prior to using the tool.

Requirements
======================
1. Windows CloudShell 7 or higher
2. New L1 driver must be already installed (no need for creating any resources using it)

Installation
============
Clone the tool from github. You may either use the Execution Server's Python interpreter or one of your own.

Usage:
======================
1. Configure Cloudshell credentials: In order to use the tool, the user must configure his credentials:
> python main.py --credentials host <CSHost>
> python main.py --credentials username <CSUserName>
> python main.py --credentials password <CSPassword>
> python main.py --credentials domain <CSDomain>
  
You may see the current credentials by running >> python main.py --credentials show

2. Assert old MRV resources to be converted:
> python main.py --resources add <ResourceName>
  
You may delete a resource name:
--resources delete <ResourceName>

3. Configuring the new shell: The user may configure which shell is the new shell (family, model, driver):
> python main.py --new-resource family <ResourceFamily>
> python main.py --new-resource model <ResourceModel>
> python main.py --new-resource model <ResourceDriver>
  
You may see the current configuration by running:
> python main.py --new-resource show

4. Convert:
> python main.py convert
