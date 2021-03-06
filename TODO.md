- ~~weight_decay~~: 0.0005, 0.001, 0.01
- AGW: [Paper](https://arxiv.org/pdf/2001.04193.pdf), [Code](https://github.com/mangye16/ReID-Survey)
- ABD-Net: [Paper](https://arxiv.org/pdf/1908.01114.pdf), [Code](https://github.com/TAMU-VITA/ABD-Net)
- AdaptiveReID: [Paper](https://arxiv.org/pdf/2007.07875v1.pdf), [Code](https://github.com/nixingyang/AdaptiveReID)
- SBS: [Paper](https://arxiv.org/pdf/2006.02631.pdf), [Code](https://github.com/JDAI-CV/fast-reid/blob/master/MODEL_ZOO.md)
- MGN: [Paper](https://arxiv.org/pdf/1804.01438v1.pdf), [Code](https://github.com/GNAYUOHZ/ReID-MGN)
- ~~support more backbone~~: [resnet50_ibn_a](https://github.com/XingangPan/IBN-Net), ...

- ~~build_backbone function~~.
- ~~build_transforms function~~.

- transforms: [Auto-augment](https://github.com/JDAI-CV/fast-reid/blob/ee634df2900996233473cb95a80029bd456cce97/fastreid/data/transforms/autoaugment.py#L495), [Random patch](https://github.com/JDAI-CV/fast-reid/blob/ee634df290/fastreid/data/transforms/transforms.py),

- Pooling: [~~GeM pooling~~](https://github.com/JDAI-CV/fast-reid/blob/46228ce946/fastreid/layers/gem_pool.py), [Attention Pooling](https://github.com/JDAI-CV/fast-reid/blob/46228ce946/fastreid/layers/attention.py)

- [~~Reduction head~~](https://github.com/JDAI-CV/fast-reid/blob/46228ce946/fastreid/modeling/heads/reduction_head.py)

- Auto-augmentation: [Paper](https://arxiv.org/pdf/1805.09501.pdf)

- ~~Non-Local~~ : [Paper](https://openaccess.thecvf.com/content_cvpr_2018/papers/Wang_Non-Local_Neural_Networks_CVPR_2018_paper.pdf), [Paper](https://arxiv.org/pdf/2001.04193.pdf)

- GradCAM: [Paper](https://arxiv.org/pdf/1610.02391.pdf)

- Thay đổi ngưỡng khi quyết định true or false

- ~~so sánh với các mô hình khác OSNET~~.

- ~~Thong ke ty le nhan~~

- ~~thay doi backbone bằng OSNET~~

- train theo episode

- ~~So sanh cua hai ham loss khi su dung CEL_sigmoid va BCE~~

- ~~print freeze~~

- [RAP](https://arxiv.org/pdf/1603.07054.pdf)

- https://github.com/TylerYep/torch-summary

- https://github.com/lukemelas/EfficientNet-PyTorch, https://towardsdatascience.com/complete-architectural-details-of-all-efficientnet-models-5fd5b736142, https://amaarora.github.io/2020/08/13/efficientnet.html

- SimCLR: https://arxiv.org/pdf/2002.05709.pdf

- https://github.com/kakaobrain/fast-autoaugment, https://arxiv.org/pdf/1905.00397.pdf

- https://github.com/ildoonet/pytorch-randaugment

- https://www.dlology.com/blog/multi-class-classification-with-focal-loss-for-imbalanced-datasets/