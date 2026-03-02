from rest_framework import serializers
from .models import Contact, ContactStats, AutomationLog


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model
    """

    full_name = serializers.CharField(read_only=True)
    days_since_added = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'surname',
            'full_name',
            'email',
            'whatsapp_contact',
            'category',
            'age_category',
            'country',
            'country_code',
            'social_media_platform',
            'social_media_handle',
            'followers_count',
            'school',
            'level',
            'notes',
            'whatsapp_message_sent',
            'synced_to_drive',
            'date_added',
            'days_since_added',
        ]
        read_only_fields = [
            'whatsapp_message_sent',
            'synced_to_drive',
            'date_added',
        ]


class ContactCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contacts
    (lighter, safer for POST requests)
    """

    class Meta:
        model = Contact
        fields = [
            'first_name',
            'surname',
            'email',
            'whatsapp_contact',
            'category',
            'age_category',
            'country',
            'country_code',
            'social_media_platform',
            'social_media_handle',
            'followers_count',
            'school',
            'level',
            'notes',
        ]


class ContactStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for daily statistics
    """

    class Meta:
        model = ContactStats
        fields = [
            'date',
            'total_contacts',
            'contacts_added_today',
        ]


class AutomationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for automation logs
    """

    contact_name = serializers.CharField(
        source='contact.full_name',
        read_only=True
    )

    class Meta:
        model = AutomationLog
        fields = [
            'id',
            'contact',
            'contact_name',
            'action_type',
            'status',
            'details',
            'timestamp',
        ]
        read_only_fields = ['timestamp']
