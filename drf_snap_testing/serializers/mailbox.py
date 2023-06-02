from django.core.mail import EmailMessage
from drf_yaml.fields import LiteralCharField
from drf_yaml.styles import LiteralStr
from rest_framework import serializers

from .base import ReadOnlySerializer


class MailAttachmentSerializer(ReadOnlySerializer[tuple[str, str, str]]):
    """
    A serializer for a mail attachment.

    Attachments are represented as a tuple of (filename, content, mimetype).
    What you see here is the result of that fun fact.
    """

    filename = serializers.SerializerMethodField(source="*")
    mimetype = serializers.SerializerMethodField(source="*")
    content = serializers.SerializerMethodField(source="*")

    def get_filename(self, attachment: tuple[str, str, str]) -> str:
        """Return the filename of the attachment."""
        return attachment[0]

    def get_content(self, attachment: tuple[str, str, str]) -> str:
        """Return the content of the attachment as a YAML literal str."""
        return LiteralStr(attachment[1])

    def get_mimetype(self, attachment: tuple[str, str, str]) -> str:
        """Return the mimetype of the attachment."""
        return attachment[2]


class MailAlternativeSerializer(ReadOnlySerializer[tuple[str, str]]):
    """
    A serializer for a mail alternative.

    Alternatives are represented as a tuple of (content, mimetype).
    What you see here is the result of that fun fact.
    """

    mimetype = serializers.SerializerMethodField(source="*")
    content = serializers.SerializerMethodField(source="*")

    def get_content(self, alternative: tuple[str, str]) -> str:
        """Return the content of the alternative as a YAML literal str."""
        return LiteralStr(alternative[0])

    def get_mimetype(self, alternative: tuple[str, str]) -> str:
        """Return the mimetype of the alternative."""
        return alternative[1]


class MailboxSerializer(ReadOnlySerializer[EmailMessage]):
    """A serializer for django.mail.outbox."""

    from_email = serializers.EmailField(required=False)
    to = serializers.ListField(child=serializers.EmailField())
    cc = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc = serializers.ListField(child=serializers.EmailField(), required=False)
    reply_to = serializers.EmailField(required=False)
    subject = serializers.CharField()
    body = LiteralCharField()
    extra_headers = serializers.DictField(required=False)
    attachments = serializers.ListField(
        child=MailAttachmentSerializer(),
        required=False,
    )
    alternatives = serializers.ListField(
        child=MailAlternativeSerializer(),
        required=False,
    )
