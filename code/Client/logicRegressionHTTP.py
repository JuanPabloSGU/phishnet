import requests
import json
import numpy as np

# Define the Triton server information
triton_server_url = "http://localhost:8000"  # Update with your Triton server URL
model_name = "logisticalRegression"  # Update with your model name
model_version = "3"  # Update with your model version (or use "1" for the default version)

# Prepare input data for inference (example for a model that expects a single input tensor)

import torchvision.transforms as transforms
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,)),])

inputData = [1.79633761,  2.93382128,  1.34271495,  2.84926993, 1.20037267, 2.45849518, 2.01379278, -0.03411079, -0.0401332, -0.06455833, -0.0175749, 1.2768875, 3.24052795, -0.04366379, -1.55740106]

inputArray = np.array(inputData)
input_data = inputArray.astype(np.float32).tolist()

# Prepare the inference request payload
payload = {
    "inputs": [
        {
            "name": "input",  # Update with your input tensor name
            "shape": [1, 15],  # Update with your input tensor shape
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