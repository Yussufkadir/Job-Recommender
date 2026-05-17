const { chromium } = require('playwright');

(async () => {
	const browser = await chromium.launch();
	const page = await browser.newPage();

	page.on('console', (msg) => console.log('PAGE LOG:', msg.text()));
	page.on('request', (request) => {
		if (request.url().includes('/auth/')) {
			console.log(`REQUEST [${request.method()}] ${request.url()}`);
			console.log('DATA:', request.postData());
		}
	});
	page.on('response', (response) => {
		if (response.url().includes('/auth/')) {
			console.log(`RESPONSE [${response.status()}] ${response.url()}`);
		}
	});

	const email = `testuser_${Date.now()}@example.com`;

	console.log('--- SIGNUP PHASE ---');
	await page.goto('http://localhost:5173/signup');
	await page.waitForTimeout(500);
	await page.fill('input[type="email"]', email);
	await page.locator('input[type="password"]').nth(0).fill('Password123!');
	await page.locator('input[type="password"]').nth(1).fill('Password123!');

	await Promise.all([page.click('button[type="submit"]'), page.waitForTimeout(2000)]);

	console.log('--- LOGIN PHASE ---');
	await page.goto('http://localhost:5173/login');
	await page.waitForTimeout(500);
	await page.fill('input[type="email"]', email);
	await page.fill('input[type="password"]', 'Password123!');

	await Promise.all([page.click('button[type="submit"]'), page.waitForTimeout(2000)]);

	await browser.close();
})();
