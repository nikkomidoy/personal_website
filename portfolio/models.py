from django.db import models
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from core.blocks import BodyStreamBlock


class ProjectIndexPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["portfolio.ProjectPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["projects"] = ProjectPage.objects.child_of(self).live().order_by("-featured", "-completed_on")
        return context


class ProjectPage(Page):
    summary = models.CharField(max_length=300, blank=True)
    image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    technologies = models.CharField(max_length=255, blank=True, help_text="Comma-separated, e.g. 'Django, AWS, React'.")
    project_url = models.URLField(blank=True)
    repository_url = models.URLField(blank=True)
    completed_on = models.DateField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    body = StreamField(BodyStreamBlock(), blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("image"),
        MultiFieldPanel(
            [
                FieldPanel("technologies"),
                FieldRowPanel([FieldPanel("project_url"), FieldPanel("repository_url")]),
                FieldRowPanel([FieldPanel("completed_on"), FieldPanel("featured")]),
            ],
            "Details",
        ),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [index.SearchField("summary"), index.SearchField("technologies")]
    parent_page_types = ["portfolio.ProjectIndexPage"]
    subpage_types = []

    @property
    def technology_list(self):
        return [t.strip() for t in self.technologies.split(",") if t.strip()]
