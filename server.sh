#!bin/bash

# TODO: 
# - Test with multiple clients (on different machines) running at the same time
# - Add logic for distributing URLs from last indexed position within data_sources (pickup where we left off)

declare -a data_sources=(
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt"
    "https://temporary.com/legit-sites.txt" # Replace this with a URL of a .txt with legit sites
)

get_total_urls() {
    local total_urls=0
    for source in "${data_sources[@]}"; do
        local url_count=$(curl -s "$source" | wc -l)
        ((total_urls += url_count))
    done
    echo "$total_urls"
}

declare -a registered_machines=()

distribute_urls() {
    local total_urls=$(get_total_urls)
    local total_machines=${#registered_machines[@]} 
    # Max 500 URLs per machine (hourly urlscan.io limit)
    local urls_per_machine=$((total_urls / total_machines > 500 ? 500 : total_urls / total_machines))
    local index=0

    # Concatenate all URLs from data_sources into a single file
    local all_urls_file="all_urls.txt"
    for source in "${data_sources[@]}"; do
        curl -s "$source" >> "$all_urls_file"
    done

    for machine_id in "${registered_machines[@]}"; do
        local remaining_urls=$((total_urls - index))
        local count=$((remaining_urls < urls_per_machine ? remaining_urls : urls_per_machine))

        # Distribute URLs from the concatenated file
        shuf -n "$count" "$all_urls_file" >> "machine_${machine_id}.txt"
        index=$((index + count))
    done
}

# Server is always listening for registration and unregistration requests
while true; do
    read -r request machine_id
    case $request in
        register)
            registered_machines+=("$machine_id")
            distribute_urls
            ;;
        unregister)
            # Remove the unregistered machine and resize the array
            unset 'registered_machines[$(echo "${!registered_machines[@]}" | grep -o "\b$machine_id\b" | tail -n1)]'
            registered_machines=("${registered_machines[@]}")
            distribute_urls
            ;;
    esac
done