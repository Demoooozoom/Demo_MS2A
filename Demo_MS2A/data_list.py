import torch
import numpy as np
import random
from PIL import Image
from torch.utils.data import Dataset
import os
import os.path
import cv2
import torchvision
from torchvision.transforms import autoaugment, transforms
#from RandAugment import RandAugment

import torchsample as ts
from torchvision import transforms
import copy



# /home/ts/anaconda3/envs/vit_kd/lib/python3.7/site-packages



def make_dataset(image_list, labels):#将路径和标签分离
    if labels:
      len_ = len(image_list)
      images = [(image_list[i].strip(), labels[i, :]) for i in range(len_)]
    else:
      if len(image_list[0].split()) > 2:
        images = [(val.split()[0], np.array([int(la) for la in val.split()[1:]])) for val in image_list]
      else:
        images = [(val.split()[0], int(val.split()[1])) for val in image_list]
    return images


def rgb_loader(path):
    with open(path, 'rb') as f:
        with Image.open(f) as img:
            return img.convert('RGB')

def l_loader(path):
    with open(path, 'rb') as f:
        with Image.open(f) as img:
            return img.convert('L')

class ImageList(Dataset):
    def __init__(self, image_list, labels=None, transform=None, target_transform=None, mode='RGB'):
        imgs = make_dataset(image_list, labels)
        if len(imgs) == 0:
            raise(RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                               "Supported image extensions are: " + ",".join(IMG_EXTENSIONS)))

        self.imgs = imgs
        self.transform = transform
        self.target_transform = target_transform
        if mode == 'RGB':
            self.loader = rgb_loader
        elif mode == 'L':
            self.loader = l_loader

    def __getitem__(self, index):
        path, target = self.imgs[index]
        img = self.loader(path)
        if self.transform is not None:
            img = self.transform(img)
        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        return len(self.imgs)

class ImageList_idx(Dataset):
    def __init__(self, image_list, labels=None, transform=None, target_transform=None, mode='RGB'):
        imgs = make_dataset(image_list, labels)
        if len(imgs) == 0:
            raise(RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                               "Supported image extensions are: " + ",".join(IMG_EXTENSIONS)))

        self.imgs = imgs
        self.transform = transform
        self.target_transform = target_transform
        if mode == 'RGB':
            self.loader = rgb_loader
        elif mode == 'L':
            self.loader = l_loader

    def __getitem__(self, index):
        path, target = self.imgs[index]
        img = self.loader(path)
        if self.transform is not None:
            img = self.transform(img)
        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target, index
#图像，label，坐标
    def __len__(self):
        return len(self.imgs)


class ImageList_idx_aug(Dataset):
    def __init__(self, image_list, labels=None, transform=None, target_transform=None, mode='RGB'):
        
        self.ra_obj = autoaugment.RandAugment()
        self.committee_size = 1
        resize_size = 256 
        crop_size = 224
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.transform_aug = copy.deepcopy(transform)
        self.transform_aug.transforms.insert(0, self.ra_obj)
        imgs = make_dataset(image_list, labels)
        if len(imgs) == 0:
            raise(RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                               "Supported image extensions are: " + ",".join(IMG_EXTENSIONS)))

        self.imgs = imgs
        self.transform = transform
        self.target_transform = target_transform
        #transform为空
        if mode == 'RGB':
            self.loader = rgb_loader
        elif mode == 'L':
            self.loader = l_loader

    def __getitem__(self, index):
        path, target = self.imgs[index]
        img = self.loader(path)

        if self.transform is not None:
            data = self.transform(img)
        
        if self.target_transform is not None:
            target = self.target_transform(target)
        
        rand_aug_lst = [self.transform_aug(img) for _ in range(self.committee_size)]
        return (data, rand_aug_lst), target, index

    def __len__(self):
        return len(self.imgs)


class ImageList_idx_aug_fix(Dataset):
    def __init__(self, image_list, labels=None, transform=None, target_transform=None, mode='RGB'):
        self.ra_obj = autoaugment.RandAugment()
        #self.ra_obj = RandAugment(2,9)#数据增强
        self.committee_size = 1
        resize_size = 256 
        crop_size = 224 
        #对大于crop_size的图片进行随机裁剪，训练阶段是随机裁剪，验证阶段是随机裁剪或中心裁剪
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])#归一化
        RandomRotate_1 = ts.transforms.RandomRotate(0.5)#以一定的概率（0.5）对图像在[-rotate_range, rotate_range]角度范围内进行旋转
        self.rf_1 = transforms.Compose([
                transforms.Resize((resize_size, resize_size)),
                transforms.RandomCrop(crop_size),
                transforms.ToTensor(),#​ToTensor()​​​将​​shape​​​为​​(H, W, C)​​​的​​nump.ndarray​​​或​​img​​​转为​​shape​​​为​​(C, H, W)​​​的​​tensor​​​，其将每一个数值归一化到​​[0,1]​​，其归一化方法比较简单，直接除以255即可
                RandomRotate_1,
                normalize
            ])
        #用Compose把多个步骤整合到一起
        imgs = make_dataset(image_list, labels)
        if len(imgs) == 0:
            raise(RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                               "Supported image extensions are: " + ",".join(IMG_EXTENSIONS)))

        self.imgs = imgs
        self.transform = transform
        self.target_transform = target_transform
        if mode == 'RGB':
            self.loader = rgb_loader
        elif mode == 'L':
            self.loader = l_loader

    def __getitem__(self, index):
        path, target = self.imgs[index]
        img = self.loader(path)

        if self.transform is not None:
            data = self.transform(img)
        
        if self.target_transform is not None:
            target = self.target_transform(target)

        img_1 = self.rf_1(img)
        re_ls = [img_1]
        return (data, re_ls), target, index

    def __len__(self):
        return len(self.imgs)

