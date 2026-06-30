"""项目级大模型配置领域错误。"""


class ModelConfigNotFoundError(Exception):
    """指定项目中不存在模型配置。"""


class ModelConfigInUseError(Exception):
    """模型配置仍被项目默认用途引用。"""


class ModelConfigNameConflictError(Exception):
    """项目内已存在同名模型配置。"""


class ModelDefaultMissingError(Exception):
    """项目尚未配置指定用途的默认模型。"""
