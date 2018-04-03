import sys
from lxml.html import builder as E
import scraper

def process_index(document, url):
    doc = document.fetch_doc(url)

    title = str(doc.xpath('//meta[@property="og:title"]/@content')[0])
    document.metadata['title'] = title
    document.metadata['author'] = 'Wildbow'

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

        document.write(E.H1(arc_title))

        for chapter in arc.iter('a'):
            process_chapter(document, chapter.get('href'))

def process_chapter(document, url):
        doc = document.fetch_doc(url)

        title, = doc.find_class('entry-title')
        document.write(E.H2(title.text_content))

        content, = doc.find_class('entry-content')

        # Remove social media links
        for tag in content.find_class('sharedaddy'):
            tag.getparent().remove(tag)

        # Remove next/previous chapter links
        # The only other link is an Urban Dictionary definition of "trigger warnings"
        for link in content.xpath('.//a'):
            if link.text_content().strip() in ('Last Chapter', 'Next Chapter', 'End'):
                # Remove parent <p> tag completely
                parent = link.getparent()
                if parent.getparent() is not None:
                    parent.getparent().remove(parent)
        
        # Process inline styles
        for tag in content.xpath('.//*[@style]'):
            style = tag.get('style')

            # Convert padding to <blockquote>
            # Ideally we would put consecutive paragraphs in the same
            # <blockquote>... but I am lazy
            if 'padding-left:30px;' in style:
                blockquote = E.BLOCKQUOTE()
                tag.addprevious(blockquote)
                blockquote.insert(0, tag)

            # Convert double padding to nested <blockquote> tags
            elif 'padding-left:60px;' in style:
                nested_blockquote = E.BLOCKQUOTE()
                blockquote = E.BLOCKQUOTE(nested_blockquote)
                tag.addprevious(blockquote)
                nested_blockquote.insert(0, tag)

            # Pandoc doesn't support styles on <p> so the tag has to be wrapped     
            # In a <div> with the style
            elif 'text-align:center;' in style:
                div = E.DIV(style='text-align:center')
                tag.addprevious(div)
                div.insert(0, tag)

            # Allow underlined text styles to stay
            # Thankfully these are on <span> tags, not <p> tags
            elif 'text-decoration:underline' in style:
                continue
            
            del tag.attrib['style']

        document.write(*content.getchildren())

def main():
    pandoc_args = sys.argv[1:]
    url = 'https://parahumans.wordpress.com/'

    # Set EPUB chapter level to 2 because the story is broken into sections
    with scraper.Document('--epub-chapter-level=2', *pandoc_args) as d:
        process_index(d, url)

if __name__ == '__main__':
    main()