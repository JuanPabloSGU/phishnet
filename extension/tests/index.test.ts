import puppeteer from 'puppeteer';

describe('Chrome Extension Tests', () => {
    let browser: puppeteer.Browser;
    let page: puppeteer.Page;
    const extensionId = 'ohplpfkbbipfioebipangnjbkmafongo';
    const extensionPath = 'dist/';

    beforeAll(async () => {
        browser = await puppeteer.launch({
            headless: true, // to see browser UI during tests
            args: [
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`,
            ],
            slowMo: 50
        });

        const pages = await browser.pages();
        page = pages[0];

        page.on('console', (msg) => {
            console.log('PAGE LOG:', msg.text());
        });
    });

    afterAll(async () => {
        await browser.close();
    });

    test('should load the extension title', async () => {
        const client = await page.target().createCDPSession();
        await client.send('Network.clearBrowserCookies');
        await client.send('Network.clearBrowserCache');
    
        await page.goto(`chrome-extension://${extensionId}/popup.html`);
        const title = await page.title();
        expect(title).toBe('Phishnet');
    });
    
    test('should load the extension paragraph', async () => {
        const client = await page.target().createCDPSession();
        await client.send('Network.clearBrowserCookies');
        await client.send('Network.clearBrowserCache');
    
        await page.goto(`chrome-extension://${extensionId}/popup.html`);
        const paragraph = await page.$eval('p', (el) => el.innerHTML);
        expect(paragraph).toBe('Phishnet is a browser extension that helps you identify phishing websites.');
    });
    
    test('should load the extension login button', async () => {
        const client = await page.target().createCDPSession();
        await client.send('Network.clearBrowserCookies');
        await client.send('Network.clearBrowserCache');
    
        await page.goto(`chrome-extension://${extensionId}/popup.html`);
        const button = await page.$eval('button', (el) => el.innerHTML);
        expect(button).toBe('Login');
    });


    test('Complete login form', async () => {
        const client = await page.target().createCDPSession();
        await client.send('Network.clearBrowserCookies');
        await client.send('Network.clearBrowserCache');

        await page.goto(`chrome-extension://${extensionId}/popup.html`);
        await page.waitForSelector('button');
        await page.click('button');

        const newPagePromise = new Promise<puppeteer.Page>((resolve) => {
            const onTargetCreated = async (target: puppeteer.Target) => {
                const newPage = await target.page();
                if (newPage) {
                    console.log('New page created:', newPage.url());
                    resolve(newPage);
                }
            };

            browser.on('targetcreated', onTargetCreated);
        });

        const newPage = await newPagePromise;

        if (newPage) {
            console.log('Interacting with new page...');

            try {
                await newPage.waitForSelector('#loginName', { timeout: 10000 });
                await newPage.type('#loginName', 'test@databending.ca', { delay: 100 });
                await newPage.click('#submit-button');

                await newPage.waitForSelector('#password', { timeout: 10000 });
                await newPage.type('#password', 'Capstone123!!', { delay: 100 });
                await newPage.click('#submit-button');

                try {
                    await Promise.race([
                        newPage.waitForNavigation({ timeout: 30000 }),
                        new Promise((_, reject) => newPage.once('close', () => reject(new Error('Page closed')))),
                        new Promise(resolve => setTimeout(resolve, 30000))
                    ]);
                } catch (navigationError) {
                    console.log('Navigation completed or page closed:', navigationError);
                }

                if (!newPage.isClosed()) {
                    await newPage.close();
                }

                await new Promise(resolve => setTimeout(resolve, 1000));

                await page.goto(`chrome-extension://${extensionId}/popup.html`, { waitUntil: 'networkidle0', timeout: 30000 });
                await page.waitForSelector('button', { timeout: 30000 });
                await page.click('button');

                await page.waitForNavigation({ timeout: 30000 });

                await page.waitForSelector('#user-info', { timeout: 30000 });

                const userInfo = await page.$eval('#user-info', (element) => {
                    const name = element.querySelector('p:nth-child(1)')?.textContent?.replace('Name: ', '');
                    const email = element.querySelector('p:nth-child(2)')?.textContent?.replace('Email: ', '');
                    const subject = element.querySelector('p:nth-child(3)')?.textContent?.replace('Subject: ', '');
                    return { name, email, subject };
                });

                expect(userInfo).toEqual({
                    name: 'Test Capstone',
                    email: 'test@databending.ca',
                    subject: '288034061585284627'
                });

            } catch (error) {
                console.error('Error during login process:', error);
                throw error;
            }
        } else {
            console.error('No new page was created for login.');
            throw new Error('Login page not created');
        }
    }, 120000); // Increase the timeout to 120 seconds

    test('basic link search', async () => {
        await page.goto(`chrome-extension://${extensionId}/home.html`);
        await page.waitForSelector('#phishing-form');
        await page.type('#url', 'https://www.google.com');
        await page.click('#phishing-form > button');

        await page.waitForSelector('#phishing-list');
        const phishingList = await page.$eval('#phishing-list', (element) => {
            const url = element.querySelector('p:nth-child(1)')?.textContent?.replace('URL: ', '');
            const score = element.querySelector('p:nth-child(2)')?.textContent?.replace('Score: ', '');

            return { url, score };
        });

        expect(phishingList).toEqual({
            url: 'https://www.google.com',
            score: expect.any(String)
        });
    });

    test('open settings page', async () => {
        await page.goto(`chrome-extension://${extensionId}/settings.html`);
        const title = await page.title();
        expect(title).toBe('Settings');
    });

    test('Enable Automatic Search', async () => {
        await page.goto(`chrome-extension://${extensionId}/settings.html`);
        await page.click('#toggle-automatic-search');
        await page.waitForSelector('#save-settings');


        const newPage = await browser.newPage();

        try {
            await Promise.all([
                page.click('#save-settings'),
                page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 5000 }).catch(() => {})
            ]);
        } catch (error) {
            console.log('Navigation error (this may be expected):', (error as Error).message);
        }

        // Reload the settings page to verify the changes
        await newPage.goto(`chrome-extension://${extensionId}/settings.html`, { waitUntil: 'networkidle0' });

        // Verify that the setting was saved
        const isAutomaticSearchEnabled = await newPage.$eval('#toggle-automatic-search', (el) => (el as HTMLInputElement).checked);
        expect(isAutomaticSearchEnabled).toBe(true);

        // Instead of closing and reopening the browser, just navigate to a new newPage
        await newPage.goto("https://www.google.com", { waitUntil: 'networkidle0', timeout: 20000 });
        console.log('Navigated to Google');

        await newPage.goto(`chrome-extension://${extensionId}/home.html`, { waitUntil: 'networkidle0', timeout: 20000 });
        console.log('Navigated back to extension home');

        await newPage.waitForSelector('#phishing-list', { timeout: 20000 });
        console.log('Found phishing-list');

        const phishingList = await newPage.$eval('#phishing-list', (element) => {
            const url = element.querySelector('p:nth-child(1)')?.textContent?.replace('URL: ', '');
            const score = element.querySelector('p:nth-child(2)')?.textContent?.replace('Score: ', '');
            return { url, score };
        });

        expect(phishingList).toEqual({
            url: 'https://about.google/?fg=1&utm_source=google-CA&utm_medium=referral&utm_campaign=hp-header',
            score: expect.any(String)
        });
    }, 60000);

    // Add a new afterEach hook to ensure browser is closed properly
    afterEach(async () => {
        if (browser && !browser.isConnected()) {
            await browser.close();
        }
    });

});
