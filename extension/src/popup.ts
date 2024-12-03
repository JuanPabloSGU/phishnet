// Function to generate a random string (code verifier)
function generateRandomString(length: number): string {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let randomString = '';
    for (let i = 0; i < length; i++) {
        const randomIndex = Math.floor(Math.random() * characters.length);
        randomString += characters[randomIndex];
    }
    return randomString;
}

// Function to generate SHA-256 hash and base64-url-encode it (code challenge)
async function generateCodeChallenge(codeVerifier: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(codeVerifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
    const base64Url = btoa(String.fromCharCode(...new Uint8Array(hash)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, ''); // Remove padding
    return base64Url;
}

document.addEventListener('DOMContentLoaded', () => {
    const login = document.getElementById('login') as HTMLButtonElement;
    login?.addEventListener('click', async () => {
        const code_verifier = generateRandomString(128);
        const code_challenge = await generateCodeChallenge(code_verifier);

        // Store the code verifier in the local storage
        localStorage.setItem('code_verifier', code_verifier);

        const client_id = '287272511991840275';
        const redirect_uri = chrome.identity.getRedirectURL('oauth2');
        const scope = 'openid profile email offline_access';
        const response_type = 'code';
        const response_mode = 'query';
        const code_challenge_method = 'S256';
        const state = 'ybshps1hnzh';
        const nonce = 'nz9ng1ee42e';

        const authUrl = `https://zitadel.databending.ca/oauth/v2/authorize?client_id=${client_id}&redirect_uri=${encodeURIComponent(redirect_uri)}&scope=${scope}&response_type=${response_type}&response_mode=${response_mode}&code_challenge_method=${code_challenge_method}&code_challenge=${code_challenge}&state=${state}&nonce=${nonce}`;

        chrome.identity.launchWebAuthFlow(
            {
                url: authUrl,
                interactive: true
            },
            (redirect_uri) => {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError.message);
                    return;
                }

                if (!redirect_uri) {
                    console.error('Redirect URI is empty');
                    return;
                }

                const tokenParam = new URL(redirect_uri).searchParams;
                const authCode = tokenParam.get('code');

                if (authCode) {
                    const code_verifier = localStorage.getItem('code_verifier');

                    fetch('https://zitadel.databending.ca/oauth/v2/token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        body: new URLSearchParams({
                            'code': authCode,
                            'grant_type': 'authorization_code',
                            'redirect_uri': chrome.identity.getRedirectURL('oauth2'),
                            'client_id': client_id,
                            'code_verifier': code_verifier || ''
                        })
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.access_token) {

                                chrome.storage.local.set({
                                    jwt: data.id_token,
                                    token: data.access_token
                                }, () => {
                                    if (chrome.runtime.lastError) {
                                        console.error(chrome.runtime.lastError.message);
                                    } else {
                                        chrome.storage.local.get(['jwt', 'token'], (result) => {
                                            if (chrome.runtime.lastError) {
                                                console.error('Error retrieving data:', chrome.runtime.lastError.message);
                                            } else {
                                                console.log('Data retrieved:', result);
                                            }
                                        });
                                        console.log('JWT and token saved');
                                        chrome.runtime.sendMessage({ token: data.access_token });
                                        chrome.runtime.sendMessage({ jwt: data.id_token });
                                        chrome.action.setPopup({ popup: 'home.html' });
                                        window.location.href = 'home.html';
                                    }
                                })
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching data:', error);
                        });
                } else {
                    console.error('Authorization code is empty');
                }
            }
        );
    });
});
