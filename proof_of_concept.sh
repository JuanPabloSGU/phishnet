#!bin/bash
declare -a data_sources=(
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt"
    "https://temporary.com/legit-sites.txt" # Replace this with a URL of a .txt with legit sites
)

export output="output"
export dom="output/dom"
export screenshots="output/screenshots"

# Get API Key from variables when running this script
export API_KEY_URLSCAN=$1
export API_KEY_GSB=$2

# Create directory if not present
mkdir -p $dom $screenshots | tr -d '\r'

# Downloads lists of URLs from the data_sources array
for url in "${data_sources[@]}"; do
    curl -L "$url" > $output/$(basename "$url") | tr -d '\r' #basename extracts the filename portion (including extension)
done

# Loop through the list of urls and submit them to urlscan.io
while IFS= read -r url; do
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

    # Save the uuid to a file
    echo $uuid >> $output/uuids.txt

    sleep 2;
done < <(cat $output/*.txt) # Reads all .txt files in the output folder

# Sleep until the scans are complete
echo "Sleeping for 60 seconds"
sleep 60; # Is there a reason for waiting 60s? The Result API documentation says to wait at least 10s

# Empty bash array
declare -a responses

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

    responses+=("$urlscan_response")
    responses+=("$gsb_response")

    # Retrieve DOM snapshot
    curl -s "https://urlscan.io/dom/$uuid/" > "$dom/$uuid.html"

    # Retrieve PNG screenshot
    curl -s "https://urlscan.io/screenshots/$uuid.png" > "$screenshots/$uuid.png"

    sleep 2;
done < "$output/uuids.txt"

# Convert the bash array to a JSON array and write it to a file
printf '%s\n' "${responses[@]}" | jq -s '.' > $output/results.json