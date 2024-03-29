# ruff: noqa: D100,D101,D105,D106

from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.styles import get_all_styles

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted([(item, item) for item in get_all_styles()])

User = get_user_model()


class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default="")
    code = models.TextField()
    linenos = models.BooleanField(default=False)
    language = models.CharField(
        choices=LANGUAGE_CHOICES,
        default="python",
        max_length=100,
    )
    style = models.CharField(choices=STYLE_CHOICES, default="friendly", max_length=100)
    owner = models.ForeignKey(User, related_name="snippets", on_delete=models.CASCADE)
    highlighted = models.TextField()

    class Meta:
        ordering = ["created"]

    def __str__(self) -> str:
        return f"[Snippet] {self.title} ({self.language})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the default save method to create a highlighted HTML.

        Use the `pygments` library to create a highlighted HTML
        representation of the code snippet.
        """
        lexer = get_lexer_by_name(self.language)
        linenos = "table" if self.linenos else False
        options: Any = {"title": self.title} if self.title else {}
        formatter = HtmlFormatter(
            style=self.style,
            linenos=linenos,
            full=True,
            **options,
        )
        self.highlighted = highlight(self.code, lexer, formatter)
        super().save(*args, **kwargs)
