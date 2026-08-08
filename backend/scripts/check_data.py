import pandas as pd

df = pd.read_csv("data/spotifydatabase.csv")

duplicate_rows = df[df["track_id"].duplicated(keep=False)]
duplicate_counts = df["track_id"].value_counts()

print(duplicate_rows[["track_id", "track_name", "artists"]].head(20))
print(f"Duplicate rows: {len(duplicate_rows)}")
print(f"Unique duplicate IDs: {duplicate_rows['track_id'].nunique()}")
print(duplicate_counts[duplicate_counts > 1].head(20))

'''
print(df.head())
print("\nColumns: ", df.columns)
print("\nShape: ", df.shape)
'''