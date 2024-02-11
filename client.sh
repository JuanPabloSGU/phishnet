#!/bin/bash

# TODO: Integrate this code with updating a database

SERVER_IP="123123123" # Replace with server address
PORT_NO=12345 # Replace with port number of the server

# For local testing purposes (remove after integrating with database)
export output="output"
export dom="output/dom"
export screenshots="output/screenshots"
mkdir -p $dom $screenshots | tr -d '\r'

# Get API Key from variables when running this script
export API_KEY_URLSCAN=$1
export API_KEY_GSB=$2

declare -a responses

check_server_status() {
    nc -z "$SERVER_IP" $PORT_NO 
}

register_machine() {
    echo "register $(hostname)" | nc "$SERVER_IP" $PORT_NO 
}

unregister_machine() {
    echo "unregister $(hostname)" | nc "$SERVER_IP" $PORT_NO 
}

process_urls() {
    local urls=("$@")
    for url in "${urls[@]}"; do
        # Submit URL to urlscan.io
        response=$(curl -s -X POST "https://urlscan.io/api/v1/scan/" \
            -H "Content-Type: application/json" \
            -H "API-Key: $API_KEY_URLSCAN" \
            -d "{\"url\": \"$url\", \"visibility\": \"public\"}")

        # If the response is 400 then skip
        if [ $(echo $response | jq -r '.status') == "400" ]; then
            echo "Skipping $url, urlscan.io cannot process this url."
            continue
        fi

        # Extract the uuid from the response
        uuid=$(echo $response | jq -r '.uuid')

        # TODO: Replace this code with saving the uuid to database
        echo $uuid >> $output/uuids.txt

        sleep 2;
    done

    # Sleep until the scans are complete
    echo "Sleeping for 60 seconds"
    sleep 60; # Is there a reason for waiting 60s? The Result API documentation says to wait 10-30s

    # Loop through the list of uuids and get the result api response
    while IFS= read -r uuid; do
        urlscan_response=$(curl -s -X GET "https://urlscan.io/api/v1/result/$uuid/")

        # Get the url from the response
        url_to_check=$(echo $urlscan_response | jq -r '.page.url')

        # The request body for the Google Safe Browsing API
        request_body=$(jq -n --arg url "$url_to_check" '{
            "client": {
                "clientId": "Capstone", "clientVersion": "1.5.2"
            }, 
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"], 
                "platformTypes": ["ANY_PLATFORM"], 
                "threatEntryTypes": ["URL"], 
                "threatEntries": [{"url": $url}]
            }
        }')

        # Send the request to the Google Safe Browsing API
        gsb_response=$(curl -s -X POST "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=$API_KEY_GSB" \
            -H "Content-Type: application/json" \
            -d "$request_body")

        # Check if the response is an empty JSON object
        if [ "$gsb_response" = "{}" ]; then
            echo "The URL $url_to_check is safe according to the Google Safe Browsing API."
        else
            echo "The URL is potentially unsafe. Here's the response from the Google Safe Browsing API:"
            echo $gsb_response
        fi

        # TODO: Replace this code with saving the responses to database
        responses+=("$urlscan_response")
        responses+=("$gsb_response")

        # TODO: Replace this code with saving the DOM snapshot to database
        curl -s "https://urlscan.io/dom/$uuid/" > "$dom/$uuid.html"

        # TODO: Replace this code with saving the PNG screenshot to database
        curl -s "https://urlscan.io/screenshots/$uuid.png" > "$screenshots/$uuid.png"

        sleep 2;
    done < "$output/uuids.txt"
}

if !check_server_status; then
    echo "Server is not running. Exiting."
    exit 1
fi

register_machine

urls=($(<machine_$(hostname).txt)) # Get the assigned URLs

process_urls "${urls[@]}"

unregister_machine