from cloudshell.migration.association.model import AssociationItemConfig


class AssociationTableParser(object):

    @staticmethod
    def convert_to_resource_config_model(raw_config):
        """
        :param dict raw_config:
        :return:
        """
        result_table = {}
        for item, conf in raw_config.items():
            config_item = AssociationItemConfig(item, **conf)
            result_table[item] = config_item
