const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('request', request => {
        if (request.url().includes('/auth/login')) {
            console.log('REQUEST HEADERS:', request.headers());
            console.log('REQUEST POST DATA:', request.postData());
        }
    });

    await page.goto('http://localhost:5173/login');
    await page.waitForTimeout(1000);

    await page.fill('input[type="text"]', 'mytest27@example.com');
    await page.fill('input[type="password"]', 'Password123!');

    await Promise.all([
        page.click('button[type="submit"]'),
        page.waitForTimeout(2000)
    ]);

    await browser.close();
})();
