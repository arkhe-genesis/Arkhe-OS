const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Simple static server
const server = http.createServer((req, res) => {
    let filePath = '.' + req.url;
    if (filePath == './') {
        filePath = './scripts/test_rlattice_shader.html';
    } else {
        filePath = './scripts' + req.url;
    }

    const extname = path.extname(filePath);
    let contentType = 'text/html';
    switch (extname) {
        case '.js': contentType = 'text/javascript'; break;
        case '.css': contentType = 'text/css'; break;
        case '.json': contentType = 'application/json'; break;
        case '.png': contentType = 'image/png'; break;
        case '.jpg': contentType = 'image/jpg'; break;
        case '.glsl': contentType = 'text/plain'; break;
    }

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if(error.code == 'ENOENT'){
                res.writeHead(404);
                res.end('File not found: ' + filePath);
                res.end();
            }
            else {
                res.writeHead(500);
                res.end('Sorry, check with the site admin for error: '+error.code+' ..\n');
                res.end();
            }
        }
        else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(8080);
console.log('Server running at http://127.0.0.1:8080/');

(async () => {
    const browser = await puppeteer.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    await page.goto('http://127.0.0.1:8080/', { waitUntil: 'networkidle0' });

    // Wait for the status element to be added by the script
    await page.waitForSelector('#render-status', { timeout: 10000 });

    const status = await page.evaluate(() => window._testStatus);
    console.log('Test Status:', status);

    if (status === "SUCCESS") {
        console.log("Shader compiled and rendered successfully in headless WebGL!");
        process.exitCode = 0;
    } else {
        console.error("Shader test failed!");
        process.exitCode = 1;
    }

    await browser.close();
    server.close();
})();
