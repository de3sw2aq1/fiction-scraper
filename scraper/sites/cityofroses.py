from lxml.html import builder as E
from . import Spider

START_URL = 'http://thecityofroses.com/contents'


class Cityofroses(Spider):
    domain = 'thecityofroses.com'

    def parse(self, url):
        doc = self.fetch(START_URL)

        self.metadata['title'] = 'City of Roses'
        self.metadata['author'] = 'Kip Manley'

        contents = doc.get_element_by_id('thecontents')
        for link in contents.xpath('h2/a/@href'):
            yield from self._parse_chapter(link)

    def _parse_chapter(self, url):
        self.info('Parsing chapter: %s', url)
        doc = self.fetch(url)

        title, = doc.xpath('//title/text()')
        title = title.split(' | ')[-1].strip()
        yield E.H1(title)

        content = doc.get_element_by_id('content')

        # Replace empty <h6> tags with <br>
        for h6 in content.iter('h6'):
            h6.addprevious(E.HR())
            h6.drop_tree()

        for tag in content:
            # Start of section
            if tag.tag == 'h3':
                yield E.H2(tag.text_content().strip())

            # Section content
            elif tag.get('class') == 'grafset':
                yield from tag

            # End note
            elif tag.get('class') == 'endnote':
                # Change <p> into a <blockquote>
                tag.tag = 'blockquote'
                yield tag
