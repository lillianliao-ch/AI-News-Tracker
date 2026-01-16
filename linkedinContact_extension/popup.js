document.addEventListener('DOMContentLoaded', () => {
  const fetchButton = document.getElementById('fetchProfile');
  const resultDiv = document.getElementById('result');
  const statusDiv = document.getElementById('status');

  fetchButton.addEventListener('click', () => {
    statusDiv.textContent = 'Fetching...';
    resultDiv.textContent = '';

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentTab = tabs[0];
      if (!currentTab || !currentTab.url) {
        statusDiv.textContent = 'Error: Could not get current tab URL.';
        return;
      }

      const url = currentTab.url;
      if (!url.includes('linkedin.com/in/')) {
        statusDiv.textContent = 'Error: Not a LinkedIn profile page.';
        return;
      }

      // Call the local service
      fetch('http://localhost:8001/parse/pretty', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
      })
      .then(response => {
        if (!response.ok) {
          return response.json().then(err => {
            throw new Error(err.detail || `HTTP error! status: ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        statusDiv.textContent = 'Success!';
        resultDiv.textContent = data.text;
      })
      .catch(error => {
        statusDiv.textContent = 'Error fetching data:';
        resultDiv.textContent = error.message;
        console.error('Error:', error);
      });
    });
  });
});
