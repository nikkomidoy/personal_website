import datetime

from django.core.management.base import BaseCommand
from wagtail.models import Site

from blog.models import BlogIndexPage, BlogPage
from core.models import SiteProfile
from home.models import Education, Experience, HomePage, Skill, StandardPage
from portfolio.models import ProjectIndexPage, ProjectPage


class Command(BaseCommand):
    help = "Fill a fresh database with placeholder career content so you can see the site's layout."

    def handle(self, *args, **options):
        home = HomePage.objects.get(depth=2)
        if home.experiences.exists():
            self.stdout.write("Demo content already present; nothing to do.")
            return

        site = Site.objects.get(is_default_site=True)
        profile = SiteProfile.for_site(site)
        profile.full_name = "Alex Example"
        profile.job_title = "Senior Software Engineer"
        profile.location = "Remote"
        profile.email = "alex@example.com"
        profile.github_url = "https://github.com/"
        profile.linkedin_url = "https://www.linkedin.com/"
        profile.save()

        home.headline = "I build reliable web platforms and the teams behind them."
        home.summary = "<p>Ten years shipping Python and cloud systems, from early-stage startups to scale-ups.</p>"
        home.save_revision().publish()

        Experience.objects.bulk_create(
            [
                Experience(
                    page=home,
                    sort_order=0,
                    role="Senior Software Engineer",
                    company="Northwind",
                    start_date=datetime.date(2022, 3, 1),
                    description="<ul><li>Led the move to AWS ECS.</li><li>Mentored five engineers.</li></ul>",
                ),
                Experience(
                    page=home,
                    sort_order=1,
                    role="Software Engineer",
                    company="Contoso",
                    start_date=datetime.date(2018, 6, 1),
                    end_date=datetime.date(2022, 2, 1),
                    description="<p>Built the customer-facing Django platform.</p>",
                ),
            ]
        )
        Education.objects.create(
            page=home,
            institution="State University",
            qualification="BSc Computer Science",
            start_year=2014,
            end_year=2018,
        )
        for i, (name, category) in enumerate(
            [
                ("Python", "Languages"),
                ("TypeScript", "Languages"),
                ("Django", "Frameworks"),
                ("Wagtail", "Frameworks"),
                ("AWS", "Cloud"),
                ("Terraform", "Cloud"),
            ]
        ):
            Skill.objects.create(page=home, sort_order=i, name=name, category=category)

        about = home.add_child(
            instance=StandardPage(title="About", slug="about", show_in_menus=True, intro="A little more about me.")
        )
        projects = home.add_child(instance=ProjectIndexPage(title="Projects", slug="projects", show_in_menus=True))
        projects.add_child(
            instance=ProjectPage(
                title="This website",
                slug="this-website",
                summary="A Wagtail CMS deployed to AWS with GitHub Actions.",
                technologies="Django, Wagtail, AWS ECS, GitHub Actions",
                featured=True,
            )
        )
        blog = home.add_child(instance=BlogIndexPage(title="Writing", slug="writing", show_in_menus=True))
        blog.add_child(instance=BlogPage(title="Hello, world", slug="hello-world", intro="Why I built this site."))
        about.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("Demo content created."))
