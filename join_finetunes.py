
import pandas as pd
import glob
files = glob.glob('.cache/ontology/*.parquet')
print(len(files))

all_df = []
for file in files:
    df = pd.read_parquet(file)
    all_df.append(df)

df = pd.concat(all_df)
df = df.drop_duplicates()
# suppress records where input is None
df = df[df['input'].notnull()]
df = df.reset_index(drop=True)
df.to_parquet('.cache/ontology.parquet')

from datasets import Dataset

dataset = Dataset.from_pandas(df)

dataset.push_to_hub('sebdg/ontology')