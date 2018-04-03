import sys
from lxml.html import builder as E
import scraper

def process_index(document, url):
    doc = document.fetch_doc(url)

    document.metadata['title'] = str(doc.xpath('//meta[@property="og:site_name"]/@content')[0])
    document.metadata['author'] = 'Kip Manley'

    contents = doc.get_element_by_id('thecontents')

    for link in contents.xpath('h2/a/@href'):
        process_chapter(document, link)

def process_chapter(document, url):
        doc = document.fetch_doc(url)

        title, = doc.xpath('//title/text()')
        title = title.split(' | ')[-1]
        document.write(E.H1(title))

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
                document.write(E.H2(section_title))

            # Section content
            elif tag.get('class') == 'grafset':
                document.write(*tag.getchildren())
            
            # End note
            elif tag.get('class') == 'endnote':
                # Change <p> into a <blockquote>
                tag.tag = 'blockquote'
                document.write(tag)

def main():
    pandoc_args = sys.argv[1:]
    url = 'http://thecityofroses.com/contents'

    # Set EPUB chapter level to 2 because the story is broken into sections
    with scraper.Document('--epub-chapter-level=2', *pandoc_args) as d:
        process_index(d, url)

if __name__ == '__main__':
    main()