from cloudshell.migration.association.model.entities import AssociationConfig
from cloudshell.migration.exceptions import AssociationException


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
            AssociationConfigTableParser.validate(config_item)
            result.append(config_item)
        return result

    @staticmethod
    def validate(config_item):
        """
        :param cloudshell.migration.association.model.entities.AssociationConfig config_item:
        """

        if not config_item.family or not config_item.address_pattern and not config_item.name:
            raise AssociationException("{} is not valid.".format(config_item))
