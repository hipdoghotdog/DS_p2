const http = require('http');

// Function to send a request to a URL and log the response
const makeRequest = (url) => {
    return new Promise((resolve, reject) => {
        console.log(`Sending request to: ${url}`);
        http.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            res.on('end', () => {
                console.log(`Response received from: ${url}`);
                resolve(data);
            });
        }).on('error', (err) => {
            console.error(`Error connecting to ${url}: ${err}`);
            reject(err);
        });
    });
};

// Function to perform load test on the /api/fortune endpoint
const runLoadTest = async () => {
    const url = 'http://localhost/api/fortune';
    const requestCount = 100; // Adjust how many requests you want to send

    console.log(`Starting load test with ${requestCount} requests to ${url}`);

    const startTime = Date.now();

    // Sending multiple requests concurrently
    const requests = [];
    for (let i = 0; i < requestCount; i++) {
        requests.push(makeRequest(url));
    }

    try {
        await Promise.all(requests);  // Wait for all requests to complete
        const endTime = Date.now();
        console.log(`Load test completed in ${endTime - startTime} ms.`);
    } catch (error) {
        console.error(`Error during load test: ${error}`);
    }
};

// Start the load test
runLoadTest();
