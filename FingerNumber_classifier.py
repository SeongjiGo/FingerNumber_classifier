# 데이터 셋 구성하기, 경로를 파악한 후
# 클래스 이름(name), 클래스(class), 그리고 학습을 위한 클래스를 숫자로 나타낸 타겟(target)을 csv파일에 저장
import os
from glob import glob # 인자로 받은 패턴과 이름이 일치하는 모든 파일과 디렉터리의 리스트 반환
import pandas as pd

file_path = os.getcwd() + '/dataSet/*/*.png' # 데이터의 경로 저장
file_list = glob(file_path)

data_dict = {'image_name':[], 'class':[], 'target':[], 'file_path':[]}
# 학습에 사용하기 위한 넘버링(?)
target_dict = {'yi_1': 1, 'er_2': 2, 'san_3': 3, 'si_4':4, 'wu_5':5, 'liu_6':6, 'qi_7':7, 'ba_8':8, 'jiu_9':9, 'shi_10': 10}

for path in file_list:
    data_dict['file_path'].append(path) # file_path 항목에 파일 경로 저장

    path_list = path.split(os.path.sep) # os별 파일 경로 구분 문자로 split

    data_dict['image_name'].append(path_list[-1]) # 이미지 이름 저장
    data_dict['class'].append(path_list[-2]) # 어떤 클래스인지 저장
    data_dict['target'].append(target_dict[path_list[-2]]) # 그 클래스의 번호 저장

train_df = pd.DataFrame(data_dict) # 데이터 프레임 화
train_df.to_csv(os.getcwd()+"/train.csv", mode='w') # csv파일로 생성
print('csv파일 생성 완료!')

from sklearn.model_selection import train_test_split # 스플릿 모듈
def get_df():
    # csv 파일 읽어서 DataFrame으로 저장
    df = pd.read_csv(os.getcwd()+'/train.csv') # csv로 불러와서 데이터 저장
    print('csv 파일 DataFrame으로 저장 완료!')

    # 데이터셋을 train, val, test로 나누기
    df_train, df_test = train_test_split(df, test_size=0.2, random_state=2359)
    df_train, df_val = train_test_split(df_train, test_size=0.2, random_state=2359)
    print('훈련셋, 검증셋, 테스트셋 분할 완료!')
    return df_train, df_val, df_test

# 데이터셋 읽어오기
df_train, df_val, df_test = get_df()
print(f'훈련셋 개수:{len(df_train)}, 검증셋 개수:{len(df_val)}, 테스트셋 개수: {len(df_test)}') # 192, 48, 60

import torch
from torch.utils.data import Dataset
from PIL import Image

# 학습시, 데이터셋을 사용할 수 있도록 만들기
class Classification_Dataset(Dataset):
    def __init__(self, csv, mode, transform=None):
        self.csv = csv.reset_index(drop=True) # random으로 섞인 데이터의 인덱스를 reset 시켜서 다시 부여한다.
        self.transform = transform

    def __len__(self):
        return self.csv.shape[0] # csv 파일의 행 개수 == 데이터 개수

    def __getitem__(self, index):
        row = self.csv.iloc[index] # 주어진 index에 대한 데이터 뽑아오기
        image = Image.open(row.file_path).convert('RGB') # 파일 경로로 부터 이미지를 읽고 rgb로 변환하기
        target = torch.tensor(self.csv.iloc[index].target).long()

        if self.transform:
            image = self.transform(image) # 이미지에 transform 적용하기

        return image, target # 이미지와 target return하기기


# normalize를 위해 rgb 채널의 mean, std 값 구하기

import numpy as np
from torchvision import transforms
dataset_train = Classification_Dataset(df_train, 'train', transform=transforms.ToTensor())

# 데이터(shape:torch.Size([3, 381, 343])) rgb에 대한 mean, std 구하기
rgb_mean = [np.mean(x.numpy(), axis=(1, 2)) for x, _ in dataset_train]
rgb_std = [np.std(x.numpy(), axis=(1, 2)) for x, _ in dataset_train]

# 각 데이터 채널별로 mean, std 나타내기
c_mean = []
c_std = []
for i in range(3):
    c_mean.append(np.mean([m[i] for m in rgb_mean]))
    c_std.append(np.std([s[i] for s in rgb_std]))

print('rgb의 mean, std값 계산 완료!')
# 사용자 모델 트랜스폼
def get_transforms(image_size):
    transforms_train = transforms.Compose([
        transforms.RandomRotation(30),
        transforms.RandomResizedCrop(image_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(c_mean, c_std)
                             ])

    transforms_val = transforms.Compose([transforms.Resize(image_size + 30),
                                         transforms.CenterCrop(image_size),
                                         transforms.ToTensor(),
                                         transforms.Normalize(c_mean, c_std)])

    return transforms_train, transforms_val

# 모델 트랜스폼 가져오기
transforms_train, transforms_val = get_transforms(224)
print("모델 트랜스폼 불러오기 완료!")

# dataset class 객체 만들기
dataset_train = Classification_Dataset(df_train, 'train', transform=transforms_train)
dataset_val = Classification_Dataset(df_val, 'valid', transform=transforms_val)
print('dataset class 객체 생성 완료!')

# DataLoader는 Classification_Dataset으로 받아온 데이터(이미지, target)를 batch로 묶어 return합니다.
from torch.utils.data.sampler import RandomSampler
from torch.utils.data import DataLoader

train_loader = torch.utils.data.DataLoader(dataset_train, batch_size=4, sampler=RandomSampler(dataset_train), num_workers=0)
valid_loader = torch.utils.data.DataLoader(dataset_val, batch_size=4, num_workers=0)

#### 데이터 준비 파트는 마무리가 되었습니다. 큰 틀을 살펴보면서 정리해보도록 하겠습니다.
# - `0. 데이터셋 다운받기`: 여러분이 수집한 데이터의 클래스별로 폴더를 구성하여 데이터셋을 준비합니다.
# - `1. 데이터셋 구성하기`: 저장한 데이터의 정보를 csv 파일로 만듭니다.
# - `2. 데이터셋 불러오기`: csv 파일을 통해 데이터를 불러와서 train, validation, test로 나눠줍니다.
# - `3. 학습 시, 데이터셋을 사용할 수 있도록 만들기`
#     - `3-1. Dataset Class`: pytorch가 dataset을 어떻게 읽을지 알려주는 클래스를 만듭니다. (데이터셋 크기와 지정한 인덱스별로 데이터를 리턴해주는 len, getitem 함수가 포함되어 있습니다.)
#     - `3-2. Transforms & Augmentation`: 학습을 위해 데이터를 가공합니다.
#     - `3-3. Data Loaders`: 배치별로 데이터를 묶어줍니다. Training시, 배치단위별로 데이터가 호출됩니다.