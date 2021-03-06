#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import tensorflow as tf

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0' 

def create_dataset(dataset):
    dataX, dataY = [], []
    for i in range(len(dataset)-1):
        dataX.append(dataset[i])
        dataY.append(dataset[i + 1])
    return np.asarray(dataX), np.asarray(dataY)

# Fix random seed for reproducibility
np.random.seed(7)

# Import data
data = pd.read_json('data/bitcoin_usdt_1m.json', orient='split')
data = data.iloc[:-11]

# Drop date variable
data = data.drop(['time','time_close','ignore','open','lo','hi','volume','quote_volume','trades','buy_base','buy_quote'], axis=1)

# Go girl
dataset = data.values
dataset = dataset.astype('float32')

# normalize the dataset
scaler = MinMaxScaler(feature_range=(0, 1))
dataset = scaler.fit_transform(dataset)

#prepare the X and Y label
X,y = create_dataset(dataset)

#Take 80% of data as the training sample and 20% as testing sample
trainX, testX, trainY, testY = train_test_split(X, y, test_size=0.20, shuffle=False)

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

print(testX.shape)

sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

# create and fit the LSTM network
model = Sequential()
model.add(LSTM(4, input_shape=(1, 1)))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')

try:
    model = load_model('./.lstm_checkpoints/future_model')
except:
    pass
model.fit(trainX, trainY, epochs=1, batch_size=1, verbose=3)
model.save('./.lstm_checkpoints/future_model')

# make predictions
# trainPredict = model.predict(trainX)
testPredict = model.predict(testX)

#high_festiva
futX = np.reshape(testPredict, (testPredict.shape[0], 1, testPredict.shape[1]))
futX = futX[-256:]
futurePredict = model.predict(futX)
# futurePredict = model.predict(np.asarray([[y[-1]]]))
futurePredict = scaler.inverse_transform(futurePredict)

# invert predictions
# trainPredict = scaler.inverse_transform(trainPredict)
# trainY = scaler.inverse_transform(trainY)
testPredict = scaler.inverse_transform(testPredict)
testY = scaler.inverse_transform(testY)

print("Price for last 5 ticks: ")
print(testPredict[-5:])
print("Bitcoin price for next tick: ", futurePredict[-1])

# calculate root mean squared error
# trainScore = np.sqrt(mean_squared_error(trainY[:,0], trainPredict[:,0]))
# print('Train Score: %.2f RMSE' % (trainScore))
testScore = np.sqrt(mean_squared_error(testY[:,0], testPredict[:,0]))
print('Test Score: %.2f RMSE' % (testScore))

# shift train predictions for plotting
# trainPredictPlot = np.empty_like(dataset)
# trainPredictPlot[:, :] = np.nan
# trainPredictPlot[1:len(trainPredict)+1, :] = trainPredict

# shift test predictions for plotting
testPredictPlot = np.empty_like(dataset)
testPredictPlot[:, :] = np.nan
testPredictPlot[len(trainX):len(dataset)-1, :] = testPredict
print(len(testPredictPlot))

futurePlot = np.empty_like(testPredictPlot)
futurePlot[:, :] = np.nan
futurePlot[len(testPredictPlot)-256:len(testPredictPlot), :] = futurePredict

# plot baseline and predictions
plt.plot(scaler.inverse_transform(dataset))
# plt.plot(trainPredictPlot)
plt.plot(testPredictPlot)
plt.plot(futurePlot)
plt.show()
