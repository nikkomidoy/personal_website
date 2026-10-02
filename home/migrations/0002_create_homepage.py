from django.db import migrations


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    HomePage = apps.get_model("home.HomePage")
    Locale = apps.get_model("wagtailcore.Locale")

    # Remove Wagtail's default "Welcome" page.
    Page.objects.filter(depth=2, slug="home").delete()

    content_type, _ = ContentType.objects.get_or_create(model="homepage", app_label="home")
    homepage = HomePage.objects.create(
        title="Home",
        draft_title="Home",
        slug="home",
        content_type=content_type,
        locale=Locale.objects.order_by("pk").first(),
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        headline="Hello — welcome to my corner of the internet.",
    )
    Site.objects.update_or_create(is_default_site=True, defaults={"hostname": "localhost", "root_page": homepage})


def remove_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    HomePage = apps.get_model("home.HomePage")
    HomePage.objects.filter(slug="home", depth=2).delete()
    ContentType.objects.filter(model="homepage", app_label="home").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0001_initial"),
        ("wagtailcore", "0094_alter_page_locale"),
    ]

    operations = [migrations.RunPython(create_homepage, remove_homepage)]
