# phishnet

This README.md goes through the needed model-repository structure and how to run the triton server inference.

## Structure

Starting with the structure with the following:

<model-repository-path>/
  <model-name>/
    [config.pbtxt]
    [<output-labels-file> ...]
    <version>/
      <model-definition-file>
    <version>/
      <model-definition-file>
**This strucuture comes directly from https://docs.nvidia.com/deeplearning/triton-inference-server/archives/triton_inference_server_1150/user-guide/docs/model_repository.html

It is important to note that model-name should not have the same name as the saved onnx model file.

## Running commands for triton server

Start by running docker, then you can run the following terminal command inside the 'code' folder.

(Windows) 
docker run --rm -p8000:8000 -p8001:8001 -p8002:8002 -v %cd%/model-repository:/models nvcr.io/nvidia/tritonserver:24.01-py3 tritonserver --model-repository=/models

(Linux)
docker run --rm -p8000:8000 -p8001:8001 -p8002:8002 -v ${PWD}/model-repository:/models nvcr.io/nvidia/tritonserver:24.01-py3 tritonserver --model-repository=/models

The terminal should show that testModel has the READY status