import pandas as pd
from sqlalchemy import create_engine
import os 
from urllib.parse import quote_plus


def main():
    name = os.getenv('DB_USER')
    passward = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = 3306
    db = os.getenv('DB_NAME')

    url = f"mysql+pymysql://{name}:{quote_plus(passward)}@{host}:{port}/{db}?charset=utf8mb4"
    engine = create_engine(url,pool_pre_ping=True,echo=True)

    train_df = pd.read_csv("train.csv")
    print(train_df.head())
    print(train_df.info())

    train_df.to_sql(
        name="train",
        con=engine,
        if_exists = "append",
        index = False
    )

    test_df = pd.read_csv("test.csv")
    print(test_df.head())
    print(test_df.info())

    test_df.to_sql(
        name="test",
        con=engine,
        if_exists = "append",
        index = False
    )


if __name__ == "__main__":
    main()
