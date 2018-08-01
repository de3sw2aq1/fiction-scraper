import sys
from lxml.html import clean, builder as E
from . import Spider

clean = clean.Cleaner(
    remove_tags=('div', 'span', 'a'),
    safe_attrs=clean.Cleaner.safe_attrs - {'class', 'width', 'height'}
)

# TODO: write generic filter to convert dashes to <hr>
# TODO: set story summary

class Keiramarcos(Spider):
    domain = 'keiramarcos.com'

    def parse(self):
        doc = self.fetch(self.url)
        title, = doc.xpath('//meta[@property="og:title"]/@content')
        self.metadata['title'] = title.strip()
        self.metadata['author'] = 'Keira Markos'

        content, = doc.find_class('entry-content')
        index_div = content.find_class('wordpress-post-tabs')
        chapter_links = content.xpath('.//a[contains(text(), "Chapter")]')

        if index_div:
            # FIXME: a couple stories actually put the whole text of the story
            # in wordpress-post-tabs, not just links
            chapter_links = index_div[0].xpath('.//div[starts-with(@id, "tabs-")][1]//a')
            content.remove(index_div[0])
        elif chapter_links:
            for link in chapter_links:
                # This also kills the tail text, but that is actually desirable
                link.getparent().remove(link)
        else:
            # This is a single chapter story
            yield from self._parse_chapter(self.url, strip_authors_note=False)
            return

        clean(content)
        yield from content.getchildren()

        for link in chapter_links:
            yield E.H1(link.text_content())
            yield from self._parse_chapter(link.get('href'))

    def _parse_chapter(self, url, strip_authors_note=True):
        self.info(f'Parsing chapter: {url}' )
        doc = self.fetch(url)

        content, = doc.find_class('entry-content')

        # Remove author's note, etc
        if strip_authors_note:
            first_tag = content.getchildren()[0]
            if 'Title:' in first_tag.text_content():
                content.remove(content.getchildren()[0])

        # Remove blog share links
        for div in content.find_class('sharedaddy'):
            content.remove(div)

        # Remove link to next chapter (any link in last paragraph)
        last_link = content.xpath('*[last()]//a')
        if last_link:
            last_link[0].getparent().remove(last_link[0])

        # Find any other links back to the series index
        # This catches some links after "The End" sometimes
        other_link = content.xpath('*//a[starts-with(@href, "http://keiramarcos.com/fan-fiction")]')
        if other_link:
            other_link[0].getparent().remove(other_link[0])

        clean(content)
        yield from content
