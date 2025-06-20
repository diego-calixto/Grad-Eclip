from PIL import Image
import os
import pandas as pd
import os
from PIL import Image
import torch
from torch.utils.data import Dataset
import utils
device = "cuda:0" if torch.cuda.is_available() else "cpu"
            

class Rival10Challenge(Dataset):

    def __init__(self, challenge_type, root_dir, split, transform=None):
        self.challenge_type = challenge_type
        self.root_dir = root_dir
        self.split = split
        self.folder2catid = {
            'truck': 0,
            'car': 1,
            'plane': 2,
            'ship': 3,
            'cat': 4,
            'dog': 5,
            'equine': 6,
            'deer': 7,
            'frog': 8,
            'bird': 9,
        }
        self.catid2folder = {
            self.folder2catid[cls]: cls 
            for cls in self.folder2catid.keys()
            }
        self.imgs = []
        self.transform = transform
        self.original_img_name = []
        self.load_images()        

    def load_images(self):
        challenge_path = os.path.join(self.root_dir, self.challenge_type, self.split)
        for category in sorted(os.listdir(challenge_path)):
            cat_path = os.path.join(challenge_path, category)
            for file in sorted(os.listdir(cat_path)):
                assert file.endswith('.JPEG')
                img_path = os.path.join(cat_path, file)
                img_label = self.folder2catid[category]
                self.imgs.append((img_path, img_label))
                self.original_img_name.append(file.split('-')[0])

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        path, label = self.imgs[idx]
        img = Image.open(path)

        if self.transform is not None:
            img = self.transform(img)

        return img, label
    

class Rival10AllChallenges(Dataset):

    def __init__(self, root_dir, split, transform=None):
        self.challenges = [
            "original", 
            "mixed-same", 
            "mixed-rand", 
            "mixed-next", 
            "only-fg", 
            #"only-bg"
            ] 
        self.root_dir = root_dir
        self.split = split
        self.challenge2dataset = {
            cha: Rival10Challenge(cha, root_dir, split, transform)
            for cha in self.challenges
            }
        self.folder2catid = self.challenge2dataset[self.challenges[0]].folder2catid
        self.catid2folder = self.challenge2dataset[self.challenges[0]].catid2folder
        
    def __len__(self):
        return len(self.challenge2dataset[self.challenges[0]])

    def __getitem__(self, idx):
        output = {}
        for cha in self.challenge2dataset.keys():
            img, label = self.challenge2dataset[cha][idx]
            output[cha.replace('-', '_')] = img
        output['label'] = label

        return output


if __name__ == "__main__":

    data = Rival10Challenge(
        challenge_type="ordinary",
        root_dir="./RIVAL10-Diego",
        split="test"
    )



    # int_method = ["selfattn", "gradcam", "maskclip", "eclip", "game", "rollout", "surgery", "m2ib", "rise"]
    int_method_list =  ["selfattn", "gradcam", "maskclip", "eclip", "game", "rollout", "surgery", "m2ib", "rise"]

    log = {
        'img_id': [],
        'interpretability_method': [],
        'label': [],
        'similarity_original': [],
        'similarity_perturb': [],
        'hm_original': [],
        'hm_perturbed': [],
        'alpha': [],
        'clip_model': []
    }
    for idx in range(10):
        image, label = data[idx]
        print(label)
        for int_method in int_method_list:
            similarity_original, similarity_perturbed, hm_original, hm_perturbed = utils.analysis_pertub(image, utils.to_prompt(label), int_method)
            log['img_id'].append(idx)
            log['interpretability_method'].append(int_method)
            log['label'].append(label)
            log['similarity_original'].append(similarity_original)
            log['similarity_perturb'].append(similarity_perturbed)
            log['hm_original'].append(hm_original.detach().cpu())
            log['hm_perturbed'].append(hm_perturbed.detach().cpu())
            log['alpha'].append(8/255)
            log['clip_model'].append("ViT-B/16")
            print(int_method)
    pd.DataFrame.from_dict(log).to_pickle("./results")    