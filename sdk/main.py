import dataloader

if __name__ == "__main__":
    df = dataloader.get("flights")
    print(df.limit(5).collect())
