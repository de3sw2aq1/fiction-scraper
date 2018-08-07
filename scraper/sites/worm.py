"""A spider for the Worm serial.

Crawl https://parahumans.wordpress.com/ to use this spider.
"""

import re

from lxml.html import builder as E
from .. import Spider, filters


# TODO: add stylesheet to draw box for <hr>
def scene_breaks(root):
    for e in root:
        if e.text_content().strip() == '■':
            e.addprevious(E.HR(E.CLASS('scene-break')))
            e.drop_tree()


def blockquotes(root):
    for tag in root.xpath('.//*[@style]'):
        style = tag.get('style')

        # Convert padding to <blockquote>
        if re.search(r'padding-left:\s*30px', style, re.I):
            blockquote = E.BLOCKQUOTE()
            tag.addprevious(blockquote)
            blockquote.insert(0, tag)
            blockquote.tail = tag.tail
            tag.tail = None

        # Convert double padding to nested <blockquote> tags
        elif re.search(r'padding-left:\s*60px', style, re.I):
            nested_blockquote = E.BLOCKQUOTE()
            blockquote = E.BLOCKQUOTE(nested_blockquote)
            tag.addprevious(blockquote)
            nested_blockquote.insert(0, tag)
            blockquote.tail = tag.tail
            tag.tail = None


class Worm(Spider):
    domain = 'parahumans.wordpress.com'
    url = 'https://parahumans.wordpress.com/'
    filters = [scene_breaks, blockquotes, filters.kill_classes, *filters.DEFAULT_FILTERS]

    def parse(self, url):
        doc = self.fetch(self.url)

        self.metadata['title'] = 'Worm'
        self.metadata['author'] = 'Wildbow'

        categories = doc.get_element_by_id('categories-2')

        # Iterate over each arc <ul> in table of contents
        for arc in categories.xpath('.//ul[not(li/ul)]'):
            # Title is in previous <a>
            arc_title = arc.getprevious().text

            # Arc 10 has a leading soft hyphen, do some cleanup
            arc_title = arc_title.replace('\u00ad', '').strip()

            # Skip chapters that are included in Ward
            if arc_title == 'Stories (Pre-Worm 2)':
                continue

            yield E.H1(arc_title)

            for chapter in arc.iter('a'):
                yield from self._parse_chapter(chapter.get('href'))

    def _parse_chapter(self, url):
        doc = self.fetch(url)

        title, = doc.find_class('entry-title')
        yield E.H2(title.text_content)

        content, = doc.find_class('entry-content')

        # Remove next/previous chapter links
        # The only other link is an Urban Dictionary definition of "trigger warnings"
        for link in content.xpath('.//a'):
            if link.text_content().strip() in ('Last Chapter', 'Next Chapter', 'End'):
                # Remove parent <p> tag completely
                parent = link.getparent()
                if parent.getparent() is not None:
                    parent.drop_tree()

        yield from content
