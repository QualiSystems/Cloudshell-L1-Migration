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
```bash
pip install cloudshell-l1-migration-1.0.1.zip
```
Usage:
======================
1.  **Configure Cloudshell credentials**
    
    In order to use the tool, the user must configure his credentials:

    ```bash
    migration_tool config host <CSHost>
    migration_tool config username <CSUserName>
    migration_tool config password <CSPassword>
    migration_tool config domain <CSDomain>
    migration_tool config port <CSPort>
    ```    
    You may see the current credentials by running:
    
    ```
    migration_tool config
    ```


2.  **Migrate resources**
    
    In order to run migration process, the user have to specify source resources and destination resources. Migration tool uses format below.
    
    ```
    Resource Name/Resource Family/Resource Model/Resource Driver
    ```
    
    *Examples:*
     
    How to migrate all resources for a specific Family/Model          
    ```bash
    migration_tool migrate '*/Old Family/Old model', '*/New Family/New Model/New Driver'
    ```
    How to migrate a list of resources
    
    ```bash
    migration_tool migrate 'L1Switc 1,L1Switch 2', '*/New Family/New Model/New Driver'
    ```
    
        
 