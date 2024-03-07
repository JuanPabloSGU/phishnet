import argparse
import sys

import gevent.ssl
import numpy as np
import tritonclient.http as httpclient
from tritonclient.utils import InferenceServerException

import torchvision.datasets as datasets
import torchvision.transforms as transforms
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,)),])
mnist_testset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
#print(mnist_testset[0])

def test_infer(
    model_name,
    headers=None,
    request_compression_algorithm=None,
    response_compression_algorithm=None,
):
    inputs = []
    outputs = []
    inputs.append(httpclient.InferInput("input", np.array(mnist_testset[0][0][0]).tolist(), "float32"))

    # Initialize the data
    #inputs[0].set_data_from_numpy(input0_data, binary_data=False)
    
    outputs.append(httpclient.InferRequestedOutput("output", binary_data=True))
    query_params = {"test_1": 1}
    results = triton_client.infer(
        model_name,
        inputs=inputs,
        outputs=outputs,
        query_params=query_params,
        headers=headers,
        request_compression_algorithm=request_compression_algorithm,
        response_compression_algorithm=response_compression_algorithm,
    )

    return results



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        default=False,
        help="Enable verbose output",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        required=False,
        default="localhost:8000",
        help="Inference server URL. Default is localhost:8000.",
    )
    parser.add_argument(
        "-s",
        "--ssl",
        action="store_true",
        required=False,
        default=False,
        help="Enable encrypted link to the server using HTTPS",
    )
    parser.add_argument(
        "--key-file",
        type=str,
        required=False,
        default=None,
        help="File holding client private key. Default is None.",
    )
    parser.add_argument(
        "--cert-file",
        type=str,
        required=False,
        default=None,
        help="File holding client certificate. Default is None.",
    )
    parser.add_argument(
        "--ca-certs",
        type=str,
        required=False,
        default=None,
        help="File holding ca certificate. Default is None.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        required=False,
        default=False,
        help="Use no peer verification in SSL communications. Use with caution. Default is False.",
    )
    parser.add_argument(
        "-H",
        dest="http_headers",
        metavar="HTTP_HEADER",
        required=False,
        action="append",
        help="HTTP headers to add to inference server requests. "
        + 'Format is -H"Header:Value".',
    )
    parser.add_argument(
        "--request-compression-algorithm",
        type=str,
        required=False,
        default=None,
        help="The compression algorithm to be used when sending request body to server. Default is None.",
    )
    parser.add_argument(
        "--response-compression-algorithm",
        type=str,
        required=False,
        default=None,
        help="The compression algorithm to be used when receiving response body from server. Default is None.",
    )

    FLAGS = parser.parse_args()
    try:
        if FLAGS.ssl:
            ssl_options = {}
            if FLAGS.key_file is not None:
                ssl_options["keyfile"] = FLAGS.key_file
            if FLAGS.cert_file is not None:
                ssl_options["certfile"] = FLAGS.cert_file
            if FLAGS.ca_certs is not None:
                ssl_options["ca_certs"] = FLAGS.ca_certs
            ssl_context_factory = None
            if FLAGS.insecure:
                ssl_context_factory = gevent.ssl._create_unverified_context
            triton_client = httpclient.InferenceServerClient(
                url=FLAGS.url,
                verbose=FLAGS.verbose,
                ssl=True,
                ssl_options=ssl_options,
                insecure=FLAGS.insecure,
                ssl_context_factory=ssl_context_factory,
            )
        else:
            triton_client = httpclient.InferenceServerClient(
                url=FLAGS.url, verbose=FLAGS.verbose
            )
    except Exception as e:
        print("channel creation failed: " + str(e))
        sys.exit(1)

    model_name = "testModel"

    if FLAGS.http_headers is not None:
        headers_dict = {l.split(":")[0]: l.split(":")[1] for l in FLAGS.http_headers}
    else:
        headers_dict = None

    # Infer with requested Outputs
    results = test_infer(
        model_name,
        headers_dict,
        FLAGS.request_compression_algorithm,
        FLAGS.response_compression_algorithm,
    )
    print(results.get_response())

    statistics = triton_client.get_inference_statistics(
        model_name=model_name, headers=headers_dict
    )
    print(statistics)