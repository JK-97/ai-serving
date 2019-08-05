from .handler.api_v1.alpha import handler as v1alpha

url_patterns = [
    (r'/api/v1alpha/detect', v1alpha.DetectHandler),
    (r'/api/v1alpha/switch', v1alpha.SwitchModelHandler),
]
