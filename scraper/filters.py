"""Filter functions for spiders.

This module contains functions that can be applied to the <body> of a story to
modify it. The body element will be passed to the filter function as the first
argument. Some filters have optional keyword arguments that may be configured
by setting the arguments with `functools.partial()`. Custom filters may also
be written and used in a spider.

Example usage:

    from . import Spider, filters

    def my_filter(root):
        pass

    class MySpider(Spider):
        filters = (my_filter, filters.kill_classes, *filters.DEFAULT_FILTERS)


Always ensure that `DEFAULT_FILTERS` are included in the filter list, unless
you are very sure you want to override them.
"""

import re

from lxml.html import clean, builder as E


# TODO: add filter to move attributes from <p> tags onto a <div> for Pandoc

# TODO: add configurable filter to remove tags by class name

# TODO: add filter to ensure ids are unique throughout the document

# TODO: add lower_heading_levels filter. Will be manually run.
# Set a max output heading level.
# Attempt to autodetect the document's heading levels.


class Cleaner(clean.Cleaner):
    """Cleaner to remove unnecessary tags and attributes.

    Currently removes <div> and <span> tags preserving their children.
    All attributes except what lxml considers to be "safe" are removed.
    Additionally the attributes `width`, `height`, `dir` and `align` are
    removed.

    Instances of this class are usable as a filter.
    """
    remove_tags = ('div', 'span')
    safe_attrs = clean.Cleaner.safe_attrs - {'width', 'height', 'align', 'dir'}


def kill_classes(root, classes=('reaction_buttons', 'sharedaddy')):
    """Filter to remove tags with unwanted classes.

    If any tag has one of the specified classes, it and it's children will be
    removed. By default this filter removes classes that match divs at the
    end of blog posts with social media sharing buttons.
    """

    for c in classes:
        for e in root.find_class(c):
            e.drop_tree()


# TODO: add stylesheet that includes alignment classes
def text_alignment(root, directions=None):
    """Convert inline styles and align attributes for text alignment to
    a class.

    This is needed because inline styles are stripped by default. Currently
    `text-align: justified` isn't handled, only left, center and right are.

    It may be a good idea to remove left from the set of handled alignments.
    Then the document's default alignment, which may be justified, can be
    applied.
    """

    if not directions:
        directions = {
            'left': 'align-left',
            'right': 'align-right',
            'center': 'align-center'}

    for e in root.xpath('.//*[@style]'):
        style = e.get('style')
        for direction, css_class in directions.items():
            if re.search(r'text-align:\s*'+direction, style, re.I):
                e.classes.add(css_class)

    for e in root.xpath('.//*[@align]'):
        align = e.get('align')
        for direction, css_class in directions.items():
            if direction == align.lower():
                e.classes.add(css_class)
                del e.attrib['align']


# TODO: add stylesheet that includes alignment classes
def text_decoration(root, decorations=None):
    """Convert `text-decoration: underline` in style attributes to
    a class."""

    if not decorations:
        decorations = {'underline': 'underlined'}

    for e in root.xpath(r'.//*[@style]'):
        style = e.get('style')
        for decoration, css_class in decorations.items():
            if re.search(r'text-decoration:\s*'+decoration, style, re.I):
                e.classes.add(css_class)


def move_attrs_to_div(root, elements=('p',)):
    """If an element has attributes move them to a <div> wrapping it.

    Pandoc doesn't support attributes on all types of elements. Notably it
    does not support attributes on <p> tags. This filter moves all the
    attributes off of the specified element types onto a <div> wrapping the
    element.
    """

    # FIXME: the behavior of iter() is undefined if the tree is modified
    # during iteration. But this seems to work for now.
    for e in root.iter(*elements):
        if e.attrib:
            wrapper = E.DIV(dict(e.attrib))
            e.attrib.clear()
            e.addprevious(wrapper)
            wrapper.insert(0, e)

            # The styles, etc shouldn't affect the tail text of the element
            # FIXME: fix handling of tail
            e.tail = e.tail.strip()
            if e.tail:
                raise Exception('FIXME: non-empty tail found')


DEFAULT_FILTERS = (text_decoration, Cleaner(), move_attrs_to_div)
