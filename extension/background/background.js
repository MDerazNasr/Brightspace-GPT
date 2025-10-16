// extension/background/background.js
// Background service worker for Phase 1

console.log('🎓 uOttawa Brightspace Assistant background script loaded');

// Configuration
const BACKEND_URL = 'http://localhost:8001'

// Extension installation/update handler
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Extension installed/updated:', details.reason);
  
  if (details.reason === 'install') {
    console.log('First time installation - setting up defaults');
    
    chrome.storage.local.set({
      extensionVersion: '0.1.0',
      installDate: new Date().toISOString(),
      userId: 'temp_user_' + Date.now(),
      settings: {
        autoExtract: true,
        debugMode: true
      }
    });
  }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);
  
  switch (request.action) {
    case 'storeData':
      handleStoreData(request.data).then(sendResponse);
      break;
      
    case 'getData':
      handleGetData(request.userId).then(sendResponse);
      break;
      
    case 'sendToBackend':
      handleSendToBackend(request.data).then(sendResponse);
      break;
      
    case 'logEvent':
      handleLogEvent(request.event).then(sendResponse);
      break;
      
    default:
      console.log('Unknown action:', request.action);
      sendResponse({ success: false, error: 'Unknown action' });
  }
  
  return true; // Keep message channel open for async responses
});

// Store extracted data locally
async function handleStoreData(data) {
  try {
    const timestamp = new Date().toISOString();
    const storageKey = `brightspace_data_${timestamp}`;
    
    await chrome.storage.local.set({
      [storageKey]: {
        ...data,
        storedAt: timestamp
      }
    });
    
    const result = await chrome.storage.local.get(['recentDataKeys']);
    const recentKeys = result.recentDataKeys || [];
    
    recentKeys.unshift(storageKey);
    const trimmedKeys = recentKeys.slice(0, 10);
    
    await chrome.storage.local.set({ recentDataKeys: trimmedKeys });
    
    console.log('Data stored successfully:', storageKey);
    return { success: true, storageKey };
    
  } catch (error) {
    console.error('Error storing data:', error);
    return { success: false, error: error.message };
  }
}

// Retrieve stored data
async function handleGetData(userId) {
  try {
    const result = await chrome.storage.local.get(['recentDataKeys']);
    const recentKeys = result.recentDataKeys || [];
    
    if (recentKeys.length === 0) {
      return { success: true, data: null, message: 'No data available' };
    }
    
    const latestKey = recentKeys[0];
    const latestData = await chrome.storage.local.get([latestKey]);
    
    return { 
      success: true, 
      data: latestData[latestKey],
      availableCount: recentKeys.length
    };
    
  } catch (error) {
    console.error('Error retrieving data:', error);
    return { success: false, error: error.message };
  }
}

// Send data to backend API
async function handleSendToBackend(data) {
  try {
    console.log('Sending data to backend:', BACKEND_URL);
    
    const response = await fetch(`${BACKEND_URL}/api/extension/process-brightspace-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Backend response:', result);
      return { success: true, result };
    } else {
      throw new Error(`Backend responded with status: ${response.status}`);
    }
    
  } catch (error) {
    console.error('Error sending to backend:', error);
    return { 
      success: false, 
      error: error.message,
      suggestion: 'Make sure the backend server is running on ' + BACKEND_URL
    };
  }
}

// Log events for debugging
async function handleLogEvent(event) {
  try {
    const timestamp = new Date().toISOString();
    const logEntry = {
      ...event,
      timestamp
    };
    
    const result = await chrome.storage.local.get(['eventLogs']);
    const logs = result.eventLogs || [];
    
    logs.unshift(logEntry);
    const trimmedLogs = logs.slice(0, 100);
    
    await chrome.storage.local.set({ eventLogs: trimmedLogs });
    
    console.log('Event logged:', logEntry);
    return { success: true };
    
  } catch (error) {
    console.error('Error logging event:', error);
    return { success: false, error: error.message };
  }
}

// Tab update listener
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    
    if (tab.url.includes('uottawa.brightspace.com')) {
      console.log('User navigated to Brightspace:', tab.url);
      
      chrome.action.setBadgeText({
        tabId: tabId,
        text: '✓'
      });
      
      chrome.action.setBadgeBackgroundColor({
        tabId: tabId,
        color: '#8B1538'
      });
      
    } else {
      chrome.action.setBadgeText({
        tabId: tabId,
        text: ''
      });
    }
  }
});