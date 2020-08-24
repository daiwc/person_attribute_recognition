import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../'))

from model.backbone.resnet import *
from model.backbone.resnet_nl import *
from model.backbone.resnet_ibn_a import *
from model.backbone.resnet_ibn_a_nl import *
from model.backbone.osnet import *
from model.backbone.vgg import *
from model.backbone.eficientnet import Efficient

__backbones = {
    'osnet': (osnet, 512),
    'resnet50': (resnet50, 2048),
    'resnet101': (resnet101, 2048),
    'resnet50_nl': (resnet50_nl, 2048),
    'resnet101_nl': (resnet101_nl, 2048),
    'resnet50_ibn_a': (resnet50_ibn_a, 2048),
    'resnet101_ibn_a': (resnet101_ibn_a, 2048),
    'resnet50_ibn_a_nl': (resnet50_ibn_a_nl, 2048),
    'resnet101_ibn_a_nl': (resnet101_ibn_a_nl, 2048),
    'vgg16': (vgg16, 512),
    'vgg19': (vgg19, 512),
    'vgg16_bn': (vgg16_bn, 512),
    'vgg19_bn': (vgg19_bn, 512)
}

def build_backbone(name, pretrained=True, progress=True):
    # assert name in __backbones.keys(), 'name of backbone must in %s' % str(__backbones.keys())
    # return __backbones[name][0](pretrained=pretrained, progress=progress), __backbones[name][1]
    if name in __backbones.keys():
        return __backbones[name][0](pretrained=pretrained, progress=progress), __backbones[name][1]
    elif name in ['efficientnet-b'+str(i) for i in range(9)]:
        model = Efficient(name)
        return model, model.get_out_channels()