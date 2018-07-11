class MigrationOperation(object):
    def __init__(self, old_resource, new_resource, migration_config):
        """
        :type old_resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        :type new_resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        :type migration_config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        """
        self.old_resource = old_resource
        self.new_resource = new_resource
        self.migration_config = migration_config
        self.valid = False
        self.success = False

    def __str__(self):
        return '{0}->{1}'.format(str(self.old_resource), str(self.new_resource))

    def __repr__(self):
        return self.__str__()
