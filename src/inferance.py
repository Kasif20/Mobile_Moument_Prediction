import pickle
import train 
import sys, time
import uvicorn
import logging 
import pandas as pd 
from lightgbm import LGBMClassifier
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(name=__name__)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fmt=formatter)
logger = logging.getLogger(name=__name__)
logger.setLevel(level=logging.INFO)
logger.addHandler(hdlr=handler)

for name in logging.root.manager.loggerDict:
    if name in ("uvicorn"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(hdlr=handler)
        uvicorn_logger.setLevel(level=logging.INFO)

app = FastAPI(title="Basic Pridection ")

class indata(BaseModel):
    data:list[list[float]]

def load_model():
    ls = pickle.load(open("./model/lgbm.sav","rb"))
    ms = pickle.load(open("./model/stdscaler.sav","rb"))
    return (ls,ms)

def output(inferation):
    inferation = int(pd.Series(inferation).mode()[0])
    swither={
        0:"Downstairs",
        1:"Jogging",
        2:"Sitting",
        3:"Standing",
        4:"Upstair",
        5:"Walking"
    } 
    return {
            "value":inferation,
            "prediction":swither.get(inferation,"Unknown")
    }

# need to inplement error handling sync between phone and pc or anything that can help me to have more accurate 
@app.post("/infer/")
def infer(m:indata):
    time.sleep(2)# <- this !!!
    if not m.data:
        logger.error("Empty Data to be used for DataFrame")
        return HTTPException(status_code=400,detail="Missing Data in DataFrame")

    indata = pd.DataFrame(m.data,columns = ['timestamp','acc_x', 'acc_y', 'acc_z']) #check data integrety and send httpException also increse time on moblie side
    indata = indata[['acc_x', 'acc_y', 'acc_z','timestamp']]

    logger.info("Data Recived Succecfully and Converted to DataFrame")
    print(f"this ->> {indata} <<-")

    #logger.info(f"The Head of the data is {indata.head()}")

    indata = indata.drop(columns = ['timestamp'])
    print(f"this ->> {indata} <<-")

    indata = train.feature_engineering(indata)
    print(f"this ->> {indata} <<-")
    (ls,ms) = load_model()
    logger.info("Loaded Model Succecfully and sending prediction")
    return output(ls.predict(ms.transform(indata)))

if __name__=="__main__":
    uvicorn.run("inferance:app",host="0.0.0.0",port=8000,log_config=None)#log_level="info")
