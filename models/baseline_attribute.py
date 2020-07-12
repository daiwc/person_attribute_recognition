import torch
import torchvision
import torch.nn as nn
from torch.nn import init

import sys
sys.path.append('.')

def weights_init_kaiming(m):
    classname = m.__class__.__name__
    if classname.find('Linear') != -1:
        nn.init.kaiming_normal_(m.weight, a=0, mode='fan_out')
        nn.init.constant_(m.bias, 0.0)
    elif classname.find('Conv') != -1:
        nn.init.kaiming_normal_(m.weight, a=0, mode='fan_in')
        if m.bias is not None:
            nn.init.constant_(m.bias, 0.0)
    elif classname.find('BatchNorm') != -1:
        if m.affine:
            nn.init.constant_(m.weight, 1.0)
            nn.init.constant_(m.bias, 0.0)

def weights_init_classifier(m):
    classname = m.__class__.__name__
    if classname.find('Linear') != -1:
        nn.init.normal_(m.weight, std=0.001)
        if m.bias:
            nn.init.constant_(m.bias, 0.0)

class BaselineAttribute(nn.Module):
    ''' https://arxiv.org/pdf/2005.11909.pdf
    '''
    def __init__(self, num_classes):
        super(BaselineAttribute, self).__init__()
        self.num_classes = num_classes
        self.base = torchvision.models.resnet50(pretrained=True)
        self.avgpool = nn.AdaptiveAvgPool2d(1)

        # remove the final downsample of resnet
        self.base.layer4[0].downsample[0].stride = (1, 1)
        self.base.layer4[0].conv2.stride=(1,1)

        self.classifier = nn.Sequential(
            nn.Linear(2048, self.num_classes),
            nn.BatchNorm1d(self.num_classes)
        )
        # self.classifier.apply(weights_init_classifier)

    def forward(self, x):
        x = self.base.conv1(x)
        x = self.base.bn1(x)
        x = self.base.relu(x)
        x = self.base.maxpool(x)

        x = self.base.layer1(x)
        x = self.base.layer2(x)
        x = self.base.layer3(x)
        x = self.base.layer4(x)
        # x.size = (batch_size, 2048, 16, 8)
        x = self.avgpool(x)
        x = x.view(x.shape[0], -1)
        # x.size() = (batch_size, 2048)
        x = self.classifier(x)
        return x

