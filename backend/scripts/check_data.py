# This file is used to gain information about the database directly
import pandas as pd

df = pd.read_csv("data/spotifydatabase.csv")

print("Before:", len(df))

duplicates = df[df.duplicated("track_id", keep=False)]

print("Duplicate rows:", len(duplicates))
print("Duplicate IDs:", duplicates["track_id"].nunique())

df_clean = df.drop_duplicates(subset="track_id")

print("After:", len(df_clean))

df_clean.to_csv("data/spotifydb_clean.csv", index=False)


'''
print(df.head())
print("\nColumns: ", df.columns)
print("\nShape: ", df.shape)

print(df["tempo"].max())
print(df["tempo"].min())

print(df["loudness"].max())
print(df["loudness"].min())

'''
