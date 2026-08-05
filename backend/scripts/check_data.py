import pandas as pd

df = pd.read_csv("data/spotifydatabase.csv")

print(df.head())
print("\nColumns: ", df.columns)
print("\nShape: ", df.shape)