"""自定义异常类"""


class RouteOptimizerError(Exception):
    """基础异常"""
    pass


class APIKeyError(RouteOptimizerError):
    """API Key 相关错误"""
    pass


class GeocodeError(RouteOptimizerError):
    """地理编码错误"""
    pass


class POISearchError(RouteOptimizerError):
    """POI 搜索错误"""
    pass


class DistanceError(RouteOptimizerError):
    """距离测量错误"""
    pass


class RouteError(RouteOptimizerError):
    """路线规划错误"""
    pass


class NetworkError(RouteOptimizerError):
    """网络请求错误"""
    pass


class InputError(RouteOptimizerError):
    """输入参数错误"""
    pass
