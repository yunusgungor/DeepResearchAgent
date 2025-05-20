import os
import pandas as pd
import datasets

from src.utils import assemble_project_path

def preprocess_file_paths(row, path, split):
    save_path = assemble_project_path(os.path.join(path, "2023", split))
    os.makedirs(save_path, exist_ok=True)
    if len(row["file_name"]) > 0:
        row["file_name"] = os.path.join(save_path, row["file_name"])
    return row

class GAIADataset():
    def __init__(self, path, name, split):
        self.path = path
        self.name = name
        self.split = split
        
        ds = datasets.load_dataset(path, name, trust_remote_code=True)[split]
        ds = ds.rename_columns({"Question": "question", "Final answer": "true_answer", "Level": "task"})
        ds = ds.map(preprocess_file_paths, fn_kwargs={"split": split, "path": path})
        data = pd.DataFrame(ds)
        
        self.data = data
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, index):
        return self.data.iloc[index]

