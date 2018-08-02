import sys
from lxml.html import builder as E
from . import Spider

START_URL = 'http://thecityofroses.com/contents'


class Cityofroses(Spider):
    domain = 'thecityofroses.com'

    def parse(self, url):
        doc = self.fetch(START_URL)

        title, = doc.xpath('//meta[@property="og:site_name"]/@content')
        self.metadata['title'] = title.strip()
        self.metadata['author'] = 'Kip Manley'

        contents = doc.get_element_by_id('thecontents')

        for link in contents.xpath('h2/a/@href'):
            yield from self._parse_chapter(link)

    def _parse_chapter(self, url):
        self.info(f'Parsing chapter: {url}' )
        doc = self.fetch(url)

        title, = doc.xpath('//title/text()')
        title = title.split(' | ')[-1]
        yield E.H1(title.strip())

        content = doc.get_element_by_id('content')

        # Replace empty <h6> tags with <br>
        for h6 in content.xpath('//h6'):
            hr = E.HR()
            h6.addprevious(hr)
            h6.getparent().remove(h6)

        for tag in content.iterchildren():
            # Start of section
            if tag.tag == 'h3':
                section_title = tag.text_content()
                yield E.H2(section_title.strip())

            # Section content
            elif tag.get('class') == 'grafset':
                yield from tag
            
            # End note
            elif tag.get('class') == 'endnote':
                # Change <p> into a <blockquote>
                tag.tag = 'blockquote'
                yield tag
