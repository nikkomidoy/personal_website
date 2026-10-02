from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting(icon="user")
class SiteProfile(BaseSiteSetting):
    """Who you are — shown in the header, footer and contact links on every page.

    Edit in the CMS under Settings → Site profile.
    """

    full_name = models.CharField(max_length=120, default="Your Name")
    job_title = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField("LinkedIn URL", blank=True)
    github_url = models.URLField("GitHub URL", blank=True)
    website_url = models.URLField("Other website URL", blank=True)
    resume = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Downloadable CV / résumé (PDF).",
    )
    footer_text = models.CharField(max_length=255, blank=True)

    panels = [
        MultiFieldPanel([FieldPanel("full_name"), FieldPanel("job_title"), FieldPanel("location")], "Identity"),
        MultiFieldPanel(
            [FieldPanel("email"), FieldPanel("linkedin_url"), FieldPanel("github_url"), FieldPanel("website_url")],
            "Contact & social",
        ),
        FieldPanel("resume"),
        FieldPanel("footer_text"),
    ]
