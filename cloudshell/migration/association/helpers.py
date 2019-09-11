class AssociationItemConfigHelper(object):
    MATCH_ALL = '*'

    @staticmethod
    def _match_to_list(value, compare_list):
        if not compare_list or AssociationItemConfigHelper.MATCH_ALL in compare_list or value in compare_list:
            return True
        return False

    @staticmethod
    def match_to_item_config(instance, item_conf):
        """
        :param cloudshell.migration.core.model.entities.AssociativeItem instance:
        :param cloudshell.migration.association.model.AssociationItemConfig item_conf:
        :return:
        """
        if AssociationItemConfigHelper._match_to_list(instance.family,
                                                      item_conf.family) and AssociationItemConfigHelper._match_to_list(
                instance.model, item_conf.model):
            return True
        return False
