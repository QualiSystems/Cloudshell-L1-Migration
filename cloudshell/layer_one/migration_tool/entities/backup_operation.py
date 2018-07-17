class BackupOperation(object):
    def __init__(self, resource, backup_config):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self.resource = resource
        self.backup_config = backup_config
        self.valid = False
        self.success = False

    def __str__(self):
        return self.resource

    def __repr__(self):
        return self.__str__()
