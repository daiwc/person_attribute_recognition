import math
import sys
sys.path.append('.')
import torchvision

import torch
import torch.nn as nn

from torch.hub import load_state_dict_from_url

from utils import summary

__all__ = ['resnet50_ibn_a_nl', 'resnet101_ibn_a_nl']


model_urls = {
    'resnet50_ibn_a': 'https://github.com/XingangPan/IBN-Net/releases/download/v1.0/resnet50_ibn_a-d9d0bb7b.pth',
    'resnet101_ibn_a': 'https://github.com/XingangPan/IBN-Net/releases/download/v1.0/resnet101_ibn_a-59ea0ac6.pth',
}

class NonLocalBlock(nn.Module):
    r""" Non local block:
    Inspired from:
        - https://openaccess.thecvf.com/content_cvpr_2018/papers/Wang_Non-Local_Neural_Networks_CVPR_2018_paper.pdf
        - https://arxiv.org/pdf/2001.04193.pdf
        - https://github.com/mangye16/ReID-Survey/blob/master/modeling/layer/non_local.py
        - https://github.com/tea1528/Non-Local-NN-Pytorch/blob/master/models/non_local.py
    """
    def __init__(self, in_channel, reduction_ratio=2):
        super(NonLocalBlock, self).__init__()
        assert in_channel % reduction_ratio == 0
        self.in_channel = in_channel
        self.hidden_channel = in_channel // reduction_ratio
        
        self.theta = nn.Conv2d(self.in_channel, self.hidden_channel, kernel_size=1, stride=1, padding=0)
        self.phi = nn.Conv2d(self.in_channel, self.hidden_channel, kernel_size=1, stride=1, padding=0)
        self.g = nn.Conv2d(self.in_channel, self.hidden_channel, kernel_size=1, stride=1, padding=0)
        self.W = nn.Sequential(
            nn.Conv2d(self.hidden_channel, self.in_channel, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(self.in_channel)
        )
        nn.init.constant_(self.W[1].weight, 0.0)
        nn.init.constant_(self.W[1].bias, 0.0)

    def forward(self, x):
        batch_size = x.size(0)
        theta_out = self.theta(x).view(batch_size, self.hidden_channel, -1).permute(0, 2, 1)
        phi_out = self.phi(x).view(batch_size, self.hidden_channel, -1)
        g_out = self.g(x).view(batch_size, self.hidden_channel, -1).permute(0, 2, 1)
        f = torch.matmul(theta_out, phi_out)
        f = f / f.size(-1)

        y = torch.matmul(f, g_out).permute(0, 2, 1).contiguous()
        y = y.view(batch_size, self.hidden_channel, x.size(2), x.size(3))
        W_out = self.W(y)
        out = W_out + x
        return out

class IBN(nn.Module):
    r"""Instance-Batch Normalization layer from
    `"Two at Once: Enhancing Learning and Generalization Capacities via IBN-Net"
    <https://arxiv.org/pdf/1807.09441.pdf>`
    Args:
        planes (int): Number of channels for the input tensor
        ratio (float): Ratio of instance normalization in the IBN layer
    """
    def __init__(self, planes, ratio=0.5):
        super(IBN, self).__init__()
        self.half = int(planes * ratio)
        self.IN = nn.InstanceNorm2d(self.half, affine=True)
        self.BN = nn.BatchNorm2d(planes - self.half)

    def forward(self, x):
        split = torch.split(x, self.half, 1)
        out1 = self.IN(split[0].contiguous())
        out2 = self.BN(split[1].contiguous())
        out = torch.cat((out1, out2), 1)
        return out

class Bottleneck_IBN(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, ibn=None, stride=1, downsample=None):
        super(Bottleneck_IBN, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        if ibn == 'a':
            self.bn1 = IBN(planes)
        else:
            self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.IN = nn.InstanceNorm2d(planes * 4, affine=True) if ibn == 'b' else None
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        if self.IN is not None:
            out = self.IN(out)
        out = self.relu(out)

        return out

class ResNet_IBN(nn.Module):
    def __init__(self,
                 block,
                 layers,
                 non_layers,
                 ibn_cfg=('a', 'a', 'a', None)):
        
        self.inplanes = 64
        super(ResNet_IBN, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        if ibn_cfg[0] == 'b':
            self.bn1 = nn.InstanceNorm2d(64, affine=True)
        else:
            self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0], ibn=ibn_cfg[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2, ibn=ibn_cfg[1])
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2, ibn=ibn_cfg[2])
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2, ibn=ibn_cfg[3])
        
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

        # non local block
        self.NL_1 = nn.ModuleList([NonLocalBlock(256) for i in range(non_layers[0])])
        self.NL_1_idx = sorted([layers[0] - (i + 1) for i in range(non_layers[0])])
        self.NL_2 = nn.ModuleList([NonLocalBlock(512) for i in range(non_layers[1])])
        self.NL_2_idx = sorted([layers[1] - (i + 1) for i in range(non_layers[1])])
        self.NL_3 = nn.ModuleList([NonLocalBlock(1024) for i in range(non_layers[2])])
        self.NL_3_idx = sorted([layers[2] - (i + 1) for i in range(non_layers[2])])
        self.NL_4 = nn.ModuleList([NonLocalBlock(2048) for i in range(non_layers[3])])
        self.NL_4_idx = sorted([layers[3] - (i + 1) for i in range(non_layers[3])])

    def _make_layer(self, block, planes, blocks, stride=1, ibn=None):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes,
                            None if ibn == 'b' else ibn,
                            stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes,
                                None if (ibn == 'b' and i < blocks-1) else ibn))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        NL1_counter = 0
        if len(self.NL_1_idx) == 0: 
            self.NL_1_idx = [-1]
        for i in range(len(self.layer1)):
            x = self.layer1[i](x)
            if i == self.NL_1_idx[NL1_counter]:
                _, C, H, W = x.shape
                x = self.NL_1[NL1_counter](x)
                NL1_counter += 1
        # Layer 2
        NL2_counter = 0
        if len(self.NL_2_idx) == 0: 
            self.NL_2_idx = [-1]
        for i in range(len(self.layer2)):
            x = self.layer2[i](x)
            if i == self.NL_2_idx[NL2_counter]:
                _, C, H, W = x.shape
                x = self.NL_2[NL2_counter](x)
                NL2_counter += 1
        # Layer 3
        NL3_counter = 0
        if len(self.NL_3_idx) == 0: 
            self.NL_3_idx = [-1]
        for i in range(len(self.layer3)):
            x = self.layer3[i](x)
            if i == self.NL_3_idx[NL3_counter]:
                _, C, H, W = x.shape
                x = self.NL_3[NL3_counter](x)
                NL3_counter += 1
        # Layer 4
        NL4_counter = 0
        if len(self.NL_4_idx) == 0: 
            self.NL_4_idx = [-1]
        for i in range(len(self.layer4)):
            x = self.layer4[i](x)
            if i == self.NL_4_idx[NL4_counter]:
                _, C, H, W = x.shape
                x = self.NL_4[NL4_counter](x)
                NL4_counter += 1
                
        return x

def resnet50_ibn_a_nl(pretrained=False, **kwargs):
    """Constructs a ResNet-50-IBN-a model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet_IBN(block=Bottleneck_IBN,
                       layers=[3, 4, 6, 3],
                       non_layers=[0, 2, 3, 0],
                       ibn_cfg=('a', 'a', 'a', None),
                       **kwargs)
    if pretrained:
        model.load_state_dict(load_state_dict_from_url(model_urls['resnet50_ibn_a']), strict=False)
    return model


def resnet101_ibn_a_nl(pretrained=False, **kwargs):
    """Constructs a ResNet-101-IBN-a model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet_IBN(block=Bottleneck_IBN,
                       layers=[3, 4, 23, 3],
                       non_layers=[0, 2, 9, 0],
                       ibn_cfg=('a', 'a', 'a', None),
                       **kwargs)
    if pretrained:
        model.load_state_dict(load_state_dict_from_url(model_urls['resnet101_ibn_a']), strict=False)
    return model


if __name__ == "__main__":
    batch = torch.rand((4, 3, 256, 128))
    model = resnet50_ibn_a_nl(True)
    out = model(batch)
    summary(print, model, (3, 256, 128), 32, 'cpu', False)
    # summary(print, torchvision.models.resnet50(True), (3, 256, 128), 32, 'cpu', False)
    pass