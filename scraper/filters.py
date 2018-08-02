from lxml.html import clean


# Cleaner to remove unnecessary tags and attributes
clean = clean.Cleaner(
    remove_tags=('div', 'span'),
    safe_attrs=clean.Cleaner.safe_attrs - {'width', 'height'}
)

# TODO: add filter to move attributes from <p> tags onto a <div> for Pandoc

# TODO: add configurable filter to remove tags by class name

# TODO: add filter to ensure ids are unique throughout the document

DEFAULT_FILTERS = [clean]