import os
import sys
from tempfile import NamedTemporaryFile
from lxml.html import builder as E
import requests
from . import Spider

URL_ALL = 'http://www.starwalkerblog.com/'
URL_SUMMARY = 'http://www.starwalkerblog.com/about/about-starwalker/'
URL_COVER = 'http://www.starwalkerblog.com/wp-content/uploads/2012/07/Spiral2_sm.jpg'
EXTRA_PAGES = [
    'http://www.starwalkerblog.com/cast/',
    'http://www.starwalkerblog.com/colonies/',
    'http://www.starwalkerblog.com/terminology/',
    'http://www.starwalkerblog.com/about/about-the-author/'
]

CHAPTER_LEVEL = 3

def heading(level, text, **kwargs):
    return E.E('h'+str(level), text, **kwargs)

class Starwalker(Spider):
    domain = 'starwalkerblog.com'

    def parse(self, url, level=0):
        self.info(f'Parsing page: {url}')

        doc = self.fetch(url)
        categories = doc.get_element_by_id('categories')

        if url == URL_ALL:
            category = categories
            self.metadata['title'] = 'Starwalker'
            self.metadata['author'] = 'Melanie Edmonds'
            self._parse_summary()
        else:
            category = categories.xpath('.//li[a[@href=$url]]', url=url)
            if not category:
                raise LookupError('Could not find category in TOC')

            category = category[0]
            title, = category.xpath('a/text()')

            if level == 0:
                self.metadata['title'] = 'Starwalker ' + str(title)
                self.metadata['author'] = 'Melanie Edmonds'
                self._parse_summary()
            else:
                yield heading(level, title)

        subcategory_urls = category.xpath('ul/li/a/@href')

        # "4.4: Rosetta" contains both chapters and the 
        # subcategory "Book 4 Alt Timeline"
        if not subcategory_urls or url == 'http://www.starwalkerblog.com/category/4-black-star/rosetta/':
            # Add ?order=asc because some categories are in reverse order
            yield from self._parse_category(url+'?order=asc')

        for subcategory_url in subcategory_urls:
            # Skip author's notes
            if subcategory_url == 'http://www.starwalkerblog.com/category/authors-notes/':
                continue
            # Reduce nesting level of alt timeline
            elif subcategory_url == 'http://www.starwalkerblog.com/category/4-black-star/rosetta/book-4-alt-timeline/':
                yield from self.parse(subcategory_url, level)
            else:
                yield from self.parse(subcategory_url, level+1)

        # Extra pages if all sections are included
        if url == URL_ALL:
            for url in EXTRA_PAGES:
                yield from self._parse_page(url, level=1)

    def _parse_category(self, url):
        doc = self.fetch(url)

        for page_url in doc.xpath('//h3/a/@href'):
            yield from self._parse_page(page_url, category_url=url)

        prev_page = doc.cssselect('.navigation .alignleft a')
        if prev_page:
            yield from self._parse_category(prev_page[0].get('href'))

    def _parse_page(self, url, category_url=None, level=CHAPTER_LEVEL):
        doc = self.fetch(url)

        # If we are parsing Alt timeline pages when we only want Rosetta pages, skip them
        # The page's category will be more specific than the desired category_url
        for c in doc.xpath('//a[@rel="category tag"]'):
            if category_url and not category_url.startswith(c.get('href')):
                return

        title, = doc.xpath('//h3[@class="posttitle"]/a/text()')
        yield heading(level, title)

        # Blog posts use .entry and pages use .entrytext
        content, = doc.cssselect('.entrytext, .entry')

        # Remove share links
        for tag in content.cssselect('.reaction_buttons, .sharedaddy'):
            tag.getparent().remove(tag)

        # Convert headings (only from EXTRA_PAGES) to <h4>
        for tag in content.iter():
            if tag.tag[0] == 'h':
                tag.tag = 'h'+str(CHAPTER_LEVEL+1)

        yield from content

    def _parse_summary(self):
        doc = self.fetch(URL_SUMMARY)
        summary_paragraphs = doc.xpath('//div[@class="entrytext"]/p')
        summary = '\n\n'.join(p.text_content().strip() for p in summary_paragraphs)
        self.metadata['description'] = summary

    # TODO: make cover images work in Spider class
    # def parse_cover_image():
    #     cover = NamedTemporaryFile(suffix='.jpg', delete=False)
    #     cover.write(
    #         requests.get(URL_COVER).content
    #     )
    #     cover.close()
