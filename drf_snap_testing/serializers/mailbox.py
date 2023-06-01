from drf_yaml.fields import LiteralCharField
from drf_yaml.styles import literal_str
from rest_framework import serializers

from .base import ReadOnlySerializer


class MailAttachmentSerializer(ReadOnlySerializer):
    filename = serializers.SerializerMethodField(source="*")
    mimetype = serializers.SerializerMethodField(source="*")
    content = serializers.SerializerMethodField(source="*")

    def get_filename(self, attachment: tuple[str, str, str]) -> str:
        return attachment[0]

    def get_content(self, attachment: tuple[str, str, str]) -> str:
        return literal_str(attachment[1])

    def get_mimetype(self, attachment: tuple[str, str, str]) -> str:
        return attachment[2]


class MailAlternativeSerializer(ReadOnlySerializer):
    mimetype = serializers.SerializerMethodField(source="*")
    content = serializers.SerializerMethodField(source="*")

    def get_content(self, alternative: tuple[str, str]) -> str:
        return literal_str(alternative[0])

    def get_mimetype(self, alternative: tuple[str, str]) -> str:
        return alternative[1]


class MailboxSerializer(ReadOnlySerializer):
    from_email = serializers.EmailField(required=False)
    to = serializers.ListField(child=serializers.EmailField())
    cc = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc = serializers.ListField(child=serializers.EmailField(), required=False)
    reply_to = serializers.EmailField(required=False)
    subject = serializers.CharField()
    body = LiteralCharField()
    extra_headers = serializers.DictField(required=False)
    attachments = serializers.ListField(
        child=MailAttachmentSerializer(), required=False
    )
    alternatives = serializers.ListField(
        child=MailAlternativeSerializer(), required=False
    )
