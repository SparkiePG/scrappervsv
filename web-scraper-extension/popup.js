// Script for the extension's popup. Handles user interaction, sends a
// message to the content script to extract data, displays the results and
// allows downloading the extracted data as JSON.

document.addEventListener('DOMContentLoaded', () => {
  const scrapeBtn = document.getElementById('scrapeBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const outputEl = document.getElementById('output');
  const statusEl = document.getElementById('status');
  const selectorInput = document.getElementById('selectorInput');
  let lastData = null;

  // Trigger scraping when the user clicks the button
  scrapeBtn.addEventListener('click', () => {
    // Reset UI state before starting a new scrape
    statusEl.textContent = 'Scraping…';
    statusEl.classList.remove('success', 'error');
    outputEl.textContent = '';
    downloadBtn.disabled = true;
    lastData = null;
    const selectorValue = selectorInput.value.trim();
    // Get the active tab and send a message to its content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || tabs.length === 0) {
        statusEl.textContent = 'No active tab found.';
        return;
      }
      const tabId = tabs[0].id;
      chrome.tabs.sendMessage(tabId, { action: 'extractData', selector: selectorValue || null }, (response) => {
        if (chrome.runtime.lastError || !response) {
          statusEl.textContent = 'Failed to extract data. Make sure the tab is a standard webpage.';
          statusEl.classList.add('error');
          return;
        }
        lastData = response.data;
        // Display a human‑readable preview of the data in the preview element
        const preview = {
          title: lastData.metadata.title,
          description: lastData.metadata.description,
          keywords: lastData.metadata.keywords,
          author: lastData.metadata.author,
          textSnippet:
            lastData.mainText.slice(0, 300) +
            (lastData.mainText.length > 300 ? '…' : ''),
          imageCount: lastData.images.length,
          linkCount: lastData.links.length,
        };
        outputEl.textContent = JSON.stringify(preview, null, 2);
        statusEl.textContent = 'Scraping complete.';
        statusEl.classList.add('success');
        downloadBtn.disabled = false;
      });
    });
  });

  // Allow downloading the last scraped data as a JSON file
  downloadBtn.addEventListener('click', () => {
    if (!lastData) return;
    const blob = new Blob([JSON.stringify(lastData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    chrome.downloads.download({ url, filename: 'scraped_data.json', saveAs: true }, () => {
      URL.revokeObjectURL(url);
    });
  });
});