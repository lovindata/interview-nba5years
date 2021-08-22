# Import
import numpy as np

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras import backend as K
from tensorflow.keras.optimizers import Adam

import pickle as pkl
import json


# Global variables
EXPECTED = ['GP', 'TOV', 'STL', 'OREB']


# Global functions
to_percentage = lambda x : round(x * 1000) / 10.0


# Class object just for item definition
    # Metrics Keras Format
def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1))) # Optimum theorical threshold on DNN for 0.5
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1))) # Optimum theorical threshold on DNN for 0.5
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))


# Main Class
class DnnModel:

    ## Init
    def __init__(self):
        self.cpu_model = None
        self.scale_mod = None

        self.decision_threshold = None
        self.mean_precision = None
        self.threestd_precision = None

    ## Get Dense Neuronal Network
    def load_dnn(self, pathmod='./resources/models/dnn_nba.h5'):
        ### Define architecture
        input_mod = Input((len(EXPECTED)))
        layer_mod = Dense(len(EXPECTED), activation='relu')(input_mod)
        layer_mod = Dense(4, activation='relu')(layer_mod)
        output_mod = Dense(1, activation = 'sigmoid')(layer_mod)
        
        model = Model(inputs=input_mod, outputs=output_mod)
        
        opt_adam = Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07)
        model.compile(opt_adam, loss='binary_crossentropy', metrics=[recall_m, precision_m, f1_m, 'accuracy'])
        
        ### Load & Add weights
        model.load_weights(pathmod)
        self.cpu_model = model

    def load_scaler(self, pathsca='./resources/models/scaler.pkl'):
        ### Load neural network & Scaler when the REST API boots up
        with open(pathsca, 'rb') as f1:
            self.scale_mod = pkl.load(f1)

    def load_metadata(self, pathmeta='./resources/models/metadata_nba.json'):
        with open(pathmeta, 'rb') as f1:
            metadata_nba = json.load(f1)
            self.decision_threshold = to_percentage(metadata_nba['decision_threshold'])
            self.mean_precision = to_percentage(metadata_nba['mean_precision'])
            self.threestd_precision = to_percentage(3 * metadata_nba['std_precision'])
        return None

    ## Load weights on the model
    def get_predict(self, feature):
        feature = np.array(feature).reshape((1,-1))
        feature = self.scale_mod.transform(feature) # Normalize the data
        probability_TARGET_5Yrs = to_percentage(self.cpu_model.predict(feature).flatten()[0])
        tARGET_5Yrs = probability_TARGET_5Yrs > self.decision_threshold
        return {'TARGET_5Yrs': tARGET_5Yrs, 'TARGET_5Yrs_probability': probability_TARGET_5Yrs, 'decision_threshold': self.decision_threshold, 'correctness': self.mean_precision, 'correctness_variability': self.threestd_precision}