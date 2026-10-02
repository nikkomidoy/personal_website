from itertools import groupby

from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from core.blocks import BodyStreamBlock


class HomePage(Page):
    """Landing page: introduction, work history, education and skills."""

    headline = models.CharField(max_length=255, blank=True, help_text="e.g. 'Senior Software Engineer building…'")
    summary = RichTextField(blank=True, features=["bold", "italic", "link"])
    profile_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    body = StreamField(BodyStreamBlock(), blank=True, help_text="Extra sections shown below your career history.")

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("headline"), FieldPanel("summary"), FieldPanel("profile_image")], "Introduction"),
        InlinePanel("experiences", heading="Work experience", label="Role"),
        InlinePanel("education_entries", heading="Education", label="Education"),
        InlinePanel("skills", heading="Skills", label="Skill"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [index.SearchField("headline"), index.SearchField("summary")]

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["home.StandardPage", "blog.BlogIndexPage", "portfolio.ProjectIndexPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        skills = self.skills.order_by("category", "sort_order")
        context["skill_groups"] = [
            (category or "Skills", list(items)) for category, items in groupby(skills, lambda s: s.category)
        ]
        return context


class Experience(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="experiences")
    role = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    company_url = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave empty if this is your current role.")
    description = RichTextField(blank=True, features=["bold", "italic", "link", "ul", "ol"])

    panels = [
        FieldRowPanel([FieldPanel("role"), FieldPanel("company")]),
        FieldRowPanel([FieldPanel("company_url"), FieldPanel("location")]),
        FieldRowPanel([FieldPanel("start_date"), FieldPanel("end_date")]),
        FieldPanel("description"),
    ]

    @property
    def is_current(self):
        return self.end_date is None

    def __str__(self):
        return f"{self.role} at {self.company}"


class Education(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="education_entries")
    institution = models.CharField(max_length=255)
    qualification = models.CharField(max_length=255, help_text="e.g. 'BSc Computer Science'")
    start_year = models.PositiveSmallIntegerField(null=True, blank=True)
    end_year = models.PositiveSmallIntegerField(null=True, blank=True)
    description = RichTextField(blank=True, features=["bold", "italic", "link"])

    panels = [
        FieldRowPanel([FieldPanel("qualification"), FieldPanel("institution")]),
        FieldRowPanel([FieldPanel("start_year"), FieldPanel("end_year")]),
        FieldPanel("description"),
    ]

    def __str__(self):
        return f"{self.qualification}, {self.institution}"


class Skill(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=100, blank=True, help_text="Skills are grouped by category, e.g. 'Languages'."
    )

    panels = [FieldRowPanel([FieldPanel("name"), FieldPanel("category")])]

    def __str__(self):
        return self.name


class StandardPage(Page):
    """General-purpose page, e.g. About, Contact, Speaking."""

    intro = models.TextField(blank=True)
    body = StreamField(BodyStreamBlock(), blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    search_fields = Page.search_fields + [index.SearchField("intro"), index.SearchField("body")]
