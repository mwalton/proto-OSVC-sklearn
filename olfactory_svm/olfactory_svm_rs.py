# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 16:41:42 2014

@author: michaelwalton
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
import pylab as pl

from sklearn import svm
from sklearn.preprocessing import StandardScaler
from sklearn.cross_validation import StratifiedKFold
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
#this is set up as a multiclass problem, could maybe modify to a multilabel
#problem and then treat the p(label) as a prediciton / reproduction of the
#odorant concentration, this would be really cool if that representation works

class RSA:
    def __init__(self, latencyScale, sigmoidRate, normalizeSpikes, maxLatency, maxSpikes):
        self.latencyScale = latencyScale
        self.sigmoidRate = sigmoidRate
        self.maxSpikes = maxSpikes
        self.maxLatency = maxLatency
        self.normalizeSpikes = normalizeSpikes
        self.desensitize = False
    
    def spikeLatencies(self, X):
        if (self.desensitize):
            latency = X
        else:
            if (self.sigmoidRate):
                rate = 1.0/(1.0 + np.exp(-(X-0.5)*10.0))
                latency = self.latencyScale / rate
            else:
                latency = self.latencyScale / X
        # find all values greater than maxL and set to maxL
        maxed = latency > self.maxLatency
        latency[maxed] = self.maxLatency
        return latency
        
    def countNspikes(self, X):
        #round latency to nearest int and set 0 <- 1        
        latency = np.round(self.spikeLatencies(X), 0)
        minL = latency <= 0.0
        latency[minL] = 1.0
        
        #intergrationWindow = np.ones(latency.shape[0])
        totalSpikes = np.zeros(latency.shape[0])
        spikeTrain = np.zeros(latency.shape)

        for i in range(latency.shape[0]):
            for j in range(self.maxLatency):
                spikeEmitted = ((j + 1) % latency[i] == 0)
                notMax = latency[i] < self.maxLatency
                
                spikeIdx = np.bitwise_and(spikeEmitted, notMax)
                
                spikeTrain[i][spikeIdx] += 1
                totalSpikes[i] += np.sum(spikeIdx)
                if (totalSpikes[i] >= self.maxSpikes): break

        if (self.normalizeSpikes):
            spikeScale = np.ones(totalSpikes.shape)
            spikesEmitted = totalSpikes > 0.0            
            spikeScale[spikesEmitted] = self.maxSpikes / totalSpikes[spikesEmitted]          
            spikeTrain = np.transpose(spikeScale * np.transpose(spikeTrain))
            
        return spikeTrain
                
def enum(**enums):
    return type('Enum', (), enums)

ExperimentTypes = enum(NoBgTrain_NoBg_test = 0, BgTrain_BgTest = 1, NoBgTrain_BgTest = 2, RS_NoBgTrain_NoBg_test = 3, RS_BgTrain_BgTest = 4, RS_NoBgTrain_BgTest = 5)

target_names = ['red', 'green', 'blue', 'yellow']
exp = ExperimentTypes.NoBgTrain_NoBg_test
standardize = True
tuneHyperparams = True
doRsa = False

###############################################################################
# Pick a dataset
# As the project grows, this should be replaced by a line arg.
# to set a containing folder then run on the data in that dir
if (exp == ExperimentTypes.NoBgTrain_NoBg_test):
    train_conc_file = "data/Otrain_4Otest/train_c.csv"
    train_actv_file = "data/Otrain_4Otest/train_a.csv"
    test_conc_file = "data/Otrain_4Otest/test_c.csv"
    test_actv_file = "data/Otrain_4Otest/test_a.csv"
elif (exp == ExperimentTypes.BgTrain_BgTest):
    train_conc_file = "data/OBGtrain_4OBGtest/train_c.csv"
    train_actv_file = "data/OBGtrain_4OBGtest/train_a.csv"
    test_conc_file = "data/OBGtrain_4OBGtest/test_c.csv"
    test_actv_file = "data/OBGtrain_4OBGtest/test_a.csv"
elif (exp == ExperimentTypes.NoBgTrain_BgTest):
    train_conc_file = "data/Otrain_4OBGtest/train_c.csv"
    train_actv_file = "data/Otrain_4OBGtest/train_a.csv"
    test_conc_file = "data/Otrain_4OBGtest/test_c.csv"
    test_actv_file = "data/Otrain_4OBGtest/test_a.csv"
elif (exp == ExperimentTypes.RS_NoBgTrain_NoBg_test):
    train_conc_file = "data/Otrain_4Otest/train_c.csv"
    train_actv_file = "data/Otrain_4Otest/train_a_rs.csv"
    test_conc_file = "data/Otrain_4Otest/test_c.csv"
    test_actv_file = "data/Otrain_4Otest/test_a_rs.csv"
elif (exp == ExperimentTypes.RS_BgTrain_BgTest):
    train_conc_file = "data/OBGtrain_4OBGtest/train_c.csv"
    train_actv_file = "data/OBGtrain_4OBGtest/train_a_rs.csv"
    test_conc_file = "data/OBGtrain_4OBGtest/test_c.csv"
    test_actv_file = "data/OBGtrain_4OBGtest/test_a_rs.csv"
elif (exp == ExperimentTypes.RS_NoBgTrain_BgTest):
    train_conc_file = "data/Otrain_4OBGtest/train_c.csv"
    train_actv_file = "data/Otrain_4OBGtest/train_a_rs.csv"
    test_conc_file = "data/Otrain_4OBGtest/test_c.csv"
    test_actv_file = "data/Otrain_4OBGtest/test_a_rs.csv"

###############################################################################
#load data
reader = csv.reader(open(train_conc_file,"rb"), delimiter=",")
x = list(reader)
train_c = np.array(x).astype('float')

reader = csv.reader(open(train_actv_file,"rb"), delimiter=",")
x = list(reader)
train_a = np.array(x).astype('float')

reader = csv.reader(open(test_conc_file,"rb"), delimiter=",")
x = list(reader)
test_c = np.array(x).astype('float')

reader = csv.reader(open(test_actv_file,"rb"), delimiter=",")
x = list(reader)
test_a = np.array(x).astype('float')

###############################################################################
# Convert the concentration labels to classes
train_target = np.argmax(train_c, axis=1)
test_target = np.argmax(test_c, axis=1)

###############################################################################
# Data Pre-processing
if (doRsa):
    rsa = RSA(latencyScale=100, sigmoidRate=False, normalizeSpikes=True, maxLatency=1000, maxSpikes=20)
    train_a = rsa.countNspikes(train_a)
    test_a = rsa.countNspikes(test_a)

if (standardize):
    scaler = StandardScaler()
    train_a = scaler.fit_transform(train_a)
    test_a = scaler.transform(test_a)
    
###############################################################################
# Train the classifier
# if tuneHyperparams, estimate optimal params via grid search
# using stratified k-folds cross validation

if (tuneHyperparams):
    #set the parameter grid
  
    param_grid = [{'kernel': ['rbf'], 'gamma': [1e-1, 1e-5],
                     'C': [1, 10, 100, 1000]},
                    {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}]

    #kernel_range = ['rbf', 'linear', 'poly', 'sigmoid']
    #gamma_range = np.arange(start=1e-3, stop=1e-1, step=1e-3)
    #C_range = np.arange(1,1000)
    #param_grid = dict(gamma=gamma_range, C=C_range)
    #configure stratified k-fold cross validation, run grid search                    
    cv = StratifiedKFold(y=train_target, n_folds=3, shuffle=True)
    grid = GridSearchCV(svm.SVC(C=1), param_grid=param_grid, cv=cv)
    grid.fit(train_a, train_target)
    print("Best Classifier: %s" % grid.best_estimator_)
    clf = grid.best_estimator_
    
    """    
    #visualize the resulting grid
    score_dict = grid.grid_scores_
    scores = [z[1] for z in score_dict]
    scores = np.array(scores).reshape(, len(gamma_range))
    pl.figure(10)
    pl.imshow(scores, interpolation='nearest', cmap=pl.cm.spectral)
    pl.xlabel('gamma')
    pl.ylabel('C')
    pl.colorbar()
    pl.show()
    """
else:
    clf = svm.SVC()
    clf.fit(train_a, train_target)

# run the prediction
pred = clf.predict(test_a)

###############################################################################
#PLOT DATA

#plot imported data and target
pl.figure(1)
plt.plot(train_c)
plt.title('Training (Odorant Concentration)')
plt.ylabel('Concentration')
plt.xlabel('Time')
plt.show()

pl.figure(2)
plt.plot(test_c)
plt.title('Testing (Odorant Concentration)')
plt.ylabel('Concentration')
plt.xlabel('Time')
plt.show()

pl.figure(3, figsize=(6,6))
plt.imshow(np.transpose(train_a))
#plt.colorbar()
plt.title('Training (Sensor Pattern)')
plt.ylabel('Activation')
plt.xlabel('Time')
plt.show()

pl.figure(6)
plt.imshow(np.transpose(test_a))
#plt.colorbar()
plt.title('Testing (Sensor Pattern)')
plt.ylabel('Activation')
plt.xlabel('Time')
plt.show()

#show confusion matrix
cm = confusion_matrix(test_target, pred)
pl.figure(7)
plt.matshow(cm)
plt.colorbar()
plt.title('SVC')
plt.ylabel('Target label')
plt.xlabel('Predicted label')
plt.show()

print(classification_report(test_target, pred, target_names=target_names))
print("Accuracy Score: %s" % accuracy_score(test_target, pred))
#print("AP", average_precision_score(test_target, pred))