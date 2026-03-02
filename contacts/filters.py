import django_filters
from .models import Contact


class ContactFilter(django_filters.FilterSet):
    """
    Filters for Contact API endpoints
    """

    # Text search
    name = django_filters.CharFilter(method='filter_by_name')

    # Followers range
    min_followers = django_filters.NumberFilter(
        field_name='followers_count',
        lookup_expr='gte'
    )
    max_followers = django_filters.NumberFilter(
        field_name='followers_count',
        lookup_expr='lte'
    )

    # Date filters
    added_after = django_filters.DateFilter(
        field_name='date_added',
        lookup_expr='date__gte'
    )
    added_before = django_filters.DateFilter(
        field_name='date_added',
        lookup_expr='date__lte'
    )

    class Meta:
        model = Contact
        fields = [
            'category',
            'age_category',
            'country',
            'social_media_platform',
            'whatsapp_message_sent',
            'synced_to_drive',
        ]

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            first_name__icontains=value
        ) | queryset.filter(
            surname__icontains=value
        )
