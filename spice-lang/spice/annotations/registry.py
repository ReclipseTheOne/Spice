"""Registry of compile-time annotation processors, keyed by name."""

from spice.annotations.base import AnnotationProcessor

_REGISTRY: dict[str, AnnotationProcessor] = {}


def register(cls):
    """Class decorator: instantiate the processor and register it by `name`."""
    instance = cls()
    if not getattr(instance, "name", ""):
        raise ValueError(f"Annotation processor {cls.__name__} must define a non-empty 'name'")
    if instance.name in _REGISTRY:
        raise ValueError(f"Duplicate annotation processor registered for '@!{instance.name}'")
    _REGISTRY[instance.name] = instance
    return cls


def get_processor(name: str):
    """Return the registered processor for `name`, or None."""
    return _REGISTRY.get(name)


def all_processors() -> dict:
    """A copy of the current registry."""
    return dict(_REGISTRY)
