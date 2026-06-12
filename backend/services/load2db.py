from lxml import etree



async def load2db(file, photos):
    text = await file.read()
    xml = etree.fromstring(text)