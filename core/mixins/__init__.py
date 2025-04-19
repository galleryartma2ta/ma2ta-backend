# core/mixins/__init__.py

from core.mixins.models import (
    TimeStampedMixin,
    SlugMixin,
    PublishableMixin,
    ViewCountMixin,
    SoftDeleteMixin,
    OrderableMixin,
    TranslatableMixin
)

from core.mixins.views import (
    PermissionRequiredMixin,
    ArtistRequiredMixin,
    OwnershipRequiredMixin,
    AjaxResponseMixin,
    LoggingMixin,
    CacheMixin
)

from core.mixins.serializers import (
    DynamicFieldsMixin,
    HyperlinkedModelSerializerMixin,
    ReadWriteSerializerMixin,
    TranslationMixin
)

__all__ = [
    # Model mixins
    'TimeStampedMixin',
    'SlugMixin',
    'PublishableMixin',
    'ViewCountMixin',
    'SoftDeleteMixin',
    'OrderableMixin',
    'TranslatableMixin',

    # View mixins
    'PermissionRequiredMixin',
    'ArtistRequiredMixin',
    'OwnershipRequiredMixin',
    'AjaxResponseMixin',
    'LoggingMixin',
    'CacheMixin',

    # Serializer mixins
    'DynamicFieldsMixin',
    'HyperlinkedModelSerializerMixin',
    'ReadWriteSerializerMixin',
    'TranslationMixin',
]