import requests
import json
import numpy as np

# Define the Triton server information
triton_server_url = "http://localhost:8000"  # Update with your Triton server URL
model_name = "testModel"  # Update with your model name
model_version = "1"  # Update with your model version (or use "1" for the default version)

# Prepare input data for inference (example for a model that expects a single input tensor)
import torchvision.datasets as datasets
import torchvision.transforms as transforms
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,)),])
mnist_testset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

inputArray = np.array(mnist_testset[0][0][0])
input_data = inputArray.astype(np.float32).tolist()

# Prepare the inference request payload
payload = {
    "inputs": [
        {
            "name": "input",  # Update with your input tensor name
            "shape": [1, 1, 28, 28],  # Update with your input tensor shape
            "datatype": "FP32",  # Update with your input tensor data type
            "data": input_data
        }
    ]
}

# Define the inference request URL
inference_url = f"{triton_server_url}/v2/models/{model_name}/infer"

# Make the HTTP POST request for inference
response = requests.post(
    inference_url,
    data=json.dumps(payload),
    headers={"Inference-Header": "your_custom_header"},  # Add any custom headers if needed
)

# Parse and print the inference result
if response.status_code == 200:
    result = response.json()
    print("Inference Result:", result)
else:
    print("Error during inference. Status code:", response.status_code)
    print("Error details:", response.text)