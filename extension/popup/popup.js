// extension/popup/popup.js
// Basic popup functionality for Phase 1

// Configuration
const BACKEND_URL = 'http://localhost:8001';  // Your FastAPI backend

// Initialize popup when DOM loads
document.addEventListener('DOMContentLoaded', function() {
  console.log('🎓 uOttawa Brightspace Assistant - Phase 1 Loaded');
  
  // Initial status check
  checkInitialStatus();
  
  // Set up event listeners
  setupEventListeners();
});

function setupEventListeners() {
  // Enter key for test query
  document.getElementById('testQuery').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendTestQuery();
    }
  });
  
  // Button click listeners
  document.getElementById('extractDataBtn').addEventListener('click', testDataExtraction);
  document.getElementById('detectPageBtn').addEventListener('click', detectCurrentPage);
  document.getElementById('testBackendBtn').addEventListener('click', testBackendConnection);
  document.getElementById('sendTestBtn').addEventListener('click', sendTestQuery);
}

async function checkInitialStatus() {
  const statusDiv = document.getElementById('status');
  
  try {
    // Check if we're on Brightspace
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const isBrightspace = tab.url && tab.url.includes('uottawa.brightspace.com');
    
    if (isBrightspace) {
      statusDiv.innerHTML = '✅ On Brightspace - Ready to extract data';
      statusDiv.className = 'status';
      
      // Auto-detect page
      detectCurrentPage();
    } else {
      statusDiv.innerHTML = '⚠️ Not on Brightspace - Navigate to uottawa.brightspace.com to test';
      statusDiv.className = 'status error';
    }
    
    // Test backend connection
    testBackendConnection();
    
  } catch (error) {
    statusDiv.innerHTML = '❌ Error checking status: ' + error.message;
    statusDiv.className = 'status error';
  }
}

async function detectCurrentPage() {
  const pageInfoDiv = document.getElementById('pageInfo');
  
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    if (!tab.url.includes('uottawa.brightspace.com')) {
      pageInfoDiv.innerHTML = '❌ Not on Brightspace';
      return;
    }
    
    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'detectPage'
    });
    
    if (response && response.success) {
      pageInfoDiv.innerHTML = `
        📍 <strong>Page:</strong> ${response.pageType}<br>
        🆔 <strong>Course:</strong> ${response.courseId || 'N/A'}<br>
        🔗 <strong>URL:</strong> ${response.url.substring(0, 50)}...
      `;
    } else {
      pageInfoDiv.innerHTML = '❓ Page detection failed - content script may not be loaded';
    }
    
  } catch (error) {
    pageInfoDiv.innerHTML = '❌ Error: ' + error.message;
    console.error('Page detection error:', error);
  }
}

async function testDataExtraction() {
  const extractBtn = document.getElementById('extractDataBtn');
  const dataDiv = document.getElementById('extractedData');
  
  console.log('testDataExtraction called');
  
  // Show loading state
  extractBtn.disabled = true;
  extractBtn.textContent = 'Extracting...';
  dataDiv.style.display = 'block';
  dataDiv.innerHTML = '<div class="loading">Extracting data from current page...</div>';
  
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    console.log('Current tab:', tab.url);
    
    if (!tab.url.includes('uottawa.brightspace.com')) {
      throw new Error('Not on Brightspace page');
    }
    
    // Send message to content script to extract data
    console.log('Sending extractData message...');
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'extractData'
    });
    
    console.log('Got response:', response);
    
    if (response && response.success) {
      // Display extracted data
      dataDiv.innerHTML = `
        <strong>✅ Data Extracted Successfully!</strong><br>
        <strong>Page Type:</strong> ${response.pageType}<br>
        <strong>Course:</strong> ${response.courseName || 'N/A'}<br>
        <strong>Course ID:</strong> ${response.courseId || 'N/A'}<br>
        <strong>Data Types Found:</strong> ${response.dataTypes?.join(', ') || 'None'}<br>
        <strong>Items Count:</strong> ${response.itemCount || 0}<br>
        <br>
        <strong>Sample Data:</strong>
        <pre style="max-height: 100px; overflow: auto; font-size: 10px;">${JSON.stringify(response.sampleData || response.items?.slice(0, 2), null, 2)}</pre>
      `;
    } else {
      dataDiv.innerHTML = '❌ No data extracted - may not be on a supported page';
    }
    
  } catch (error) {
    console.error('Data extraction error:', error);
    dataDiv.innerHTML = '❌ Extraction failed: ' + error.message;
  } finally {
    // Reset button
    extractBtn.disabled = false;
    extractBtn.textContent = 'Extract Current Page Data';
  }
}

async function testBackendConnection() {
  const backendBtn = document.getElementById('testBackendBtn');
  const statusDiv = document.getElementById('backendStatus');
  
  backendBtn.disabled = true;
  backendBtn.textContent = 'Testing...';
  statusDiv.style.display = 'block';
  statusDiv.innerHTML = 'Testing connection to backend...';
  
  try {
    // Test connection to your FastAPI backend
    const response = await fetch(`${BACKEND_URL}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      statusDiv.innerHTML = `
        ✅ <strong>Backend Connected!</strong><br>
        Status: ${data.status || 'running'}<br>
        Version: ${data.version || 'unknown'}
      `;
    } else {
      statusDiv.innerHTML = `❌ Backend responded with status: ${response.status}`;
    }
    
  } catch (error) {
    statusDiv.innerHTML = `❌ Connection failed: ${error.message}<br>
                          Make sure backend is running on ${BACKEND_URL}`;
  } finally {
    backendBtn.disabled = false;
    backendBtn.textContent = 'Test Backend Connection';
  }
}

async function sendTestQuery() {
  const queryInput = document.getElementById('testQuery');
  const sendBtn = document.getElementById('sendTestBtn');
  const responseDiv = document.getElementById('testResponse');
  
  const query = queryInput.value.trim();
  if (!query) {
    alert('Please enter a test query');
    return;
  }
  
  // Show loading state
  sendBtn.disabled = true;
  sendBtn.textContent = 'Sending...';
  responseDiv.style.display = 'block';
  responseDiv.innerHTML = '<div class="loading">Processing query...</div>';
  
  try {
    // First, get current page data
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    let brightspaceData = null;
    
    if (tab.url.includes('uottawa.brightspace.com')) {
      try {
        const dataResponse = await chrome.tabs.sendMessage(tab.id, {
          action: 'extractData'
        });
        
        if (dataResponse && dataResponse.success) {
          brightspaceData = dataResponse;
        }
      } catch (error) {
        console.log('Could not extract data, sending query without context');
      }
    }
    
    // Send query to backend
    const response = await fetch(`${BACKEND_URL}/api/extension/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        brightspace_data: brightspaceData,
        user_id: 'test_user_' + Date.now()
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      responseDiv.innerHTML = `
        <strong>🤖 AI Response:</strong><br>
        ${data.response || data.message || 'No response received'}<br>
        <br>
        <small><strong>Context Used:</strong> ${data.context_used ? data.context_used.join(', ') : 'None'}</small>
      `;
    } else {
      responseDiv.innerHTML = `❌ Query failed with status: ${response.status}`;
    }
    
  } catch (error) {
    responseDiv.innerHTML = `❌ Query error: ${error.message}`;
    console.error('Query error:', error);
  } finally {
    // Reset UI
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send Test Query';
    queryInput.value = '';
  }
}