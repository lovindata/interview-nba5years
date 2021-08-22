import traceback

from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

from tensorflow.python.ops.numpy_ops.np_math_ops import true_divide
from tensorflow.python.platform.tf_logging import error
from model import DnnModel


app = FastAPI()
dnnmodel = DnnModel()
dnnmodel.load_dnn()
dnnmodel.load_scaler()
dnnmodel.load_metadata()


class Input(BaseModel):
    game_played: float
    turnover: float
    steal: float
    offensive_rebounds: float


class Output(BaseModel):
    request_id: str = None
    TARGET_5Yrs: float = None
    TARGET_5Yrs_probability: float = None
    decision_threshold: float = None
    correctness: float = None
    correctness_variability: float = None
    errors: List = []


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/{request_id}", response_model=Output)
def get_prediciton(request_id: str, request_model: Input):
    
    response = Output()
    response.request_id = request_id

    try:
        input = [request_model.game_played, request_model.turnover, request_model.steal, request_model.offensive_rebounds]
        output = dnnmodel.get_predict(input)

        response.TARGET_5Yrs = output['TARGET_5Yrs']
        response.TARGET_5Yrs_probability = output['TARGET_5Yrs_probability']
        response.decision_threshold = output['decision_threshold']
        response.correctness = output['correctness']
        response.correctness_variability = output['correctness_variability']
    except:
        response.errors.append(traceback.format_exc())

    return response
