from typing import List

from exceptions import DatabaseQueryError


def fetch_from_model(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise DatabaseQueryError(f"{model.__name__} not found for {kwargs}")


def sort_versions(version_keys: List[str]) -> List[str]:
    return sorted(
        version_keys, key=lambda x: [int(i) for i in x.lstrip("v").split(".")]
    )
