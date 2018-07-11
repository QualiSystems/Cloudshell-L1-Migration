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
        return 'Migrate resource: {0} ({1})'.format(operation,
                                                    'Operation Valid' if operation.valid else 'Operation Invalid')

    @staticmethod
    def format_logical_routes(logical_routes):
        return '\n'.join(
            [OutputFormatter._logical_route_info(logical_route) for logical_route in logical_routes])

    @staticmethod
    def _logical_route_info(logical_route):
        return 'Logical route: {}'.format(logical_route)
