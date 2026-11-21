import pandas as pd
import numpy as np
import pickle
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import MinMaxScaler, StandardScaler, OneHotEncoder
from sklearn.tree import DecisionTreeClassifier 
from sklearn.ensemble import RandomForestClassifier 
from imblearn.under_sampling import RandomUnderSampler
from lightgbm import LGBMClassifier

def db_load_data():
    name = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = 3306
    db = os.getenv('DB_NAME')
    try:
        url = f"mysql+pymysql://{name}:{quote_plus(password)}@{host}:{port}/{db}?charset=utf8mb4"
        engine = create_engine(url,echo=True,pool_pre_ping=True)
        Train_df = pd.read_sql(
        "train",
        engine
        )
        Test_df = pd.read_sql(
            "test",
            engine
        )
        return (Train_df,Test_df)
    except Exception as e:
        print(f"Connecting to db failed due to {e}")
        return None

def feature_engineering(df):
    df['mgs'] = (df['acc_x']**2+df['acc_y']**2+df['acc_z']**2)**0.5 
    df['sma'] = df['acc_x'].abs()+df['acc_y'].abs()+df['acc_z'].abs()
    
    window = 10
    for col in ['acc_x','acc_y','acc_z']:
        df[f'{col}_rol_mean'] = df[col].rolling(window).mean()
        df[f'{col}_rol_std'] = df[col].rolling(window).std()
        df[f'{col}_rol_min'] = df[col].rolling(window).min()
        df[f'{col}_rol_max'] = df[col].rolling(window).max()

    df['xy_corr'] = df['acc_x'].rolling(window).corr(df['acc_y'])
    df['xz_corr'] = df['acc_x'].rolling(window).corr(df['acc_z'])
    df['yz_corr'] = df['acc_y'].rolling(window).corr(df['acc_z'])
    
    df = df.replace([np.inf,-np.inf],np.nan)
    df = df.dropna()
    df = df.reset_index(drop=True)
    
    return df
   

def LGBM(X_train,y_train,X_test,y_test):
    ls = LGBMClassifier(n_estimators=100,max_depth=8,learning_rate=0.1,class_weight="balanced")
    ls.fit(X_train,y_train)
    y_pred = ls.predict(X_test)
    #print(y_pred)

    pickle.dump(ls,open("./model/lgbm.sav","wb")) 
    print(f'LGBMClassifier f1 = {f1_score(y_test,y_pred,average="weighted")}')
    print("\n confusion_matrix :-")
    print(confusion_matrix(y_test,y_pred))
    print("\n classification_report :-")
    print(classification_report(y_test,y_pred))
    print("\n Model saved at ./model/lgbm.sav")

def Scaler(X_train,X_test):
    ms = StandardScaler().set_output(transform="pandas")
    X_train = ms.fit_transform(X_train)
    X_test = ms.transform(X_test)
    pickle.dump(ms,open("./model/stdscaler.sav","wb"))
    print("dumping StandardScaler")
    return (X_train,X_test)

def process_df(df):
    print("\n Data Loaded from DataBase Frist 5 rows are :-")
    print(df.head())
    df = feature_engineering(df)
    df.columns = [str(col) for col in df.columns] # sqlalchemy gives quoted_name obj subclass of str which sklearn requires 

    X = df.drop(columns=['timestamp','Activity'])
    y = df['Activity']
    return (X,y)
    
def main():
    (df,df2) = db_load_data()
    if df is None or df2 is None: # find diffrence between == and is for dataframe in this case 
        return -1
    (X_train,y_train) = process_df(df)
    (X_test,y_test) = process_df(df2)
    #X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.3,random_state=42)
    (X_train,X_test) = Scaler(X_train,X_test)
    rus = RandomUnderSampler(random_state=42)
    X_train,y_train = rus.fit_resample(X_train,y_train)
    LGBM(X_train,y_train,X_test,y_test)
    
if __name__ == "__main__":
    main()
    
