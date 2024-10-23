import threading
import time
from phishnet import start_server, create_app

def test_start_server():
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # This allows the thread to exit when the main program does
    server_thread.start()

    # Give the server a moment to start
    time.sleep(1)

    # Create a new test client to make requests to the running server
    app = create_app()
    client = app.test_client()

    # Now we can test the server is running by making a request
    response = client.get('/api/v1/hello_world')  # Adjust this based on your actual endpoint
    assert response.status_code == 200  # Check if the server is running and responding

