from ..bit import Bit
from ..serializers import MailboxSerializer


class Mailbox(Bit):
    """
    A bit for Django's mail outbox.

    This bit is useful for testing emails sent by Django.
    It takes the value of django.core.mail.outbox as the value.
    """

    serializer_class = MailboxSerializer
    many = True
