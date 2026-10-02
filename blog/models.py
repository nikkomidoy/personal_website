from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from core.blocks import BodyStreamBlock


class BlogIndexPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["posts"] = BlogPage.objects.child_of(self).live().order_by("-date")
        return context


class BlogPage(Page):
    date = models.DateField("Post date", default=timezone.localdate)
    intro = models.CharField(max_length=300, blank=True)
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    body = StreamField(BodyStreamBlock(), blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("cover_image"),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [index.SearchField("intro"), index.SearchField("body")]
    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []
