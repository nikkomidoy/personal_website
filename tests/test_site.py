import datetime

import pytest
from django.test import override_settings
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from blog.models import BlogIndexPage, BlogPage
from home.models import Experience, HomePage, Skill, StandardPage
from portfolio.models import ProjectIndexPage, ProjectPage


@pytest.fixture
def home():
    return HomePage.objects.get(slug="home")


@pytest.mark.django_db
def test_homepage_created_by_migration(home):
    assert Site.objects.get(is_default_site=True).root_page.specific == home


@pytest.mark.django_db
def test_homepage_renders_career_history(client, home):
    Experience.objects.create(page=home, role="Engineer", company="Acme", start_date=datetime.date(2020, 1, 1))
    Skill.objects.create(page=home, name="Django", category="Frameworks")

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Engineer" in content and "Acme" in content and "Present" in content
    assert "Frameworks" in content and "Django" in content


@pytest.mark.django_db
def test_blog_and_portfolio_pages_render(client, home):
    blog = home.add_child(instance=BlogIndexPage(title="Blog", slug="blog"))
    blog.add_child(instance=BlogPage(title="First post", slug="first-post", intro="Hello"))
    projects = home.add_child(instance=ProjectIndexPage(title="Projects", slug="projects"))
    projects.add_child(instance=ProjectPage(title="Career site", slug="career-site", technologies="Django, AWS"))
    home.add_child(instance=StandardPage(title="About", slug="about"))

    for url, expected in [
        ("/blog/", "First post"),
        ("/blog/first-post/", "Hello"),
        ("/projects/", "Career site"),
        ("/projects/career-site/", "AWS"),
        ("/about/", "About"),
    ]:
        response = client.get(url)
        assert response.status_code == 200, url
        assert expected in response.content.decode(), url


@override_settings(ALLOWED_HOSTS=["example.com"], SECURE_SSL_REDIRECT=True)
def test_health_check_bypasses_host_validation_and_ssl_redirect(client):
    response = client.get("/health/", HTTP_HOST="10.0.1.23")
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_sitemap(client):
    assert client.get("/sitemap.xml").status_code == 200


class TestPageHierarchy(WagtailPageTestCase):
    def test_allowed_children(self):
        self.assertAllowedSubpageTypes(HomePage, {StandardPage, BlogIndexPage, ProjectIndexPage})
        self.assertAllowedSubpageTypes(BlogIndexPage, {BlogPage})
        self.assertAllowedSubpageTypes(ProjectIndexPage, {ProjectPage})

    def test_only_one_homepage(self):
        assert not HomePage.can_create_at(Page.get_first_root_node())
