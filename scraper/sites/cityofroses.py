from lxml.html import builder as E
from .. import Spider, filters

START_URL = 'http://thecityofroses.com/contents'

# TODO: story uses <span class="caps"> for small caps
# TODO: use picture icon for scene break

def scene_breaks(root):
    # Replace empty <h6> tags with <br>
    for h6 in root.xpath('.//h6'):
        h6.addprevious(E.HR(E.CLASS('scene-break')))
        h6.drop_tree()


class Cityofroses(Spider):
    name = "City of Roses"
    domain = 'thecityofroses.com'
    url = 'http://thecityofroses.com/'
    filters = (scene_breaks, *filters.DEFAULT_FILTERS)

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

        for tag in doc.get_element_by_id('content'):
            # Start of section
            if tag.tag == 'h3':
                yield E.H2(tag.text_content().strip())

            # Section content
            elif 'grafset' in tag.classes:
                yield from tag

            # End note
            elif 'endnote' in tag.classes:
                # Change tag into a <blockquote class="endnote">
                tag.tag = 'blockquote'
                yield tag
