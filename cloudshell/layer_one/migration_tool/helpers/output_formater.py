class OutputFormatter(object):
    @staticmethod
    def format_prepared_valid_operations(operations):
        return '\n'.join(
            [OutputFormatter._prepared_operation_output(operation) for operation in operations if operation.valid])

    @staticmethod
    def format_prepared_invalid_operations(operations):
        return '\n'.join(
            [OutputFormatter._prepared_operation_output(operation) for operation in operations if not operation.valid])

    @staticmethod
    def _prepared_operation_output(operation):
        """
        :type operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        return 'Operation: {0} ({1})'.format(operation, 'Valid' if operation.valid else 'Invalid')
