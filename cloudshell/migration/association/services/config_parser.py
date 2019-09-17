from cloudshell.migration.association.model.entities import AssociationConfig


class AssociationConfigTableParser(object):

    @staticmethod
    def convert_to_resource_config_model(raw_config):
        """
        :param dict raw_config:
        :return:
        """
        result = []
        for item, conf in raw_config.items():
            config_item = AssociationConfig(item, **conf)
            result.append(config_item)
        return result
