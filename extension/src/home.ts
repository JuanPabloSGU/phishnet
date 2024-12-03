// eslint-disable-next-line @typescript-eslint/no-explicit-any
let list_of_urls = [] as any[];

document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.local.get(['jwt', 'token'], (result) => {
        if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError.message);
        } else {
            const jwt = result.jwt;
            const token = result.token;
            if (!jwt || !token) {
                window.location.href = 'popup.html';
            }
        }
    });


    const userInfoDiv = document.getElementById('user-info') as HTMLDivElement;
    const logout = document.getElementById('logout') as HTMLButtonElement;
    const phishingForm = document.getElementById('phishing-form') as HTMLFormElement;
    const phishingList = document.getElementById('phishing-list') as HTMLDivElement;

    chrome.runtime.sendMessage({ action: 'getToken' }, (response) => {
        const accessToken = response.token;
        if (accessToken) {
            fetch('https://zitadel.databending.ca/oidc/v1/userinfo', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            })
                .then(response => response.json())
                .then(data => {
                    console.log('User info:', data);
                    userInfoDiv.innerHTML = `
                        <p><strong>Name:</strong> ${data.name}</p>
          <p><strong>Email:</strong> ${data.email}</p>
                        <p><strong>Subject:</strong> ${data.sub}</p>
                    `;
                })
                .catch(error => {
                    console.error('Error fetching user info:', error);
                    userInfoDiv.innerHTML = '<p>Error fetching user info</p>';
                });
        }
    });

    phishingForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = event.target as HTMLFormElement;
        const url = form.url.value;

        if (!url) {
            console.error('URL is empty');
            return;
        }

        chrome.runtime.sendMessage({ action: 'getJWT' }, (response) => {
            const jwt = response.jwt;
            if (jwt) {
                fetch('https://api.capstone.databending.ca/api/v1/urlBert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${jwt}`
                    },
                    body: JSON.stringify({ url: url })
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Data from server:', data);
                        const score = Math.round(parseFloat(data["triton"]["outputs"][0]["data"].split("[")[1].split("]")[0]) * 100).toFixed(2);
                        const result = score + "%";

                        const exists = list_of_urls.some(item => item.url === url);
                        if (!exists) {
                            list_of_urls.push({ url: url, score: result });
                            updatePhishingList();
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                    });
            } else {
                console.error('JWT is empty');
            }
        });
    });

    chrome.runtime.sendMessage({ action: 'getLinks' }, (response) => {
        const links = response.links;
        if (links) {
            list_of_urls = links.filter((link: { url: string }, index: number, self: { url: string }[]) =>
                index === self.findIndex((t: { url: string }) => (
                    t.url === link.url
                ))
            );
            updatePhishingList();
        } else {
            console.error('Links are empty');
        }
    });

    function updatePhishingList() {
        phishingList.innerHTML = '';
        const uniqueUrls = Array.from(new Set(list_of_urls.map(item => item.url)));
        uniqueUrls.forEach((url) => {
            const item = list_of_urls.find(item => item.url === url);
            if (item) {
                const score = item.score;
                const phishingItem = document.createElement('div');
                phishingItem.innerHTML = `
                    <p><strong>URL:</strong> ${url}</p>
                    <p><strong>Score:</strong> ${score}</p>
                `;
                phishingList.appendChild(phishingItem);
            }
        });
    }

    logout.addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'clearToken' }, (response) => {
            const message = response.message;
            if (message) {
                chrome.storage.local.clear().then(() => {
                    console.log('Token cleared:', message);
                    chrome.action.setPopup({ popup: 'popup.html' });
                    window.location.href = 'popup.html';
                });
            } else {
                console.error('Error clearing token');
            }
        });
    });
});
