import re

from lxml.html import clean, builder as E
from .. import Spider, filters

# Remove some wordpress tags and attributes
# TODO: is removing <a> needed?
class Cleaner(clean.Cleaner):
    remove_tags = ('a', 'table', 'tbody', 'tr', 'td')
    safe_attrs = clean.Cleaner.safe_attrs - {'class'}


# TODO: write generic filter to convert dashes to <hr> tags
# TODO: set story summary
# TODO: Stories use a mix of <h1> and <h2> tags for headings
# TODO: Link to chapter is in a <h3> and isn't dropped
# TODO: Some stories put the chapter links in a table that goes down (not across) and the chapters are out of order


def scene_breaks(root):
    for e in root:
        if re.match(r'(\s*[—–-]+\s*)+', e.text_content()):
            e.addprevious(E.HR(E.CLASS('scene-break')))
            e.drop_tree()


class Keiramarcos(Spider):
    name = 'Keira Marcos fanfiction'
    domain = 'keiramarcos.com'
    url = 'http://keiramarcos.com/fan-fiction/harry-potter-the-soulmate-bond/'
    filters = (filters.kill_classes, Cleaner(), scene_breaks, *filters.DEFAULT_FILTERS)

    def parse(self, url):
        doc = self.fetch(url)
        title, = doc.xpath('//meta[@property="og:title"]/@content')
        self.metadata['title'] = title.strip()
        self.metadata['author'] = 'Keira Markos'

        content, = doc.find_class('entry-content')
        index_div = content.find_class('wordpress-post-tabs')
        chapter_links = content.xpath('.//a[contains(text(), "Chapter")]')

        if index_div:
            # Tabs

            # FIXME: a couple stories actually put the whole text of the story
            # in wordpress-post-tabs, not just links to chapters
            chapter_links = index_div[0].xpath('.//div[starts-with(@id, "tabs-")][1]//a')

            # Drop the entire tags <div>
            index_div[0].drop_tree()
        elif chapter_links:
            # Links to chapters

            for link in chapter_links:
                # This also kills the tail text, but that is actually desirable
                link.getparent().remove(link)
        else:
            # Single chapter story

            yield from self._parse_chapter(url, strip_authors_note=False)
            return

        yield from content

        for link in chapter_links:
            yield E.H1(link.text_content())
            yield from self._parse_chapter(link.get('href'))

    def _parse_chapter(self, url, strip_authors_note=True):
        self.info(f'Parsing chapter: %s', url)
        doc = self.fetch(url)

        content, = doc.find_class('entry-content')

        # Remove author's note, etc
        if strip_authors_note:
            first_tag = content[0]
            if 'Title:' in first_tag.text_content():
                content[0].drop_tree()

        # Remove link to next chapter (any link in last paragraph)
        last_link = content.xpath('*[last()]/a')
        if last_link:
            last_link[0].drop_tree()

        # Find any other links back to the series index
        # This catches some links after "The End" sometimes
        other_link = content.xpath('*//a[starts-with(@href, "http://keiramarcos.com/fan-fiction")]')
        if other_link:
            other_link[0].drop_tree()

        yield from content
