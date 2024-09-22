function storeCommand(command) {
    fetch('/store_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Command stored:', data);
        handleCommand(command);  // Optionally handle the command locally
    })
    .catch(error => console.error('Error:', error));
}

// Function to handle the command locally (optional)
function handleCommand(command) {
    if (command === 'highlight') {
        document.querySelector('.card').style.border = '5px solid red';
    } else if (command === 'changeText') {
        document.querySelector('.card h2').innerText = 'Updated Title';
    } else if (command === 'redirectToReddit') {
        window.location.href = 'https://www.reddit.com/';
    } else if (command === 'calculator') {
        window.location.href = 'calculator.html';
    }
}

// Automatically open the command window when the page loads
window.onload = function() {
    let commandWindow = window.open('', 'Command Window', 'width=400,height=300');
    
    // Write the basic structure of the command window
    commandWindow.document.write(`
        <html>
        <head><title>Command Interface</title></head>
        <body>
            <h2>Send Command</h2>
            <input type="text" id="commandInput" placeholder="Enter command">
            <button id="sendButton">Send</button>
        </body>
        </html>
    `);

    // After the document is ready, we attach the script dynamically
    commandWindow.document.close();  // Important to close the document for DOM manipulation
    commandWindow.document.getElementById('sendButton').onclick = function() {
        const command = commandWindow.document.getElementById('commandInput').value;
        // Use postMessage to communicate with the main window
        window.postMessage(command, '*');
    };
};

// Listen for messages from the command window
window.addEventListener('message', function(event) {
    const command = event.data;
    storeCommand(command);  // Store the command to the database
});