# **CloudShell Migration Tool**  

Release date: March 2019

Document version: 1.0

# In This Guide
* [Introduction](#introduction)
    * [Workflow](#workflow)
* [Installation](#installation)
    * [Installation Prerequisites](#installation-prerequisites)
    * [Installing the Migration tool](#installing-the-migration-tool)
* [Help Commands](#help-commands)
* [Configuration](#configuration)
* [Showing Resources](#showing-resources)
* [Backing up Resource Connections, Routes and Connectors](#backing-up-resource-connections-routes-and-connectors)
    * [Backing up resource connections, routes and connectors](#backing-up-resource-connections-routes-and-connectors)
    * [Backing up resource routes only](#backing-up-resource-routes-only)
    * [Backing up resource connections only](#backing-up-resource-connections-only)
    * [Backing up resource connectors only](#backing-up-resource-connectors-only)
    * [Backing up resources using a different config file](#backing-up-resources-using-a-different-config-file)
 * [Migrating Resources](#migrating-resources)  
     * [Migrate resources of a specific Family and Model](#migrate-resources-of-a-specific-family-and-model)
     * [Migrate a list of resources](#migrate-a-list-of-resources)
     * [Migrate resources to existing resources](#migrate-resources-to-existing-resources)
     * [Migration options](#migration-options)
          * [Migrate resources using dry run](#migrate-resources-using-dry-run)
          * [Migrate resources using a different config file](#migrate-resources-using-a-different-config-file)
          * [Migrate resources from a backup file](#migrate-resources-from-a-backup-file)
          * [Migrate resources while overriding existing connections](#migrate-resources-while-overriding-existing-connections)
 * [Post Migration Operations](#post-migration-operations)
 * [Appendix Restoring Resource Mappings](#appendix-restoring-resource-mappings)
 * [Additional Restore options](#additional-restore-options)
  

# Introduction
In order to benefit from the capabilities of Quali’s upgraded shells, you must migrate your existing resources (based on the old shells) to new resources based on the new shells. The Migration tool automates the resource migration process, automatically mapping the physical connections in the new resources and updating active sandbox routes in the process.

Quali’s upgraded shells include certain enhancements, such as the following:

* Developing and extending shells is now easier
* New shells now support different operating system versions of a particular device. This reduces the need to continuously release new shells each time a shell is released with a new OS version. 
* New shells offer enhanced shell management and customization capabilities.

   **Notes:**
   * You can continue using your resources based on the old shells. However, you will not benefit from the capabilities of the new shells. 
   * Quali provides support for these older shells. However, bug fixing services are only provided for the new shell versions. 

## Workflow

1.	Create a list of the resources you want to migrate. See [Showing Resources](#showing-resources) to generate a list of the resources currently in CloudShell.
2.	Install the new shell versions. You do not need to create a resource from these shells.

    a.	Search the [Quali Community Integrations](https://community.quali.com/integrations) page for the new shells.
    
    b.	Import the shells into CloudShell. See [Importing Shells](https://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Shells.htm#Adding) in the CloudShell online help.
3.	Install the Migration tool. See [Installing the Migration tool](#installing-the-migration-tool).
4.	Configure the Migration tool. See [Configuration](#configuration).
5.	Back up the routes, connections and connectors of the resources you want to migrate. See [Backing up resource connections, routes and connectors](#backing-up-resource-connections-routes-and-connectors).
6.	Run the Migration tool. See [Migrating Resources](#migrating-resources). 
7.	If you are not satisfied with your results, you can restore the resource routes and connections to their state prior to the migration. See [Appendix Restoring Resource Mappings](#appendix-restoring-resource-mappings).<br><br>
The new resources are displayed in **Resource Manager Client’s Resource Explorer** with the prefix (“New_”). The migration process copies physical connections to the new resources. In active sandboxes, all existing routes are updated to use the new resources.
8.	Following a successful migration, you are advised to remove the old resources.

# Installation

## Installation Prerequisites

* CloudShell version 7.0 and above
* pip

## Installing the Migration tool

**To install the Migration tool via pip (PyPi):**

* Run the following command-line: 

   ```pip install cloudshell-migration```
   
# Help Commands

**To list the tool’s main commands:**

* Run the following command-line: 

   ```migration_tool --help```
   
   To use the tool, navigate to the folder in command-line.

   **Note:** It is recommended to add the python and pip installation folder paths to your local environment variables. For example, *C:\Python27 and C:\Python27\Scripts*. This will enable you to run the python/pip commands from any folder.

**To view the tool’s version number:**

* Run the following command-line: 

   ```migration_tool --version```
   
**To show detailed information for a main command:**

* Run the following command-line: 

   ```migration_tool <command> --help```
   
   Where **command** is the name of the main command.


# Configuration

**To configure the Migration tool:**

1. Configure your CloudShell credentials: 

   Run the following command-lines and replace your CS credentials within the <>. For example, replace **CSHost** with your CloudShell host, etc.: 
   
   ```
   migration_tool config host <CSHost>
   migration_tool config username <CSUserName>
   migration_tool config password <CSPassword>
   migration_tool config domain <CSDomain>
   migration_tool config port <CSPort>
   ```

2. Configure other elements of the tool:

   * **To view the tool’s current configuration, run the following command-line:**

      ```migration_tool config```
   
      After running this command, the following output (sample) is generated:
   
      ```username: admin
      domain: Global
      name_prefix: new_
      log_path: C:\Users\Administrator\AppData\Roaming\Quali\migration_tool\Logs
      log_level: INFO
      host: localhost
      backup_location: C:\Users\Administrator\AppData\Roaming\Quali\migration_tool\Backup
      password: ******
      port: 8029
      ```

   * **To specify the tool’s log path information:**

      Run the following command-line:

      ```migration_tool config log_path c:\<FOLDER_PATH>```

   * **To specify the tool’s log level information:**

      Run the following command-line:

      Specify either **DEBUG** to obtain the most detailed logging information or **INFO** for basic logging information. If you do not specify a value here, the default value **(INFO)** will be used. Logging information is displayed in the output in your Command Prompt window after running a command.

      ```migration_tool config log_level <DEBUG or INFO>```

   * **To change the backup file’s containing folder:**

      Run the following command-line:
   
      ```migration_tool config backup_location C:\<FOLDER_PATH>```
   
      The Migration tool automatically creates a new backup file each time you run a migration command, saving your existing connections and routes in the following default location: *C:\Users\<user>\AppData\Roaming\Quali\migration_tool\Backup*. The file is generated in yaml format.

   * **To change the prefix for your new migrated resources:**

      Run the following command-line:
   
      ```migration_tool config name_prefix "<New>_"```

      Replace **New** with the desired prefix. 

   * **To generate a custom config file based on the tool’s default configuration:**

      Run the following command-line:
   
      ```migration_tool config --config <FILE-PATH> <config command>```
   
      Replace **FILE-PATH** with the relative file path and name of the custom config file and **config command** with any command that updates a parameter in the config file. For example:

      ```migration_tool config --config test.conf name_prefix "test"```
   
      You now have a custom config file, based on the default configuration, in the location specified.

      The config file uses the “Yaml” format, however, any of the following file extensions can be used: .conf, .yaml, .or yml.

      This file can now be used later as needed. It is helpful if you have more than one configuration. You can specify this config file when running a command.

# Showing Resources

This command produces a list of all resources, which helps when you need to include the names of resources in other commands within the tool.

**To generate a list of all resources based on the default config file:**

* Run the following command-line: 

   ```migration_tool show```
    
**To generate a list of all resources that exist on the CloudShell server specified in a custom config file:**

* Run the following command-line: 

   ```migration_tool show --config <FILE-PATH>```
   
   Replace **FILE-PATH** with the relative file path and name of the custom config file you generated here: "To generate a custom config file based on the tool's default configuration". 
   
**To generate a list of all resources for a particular family:**

* Run the following command-line: 

   ```migration_tool show --family <TEXT>```
   
   Replace **TEXT** with the name of the family. If the family name contains spaces, place quotes around the name of the family, for example “L1 Switch”.
   
# Backing up Resource Connections, Routes and Connectors

This section explains how to back up resource connections, routes and connectors. If you are not happy with the results of your migration, you can use this file to restore connections, routes and connectors. 

By default, a backup file is saved in the folder you specified in the config file. For example:

*C:\Users\<Username>\AppData\Roaming\Quali\migration_tool\Backup\2018-12-12_01-19-39.yaml*

## Backing up resource connections, routes and connectors

**To back up resource connections, routes and connectors:**

1. Run the following command-line and include the name of your resource(s) you want to backup:

   ```migration_tool backup “RESOURCE1,RESOURCE2,etc.”```
   
   The names of the **Resources to backup** are presented in the command-line.
   
   [Optional] To change the path to the backup yaml file, add the file path as follows:
   
   ```migration_tool backup --backup-file [BACKUP FILE-PATH]” “RESOURCE1,RESOURCE2,etc.”```

2. Type “y” when the system asks you: Do you want to continue?

   The resource connections and routes are saved in the default location defined in the config file or in the location you specified here.

## Backing up resource routes only

**To back up resource routes only:**

* Run the following command-line: 

   ```migration_tool backup --routes “RESOURCE1,RESOURCE2,etc.”```
   
   [Optional] To change the path to the backup file, add the file-path as follows:

   ```migration_tool backup --backup-file [BACKUP FILE-PATH] --routes “RESOURCE1,RESOURCE2,etc.”```

## Backing up resource connections only

**To backup resource connections only:**

* Run the following command-line: 

   ```migration_tool backup --connections “RESOURCE1,RESOURCE2,etc.”```
   
   [Optional] To change the path to the backup file, add the path as follows:

   ```migration_tool backup --backup-file [BACKUP FILE-PATH] --connections “RESOURCE1,RESOURCE2,etc.”```

## Backing up resource connectors only

**To backup resource connections only:**

* Run the following command-line: 

   ```migration_tool backup --connectors “RESOURCE1,RESOURCE2,etc.”```
   
   [Optional] To change the path to the backup file, add the path as follows:

   ```migration_tool backup --backup-file [BACKUP FILE-PATH] --connectors “RESOURCE1,RESOURCE2,etc.”```


## Backing up resources using a different config file

**To back up resources from a config file other than the default config file:**

* Run the following command-line: 

   ```migration_tool backup --config [FILE-PATH] “RESOURCE1,RESOURCE2,etc.”```
   
   Where [FILE-PATH] is the full path to the config file.

# Migrating Resources

This section explains how to migrate resources. In order to run a migration process, you must specify the source resources (SRC) and the destination resources (DST).

**Notes:** 
* The migration process migrates only routes and mappings, not additional settings on the resource, like attributes and metadata.
* You do not need to specify the full path from the root of the desired resource(s). However, the tool will create the new resource(s) in the root.
 
## Migrate resources of a specific Family and Model

**To migrate resources of a specific Family and Model:**

* Run the following command-line: 

   ```migration_tool migrate "*/Old Family/Old Model" "*/New Family/New Model"```
   
   The default prefix (_new) or the prefix configured in: "To change the prefix for your new migrated resources" will be used to create new resources containing the prefix in their names. For example, if you have an old resource named “TestL1Shell”, which relates to Old Family/Old Model, a new resource will be created named “new_TestL1Shell” under the New Family/New Model.

## Migrate a list of resources

**To migrate a list of resources:**

* Run the following command-line with the name of each resource: 

   ```migration_tool migrate "L1 Switch1,L1 Switch2" "*/New Family/New Model"```
   
   Provide the name of each resource that you want to migrate.

## Migrate resources to existing resources

**To migrate resources to existing resources:**

* Run the following command-line: 

   ```migration_tool migrate "L1 Switch1,L1 Switch2" "New Switch1,New Switch2"```
   
   This command migrates the old resources to the new resources, if you already created the new resources in **Resource Manager Client**. If you do not have new resources, the migration process will create new resources with the names you provided.
   
## Migration options

### Migrate resources using dry run

Running the migrate command as a dry run creates new resources but does not switch the physical connections or create or remove active routes. Instead, it lists the actions to be performed, allowing the user to check these actions and decide if to proceed with the migration. You can add this option to any of the migrate commands.

**To migrate resources using dry-run:**

1. Run the following command-line:

   ```migration_tool migrate --dry-run SRC_RESOURCES DST_RESOURCES```
   
   A list of actions to be taken on active routes and connections is displayed, such as remove, update or create.
   
2. Answer “y” to the question: Do you want to continue?

   The connections and active routes are migrated to the new resources. 
   
### Migrate resources using a different config file

**To migrate resources using a config file (other than default):**

* Run the following command-line: 

   ```migration_tool migrate --config <FILE-PATH> SRC_RESOURCES DST_RESOURCES```
   
   Where **FILE-PATH** is the relative file-path and name of the config file you created in "To generate a custom config file based on the tool's default configuration".
   
### Migrate resources from a backup file

**To migrate resources from a backup file:**

* Run the following command-line: 

   ```migration_tool migrate --backup-file [BACKUP FILE-PATH] SRC_RESOURCES DST_RESOURCES```
   
   Where [BACKUP FILE-PATH] is the full path to the backup file.
   
### Migrate resources while overriding existing connections

Add the ‘override’ tag if you want the port connections on your source resource to override any existing port connections on your destination resource. In other words, if a port on your destination resource is being used for any other connection, this command will override these connections. Without this tag, the process will add new connections and routes, and ignore existing ones. 

**To migrate resources while existing port connections (if they exist):**

* Run the following command-line: 

   ```migration_tool migrate --override SRC_RESOURCES DST_RESOURCES```
   
# Post Migration Operations

This section explains the steps you should take after completing the migration process.

1. Move the new resources to their rightful place in the folder hierarchy.
2. Test the new resources to ensure that they were migrated successfully.
3. Delete the old ones (or exclude them if you want to keep them for reference purposes). 

   If you are not happy with the migration, you can always restore from a config file, see [Appendix Restoring  Resource Mappings](#appendix-restoring-resource-mappings).
   
# Appendix Restoring Resource Mappings

This section explains how to restore resource connections and routes after running the migration from a backup file if you are not satisfied with the migration.

**Restoring from a backup file:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH]```
   
   Where [BACKUP FILE-PATH] is the full path to the backup file.

**Restoring a specific resource from a backup file:** 

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH] "L1 Switch1 X"```

   Where [BACKUP FILE-PATH] is the full path to the backup file, and L1 Switch X is the name of the switch.

**Restoring a specific resource connections from a backup file:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH] "L1 Switch X" --connections```

   Where [BACKUP FILE-PATH] is the full path to the backup file, and L1 Switch X is the name of the switch.

**Restoring a specific resource routes from a backup file:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH] "L1 Switch X" --routes```

   Where [BACKUP FILE-PATH] is the full path to the backup file, and L1 Switch X is the name of the switch.
   
## Additional Restore options

**Restore as a dry run:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH] "L1 Switch X” --dry-run```
   
   **Note:** For additional information about dry-runs, see [Migrate resources using dry run](#migrate-resources-using-dry-run).

**Restore using a custom config file:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUPFILE-PATH] [Resources] --config [FILE-PATH]```
   
**Restore while override existing routes and connections:**

* Run the following command-line: 

   ```migration_tool restore --backup-file [BACKUP FILE-PATH] --override```
 
