from PIL import Image, ImageColor
from sorl.thumbnail.engines.pil_engine import Engine

class Engine(Engine):
    def create(self, image, geometry, options):
        if options.get('background'):
            try:
                background = Image.new(
                    'RGB',
                    image.size,
                    (255, 255, 255))
                background.paste(image, mask=image.split()[3]) # 3 is the alpha of an RGBA image.
                return super(Engine, self).create(background, geometry, options)
            except Exception, e:
                pass
        return super(Engine, self).create(image, geometry, options)
