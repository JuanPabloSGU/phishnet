interface Link {
    href: string;
    text: string;
}

chrome.storage.local.get(['automatic_search'], (result) => {
    if (result.automatic_search) {
        chrome.storage.local.get(['jwt'], (result) => {
            if (chrome.runtime.lastError) {
                console.error(chrome.runtime.lastError.message);
            } else {
                const jwt = result.jwt;
                if (jwt) {
                    const a_tags = document.getElementsByTagName('a');

                    const possible_links = new Set<Link>();

                    for (let i = 0; i < a_tags.length; i++) {
                        possible_links.add({
                            href: a_tags[i].href,
                            text: a_tags[i].innerText
                        });
                    }

                    const fetchLinksPromises = Array.from(possible_links).map(link => {
                        return fetch('https://api.capstone.databending.ca/api/v1/urlBert', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${jwt}`
                            },
                            body: JSON.stringify({ url: link.href })
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log('Data from server:', data);
                                const score = Math.round(parseFloat(data["triton"]["outputs"][0]["data"].split("[")[1].split("]")[0]) * 100).toFixed(2);
                                const result = score + "%";
                                return { url: link.href, score: result };
                            })
                            .catch(error => {
                                console.error('Error fetching data:', error);
                            });
                    });

                    Promise.all(fetchLinksPromises).then(links => {
                        links = links.filter(link => link !== null && link !== undefined && link.url !== null && link.url !== undefined && link.url !== '');

                        chrome.runtime.sendMessage({ links: links }, (response) => {
                            console.log('Response from background:', response);
                        });
                    });
                } else {
                    console.error('JWT is empty');
                }
            }
        });
    } else {
        console.log('Automatic search disabled');
    }
});
