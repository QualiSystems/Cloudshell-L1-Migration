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
pip install cloudshell-l1-migration-x.x.x.zip
```
Usage:
======================
1.  **Basic Configuration**
    * Cloudshell credentials:
        
        *In order to use the tool, the user must configure his credentials*

    ```bash
    migration_tool config host <CSHost>  # CS Host
    migration_tool config username <CSUserName> # CS Username
    migration_tool config password <CSPassword> # CS Password
    migration_tool config domain <CSDomain> # CS Domain
    migration_tool config port <CSPort> # CS Port
    ```    
    * Logging level:
    
        *To get detailed output, specify logging level*
    
    ```bash
    migration_tool config logging_level DEBUG
    ```
    
    * Backup location:
        
        *Folder where to save backup* 
    ```bash
    migration_tool config backup_location C:\Backup # Backup folder
    ```
    
    * Name prefix:
        * New created resources will be used SRC resource name with the prefix
    ```bash
    migration_tool config name_prefix "New_" # Prefix for new resource

    ```
    * You may see the current settings by running:
    
    ```bash
    migration_tool config
    ```
    
    
2.  **Patterns Table**
    Patterns distinguish blocks of relative address which will be used for ports association.
    To compare full string of relative address use "(.*)".
    
    * Add new pattern associated with resource Family/Model:
    ```bash
        migration_tool config --patterns_table "L1 Switch/Test Switch Chassis" ".*/(.*)/(.*)"
    ```
    * List patterns
    ```bash
        migration_tool config --patterns_table
    ```

3.  **Migrate resources**
    
    In order to run migration process, the user have to specify source resources(SRC) and destination resources(DST). Migration tool uses format below.
    
    ```
    Resource Name/Resource Family/Resource Model/Resource Driver
    ```
    
    *Examples:*
     
    How to migrate all resources for a specific Family/Model 
             
    ```bash
    migration_tool migrate "*/Old Family/Old model" "*/New Family/New Model" --override
    ```
    
    How to migrate a list of resources
    
    ```bash
    migration_tool migrate "L1 Switch 1, L1 Switch2" "*/New Family/New Model/New Driver" --override
    ```
    
    How to migrate to existing resource
    
    ```bash
    migration_tool migrate "L1 Switch 1, L1 Switch2" "New Switch1, New Switch 2" --override
    ```    
    
    Dry run option used to verify port association. It does not remove routes and switch connections.
    
    ```bash
    migration_tool migrate --dry-run "L1 Switch 1,L1 Switch 2" "*/New Family/New Model/New Driver" --override
    ```
    
4. **Backup/Restore**
    * Backup specified resources
    
        ```bash
        migration_tool backup "L1 Switch 1,L1 Switch 2"
        ```
        Backup to a specified file
        
        ```bash
        migration_tool backup "L1 Switch 1,L1 Switch 2" --backup-file c:\Backup\backup.yaml
        ```
    
    * Restore
    
        Restore connections and routes for resources from backup file
        
        ```bash
        migration_tool restore --backup-file c:\Backup\backup.yaml --override
        ```
        
        Restore connections and routes for specified resources 
        
        ```bash
        migration_tool restore --backup-file c:\Backup\backup.yaml "L1 Switch 1" --override
        ```

        Restore connections only
        
        ```bash
        migration_tool restore --backup-file c:\Backup\backup.yaml "L1 Switch 1" --connections --override
        ```
        
        Restore routes only
        
        ```bash
        migration_tool restore --backup-file c:\Backup\backup.yaml "L1 Switch 1" --routes --override
        ```