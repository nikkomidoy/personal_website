from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "blocks/image_block.html"


class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    attribution = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "blocks/quote_block.html"


class CallToActionBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False, help_text="Used when no page is selected.")

    class Meta:
        icon = "link"
        template = "blocks/cta_block.html"


class BodyStreamBlock(blocks.StreamBlock):
    """Flexible content used by most page types."""

    heading = blocks.CharBlock(form_classname="title", icon="title", template="blocks/heading_block.html")
    paragraph = blocks.RichTextBlock(icon="pilcrow")
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock(help_text="YouTube, Vimeo, SlideShare, etc.", icon="media")
    call_to_action = CallToActionBlock()
