''' See: 
'''
from struct import pack
from Blit import Layer, utils
from numpy import zeros
from PIL import Image
    
def uint8(num):
    return pack('>B', num)

def int16(num):
    return pack('>h', num)

def uint16(num):
    return pack('>H', num)

def uint32(num):
    return pack('>I', num)

def double(num):
    return pack('>d', num)

def pascal_string(chars, pad_to):
    base = uint8(len(chars)) + chars
    base += '\x00' * ((pad_to - len(base) % pad_to) % pad_to)
    
    return base

class Dummy:
    def tostring(self):
        return uint32(0)

class PhotoshopFile:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_pgfId-1036097
    '''
    def __init__(self, file_header, color_mode_data, image_resources, layer_mask_info, image_data):
        self.file_header = file_header
        self.color_mode_data = color_mode_data
        self.image_resources = image_resources
        self.layer_mask_info = layer_mask_info
        self.image_data = image_data
    
    def tostring(self):
        return self.file_header.tostring() + self.color_mode_data.tostring() \
             + self.image_resources.tostring() + self.layer_mask_info.tostring() \
             + self.image_data.tostring()

class FileHeader:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_19840
    '''
    def __init__(self, channel_count, height, width, depth, color_mode):
        self.channel_count = channel_count
        self.height = height
        self.width = width
        self.depth = depth
        self.color_mode = color_mode
    
    def tostring(self):
        
        parts = [
            '8BPS',
            uint16(1),
            '\x00' * 6,
            uint16(self.channel_count),
            uint32(self.height),
            uint32(self.width),
            uint16(self.depth),
            uint16(self.color_mode)
        ]
        
        return ''.join(parts)

class ColorModeData (Dummy):
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_71638
    '''
    pass

class ImageResourceSection (Dummy):
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_69883
    '''
    pass

class LayerMaskInformation:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_75067
    '''
    def __init__(self, layer_info, global_layer_mask):
        self.layer_info = layer_info
        self.global_layer_mask = global_layer_mask
    
    def tostring(self):
        layer_info = self.layer_info.tostring()
        global_layer_mask = self.global_layer_mask.tostring()
        
        layer_mask_info = layer_info + global_layer_mask
        return uint32(len(layer_mask_info)) + layer_mask_info

class LayerInformation:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_16000
    '''
    def __init__(self, layer_count, layer_records, channel_image_data):
        self.layer_count = layer_count
        self.layer_records = layer_records
        self.channel_image_data = channel_image_data
    
    def tostring(self):
        layer_count = uint16(self.layer_count)
        layer_records = ''.join([record.tostring() for record in self.layer_records])
        channel_image_data = self.channel_image_data.tostring()
        
        layer_info = layer_count + layer_records + channel_image_data
        return uint32(len(layer_info)) + layer_info

class LayerRecord:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_13084
    '''
    def __init__(self, rectangle, channel_count, channel_info, blend_mode, opacity,
                 clipping, mask_data, blending_ranges, name, additional_infos):
        self.rectangle = rectangle
        self.channel_count = channel_count
        self.channel_info = channel_info
        self.blend_mode = blend_mode
        self.opacity = opacity
        self.clipping = clipping
        self.mask_data = mask_data
        self.blending_ranges = blending_ranges
        self.name = name
        self.additional_infos = additional_infos
    
    def tostring(self):
        pixel_count = (self.rectangle[2] - self.rectangle[0]) * (self.rectangle[3] - self.rectangle[1])
        mask_data = self.mask_data.tostring()
        blending_ranges = self.blending_ranges.tostring()
        name = pascal_string(self.name, 4)
        additional_infos = ''.join([info.tostring() for info in self.additional_infos])
    
        parts = [
            ''.join(map(uint32, self.rectangle)),
            uint16(self.channel_count),
            ''.join([int16(chid) + uint32(2 + pixel_count) for chid in self.channel_info]),
            '8BIM',
            self.blend_mode,
            uint8(self.opacity),
            uint8(self.clipping),
            uint8(0b00000000),
            uint8(0x00),
            uint32(len(mask_data + blending_ranges + name + additional_infos)),
            mask_data,
            blending_ranges,
            name,
            additional_infos
        ]
        
        return ''.join(parts)

class GlobalLayerMask (Dummy):
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_17115
    '''
    pass

class AdditionalLayerInfo:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_71546
    '''
    code, data = None, None
    
    def tostring(self):
        return '8BIM' + self.code + uint32(len(self.data)) + self.data

class SolidColorInfo (AdditionalLayerInfo):

    def __init__(self, red, green, blue):
        red, green, blue = [double(component) for component in (red, green, blue)]
    
        self.code = 'SoCo'
        self.data = '\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00null\x00\x00\x00\x01\x00\x00\x00\x00Clr Objc\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00RGBC\x00\x00\x00\x03\x00\x00\x00\x00Rd  doub%(red)s\x00\x00\x00\x00Grn doub%(green)s\x00\x00\x00\x00Bl  doub%(blue)s' % locals()

class LayerMaskAdjustmentData (Dummy):
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_22582
    '''
    pass

class LayerBlendingRangesData (Dummy):
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_21332
    '''
    pass

class ChannelImageData:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_26431
    '''
    def __init__(self, channels):
        self.channels = channels
    
    def tostring(self):
        ''' Compression. 0 = Raw Data, 1 = RLE compressed, 2 = ZIP without prediction, 3 = ZIP with prediction.
        '''
        return ''.join(['\x00\x00' + chan.tostring() for chan in self.channels])

class ImageData:
    ''' http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/PhotoshopFileFormats.htm#50577409_89817
    '''
    def __init__(self, channels):
        self.channels = channels
    
    def tostring(self):
        ''' Compression. 0 = Raw Data, 1 = RLE compressed, 2 = ZIP without prediction, 3 = ZIP with prediction.
        '''
        return '\x00\x00' + ''.join([chan.tostring() for chan in self.channels])

class PSD (Layer):

    def __init__(self, width, height):
        channels = [zeros((width, height), dtype=float)] * 4
        Layer.__init__(self, channels)
        
        self.head = FileHeader(3, height, width, 8, 3)
    
    def save(self, outfile):
        img = self.image()
        
        rec_args = dict(
            rectangle = (0, 0) + self.size(),
            channel_count = 4,
            channel_info = (0, 1, 2, -1),
            blend_mode = 'norm',
            opacity = 0xff,
            clipping = 0x00,
            mask_data = LayerMaskAdjustmentData(),
            blending_ranges = LayerBlendingRangesData(),
            name = '',
            additional_infos = []
            )
        
        rec = LayerRecord(**rec_args)
        cim = ChannelImageData(img.split())
        info = LayerInformation(1, [rec], cim)
        lmi = LayerMaskInformation(info, GlobalLayerMask())
        idata = ImageData(img.split()[:3])
        
        file = PhotoshopFile(self.head, ColorModeData(), ImageResourceSection(), lmi, idata)
        
        open(outfile, 'w').write(file.tostring())

if __name__ == '__main__':

    psd = PSD(128, 128)
    
    psd.save('made.psd')
    
    exit()
    
    img = Image.new('RGBA', (8, 8), (0xff, 0x99, 0x00, 0xff))
    
    rec_args = dict(
        rectangle = (0, 0, 8, 8),
        channel_count = 4,
        channel_info = (0, 1, 2, -1),
        blend_mode = 'norm',
        opacity = 0xff,
        clipping = 0x00,
        mask_data = LayerMaskAdjustmentData(),
        blending_ranges = LayerBlendingRangesData(),
        name = 'Orange',
        additional_infos = [SolidColorInfo(0xff, 0x00, 0xff)]
        )
    
    rec = LayerRecord(**rec_args)
    cim = ChannelImageData(img.split())
    info = LayerInformation(1, [rec], cim)
    lmi = LayerMaskInformation(info, GlobalLayerMask())
    idata = ImageData(img.split()[:3])
    
    head = FileHeader(3, 8, 8, 8, 3)
    
    file = PhotoshopFile(head, ColorModeData(), ImageResourceSection(), lmi, idata)
    
    print repr(file.tostring())
    
    open('made.psd', 'w').write(file.tostring())
