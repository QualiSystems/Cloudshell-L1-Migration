class AssociationConfigHelper(object):
    MATCH_ALL = '*'

    @staticmethod
    def _match_to_list(value, compare_list):
        if not compare_list or AssociationConfigHelper.MATCH_ALL in compare_list or value in compare_list:
            return True
        return False

    @staticmethod
    def match_to_item_config(instance, item_conf):
        """
        :param cloudshell.migration.core.model.entities.AssociateItem instance:
        :param cloudshell.migration.association.model.AssociationConfig item_conf:
        :return:
        """
        if AssociationConfigHelper._match_to_list(instance.family,
                                                  item_conf.family) and AssociationConfigHelper._match_to_list(
                instance.model, item_conf.model):
            return True
        return False
