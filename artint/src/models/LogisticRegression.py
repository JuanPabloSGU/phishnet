import numpy as np
import torch.nn as nn
from sklearn.linear_model import LogisticRegression

class LogisticRegressionBase:
    def __init__(self, X_train, Y_train, X_test, Y_test, num_epochs=2000, learning_rate=0.005) -> None:
        self.X_train = X_train
        self.Y_train = Y_train
        self.X_test = X_test
        self.Y_test = Y_test
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate

    def activation(self, x):
        return 1 / (1 + np.exp(-x)) # sigmoid
    
    def cost(self, A, Y, n):
        return (- 1 / n) * np.sum(Y * np.log(A) + (1 - Y) * np.log(1 - A)) # negative log likelihood

    # initialize parameters
    def init_params(d):
        return np.zeros((d, 1)), 0

    # compute activation, error and gradients
    def propagate(self, w, b, X, Y):
        n = X.shape[1]
        # forward propagation
        A = self.activation(np.dot(w.T, X) + b)
        cost = self.cost(A, Y, n)
        # gradient computations
        dw = (-1/n) * np.dot(X, (Y-A).T)
        db = (-1/n) * np.sum(Y-A)
        return dw, db, cost

    # gradient descent on weights and bias
    def optimize(self, w, b, X, Y):
        costs = []
        for epoch in range(self.num_epochs):
            dw, db, cost = self.propagate(w, b, X, Y)
            w, b = w - self.learning_rate * dw, b - self.learning_rate * db
            if epoch % 500 == 0:
                costs.append(cost)
                print('Epoch {num}, Cost {cost}'.format(num=epoch, cost=cost))
        return w, b, costs

    # return vector of predictions 
    def predict(self, w, b, X):
        w = w.reshape(X.shape[0], 1)
        A = self.activation(np.dot(w.T, X) + b)
        Y_pred = np.zeros((1, X.shape[1]))
        for idx in range(Y_pred.shape[1]):
            Y_pred[0, idx] = 1 if A[0, idx] > 0.5 else 0 # thresholding
        return Y_pred
    
    # single neuron model with alpha=0.005 and 2000 epochs
    def model(self):
        w, b = self.init_params(self.X_train.shape[0])
        w_opt, b_opt, costs = self.optimize(w, b, self.X_train, self.Y_train)
        Y_pred_train = self.predict(w_opt, b_opt, self.X_train)
        Y_pred_test = self.predict(w_opt, b_opt, self.X_test)

        print("train accuracy: {} %".format(100 - np.mean(np.abs(Y_pred_train - self.Y_train)) * 100))
        print("test accuracy: {} %".format(100 - np.mean(np.abs(Y_pred_test - self.Y_test)) * 100))
        
        return {
            'learning_rate': self.learning_rate, 
            'epoch_num': self.num_epochs,
            'w': w_opt,
            'b': b_opt,
            "costs": costs,
            'Y_pred_train': Y_pred_train,
            'Y_pred_test': Y_pred_test
        }

class LogisticRegressionPytorch(nn.Module):
    def __init__(self, input_size):
        super(LogisticRegressionPytorch, self).__init__()
        self.linear = nn.Linear(input_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out = self.linear(x)
        out = self.sigmoid(out)
        return out
