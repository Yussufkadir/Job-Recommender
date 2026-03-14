const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));
  page.on('response', response => console.log('RESPONSE:', response.url(), response.status()));
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) console.log('NAVIGATED:', frame.url());
  });

  await page.goto('http://localhost:5173/login');
  
  await page.fill('input[type="text"]', 'test@test.com');
  await page.fill('input[type="password"]', 'worngpassword');
  
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForTimeout(3000)
  ]);

  console.log('Final URL:', page.url());
  await browser.close();
})();
