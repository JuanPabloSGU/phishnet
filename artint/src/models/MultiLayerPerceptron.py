import torch.nn as nn

class MLP(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size, activation_fn=nn.ReLU, dropout_rate=0.5):
        """
        Initializes the model.

        Parameters:
        input_size (int): Number of input features.
        hidden_layers (list of int): List of sizes for each hidden layer.
        output_size (int): Number of output features.
        activation_fn (torch.nn.modules.activation): Activation function to use after each hidden layer.
        dropout_rate (float): Dropout rate for regularization, value between 0 and 1.
        """
        super(MLP, self).__init__()
        self.layers = nn.ModuleList()

        # Input layer
        self.layers.append(nn.Linear(input_size, hidden_layers[0]))
        self.layers.append(activation_fn())

        # Hidden layers
        for i in range(1, len(hidden_layers)):
            self.layers.append(nn.Linear(hidden_layers[i-1], hidden_layers[i]))
            self.layers.append(activation_fn())
            self.layers.append(nn.Dropout(dropout_rate)) # dropout layer to avoid overfitting

        # Output layer
        self.layers.append(nn.Linear(hidden_layers[-1], output_size))

        # Regression layer
        self.layers.append(nn.Sigmoid())

    def forward(self, x):
        # Forward pass of the model.
        for layer in self.layers:
            x = layer(x)
        return x