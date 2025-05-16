from decouple import config

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": [config("ELASTIC_SEARCH_URL")],
        "http_auth": ("elastic", ""),
        "timeout": 30,
        "retry_on_timeout": True,
        "verify_certs": False,  # In production, you should use proper certificates
    },
}
# ELASTICSEARCH_DSL_AUTOSYNC = False
# ELASTICSEARCH_DSL_AUTO_REFRESH = False
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = (
    "src.apps.elastic_search.custom_signal_processor.CustomCelerySignalProcessor"
)
