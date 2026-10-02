from django import template
from wagtail.models import Site

register = template.Library()


@register.simple_tag(takes_context=True)
def get_site_root(context):
    return Site.find_for_request(context["request"]).root_page


@register.simple_tag
def menu_items(root):
    """Top-level pages ticked 'Show in menus' in the CMS."""
    return root.get_children().live().in_menu() if root else []
