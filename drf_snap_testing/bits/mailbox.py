from ..bit import Bit
from ..serializers import MailboxSerializer


class Mailbox(Bit):
    serializer_class = MailboxSerializer
    many = True
