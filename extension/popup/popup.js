// popup.js - Development/Testing Mode for Brightspace GPT Extension

const API_BASE_URL = 'http://localhost:8001/api';

console.log('🚀 Popup script loaded');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ DOM Content Loaded');
  
  // Add event listeners to buttons
  document.getElementById('detectPageBtn').addEventListener('click', detectCurrentPage);
  document.getElementById('extractDataBtn').addEventListener('click', testDataExtraction);
  document.getElementById('testBackendBtn').addEventListener('click', testBackendConnection);
  document.getElementById('sendTestBtn').addEventListener('click', sendTestQuery);
  document.getElementById('syncAllBtn').addEventListener('click', syncAllCourses);
  
  // Initialize
  checkInitialStatus();
  detectCurrentPage();
});

/**
 * Check initial connection status
 */
function checkInitialStatus() {
  console.log('🔍 Checking initial status...');
  const statusDiv = document.getElementById('status');
  
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const tab = tabs[0];
    console.log('Current tab URL:', tab.url);
    
    if (!tab.url.includes('brightspace.com')) {
      statusDiv.className = 'status error';
      statusDiv.innerHTML = '⚠️ Not on Brightspace. Please navigate to uottawa.brightspace.com';
      return;
    }
    
    // Try to ping content script
    chrome.tabs.sendMessage(tab.id, { action: 'ping' }, function(response) {
      if (chrome.runtime.lastError) {
        console.error('❌ Content script error:', chrome.runtime.lastError);
        statusDiv.className = 'status error';
        statusDiv.innerHTML = '⚠️ Content script not loaded. Please refresh the Brightspace page.';
      } else {
        console.log('✅ Content script responding');
        statusDiv.className = 'status';
        statusDiv.innerHTML = '✅ Connected to Brightspace page';
      }
    });
  });
}

/**
 * Detect current page type
 */
function detectCurrentPage() {
  console.log('🔍 Detecting page type...');
  const pageInfoDiv = document.getElementById('pageInfo');
  
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const tab = tabs[0];
    
    if (!tab.url.includes('brightspace.com')) {
      pageInfoDiv.innerHTML = '❌ Not on Brightspace';
      return;
    }
    
    chrome.tabs.sendMessage(tab.id, { action: 'extractData' }, function(response) {
      if (chrome.runtime.lastError) {
        console.error('❌ Error:', chrome.runtime.lastError);
        pageInfoDiv.innerHTML = '❌ Could not detect page type';
        return;
      }
      
      if (response && response.pageType) {
        console.log('📄 Page data:', response);
        pageInfoDiv.innerHTML = `
          <strong>Page Type:</strong> ${response.pageType}<br>
          <strong>Course ID:</strong> ${response.courseId || 'N/A'}<br>
          <strong>URL:</strong> ${tab.url.substring(0, 50)}...
        `;
      } else {
        pageInfoDiv.innerHTML = '❌ Could not detect page type';
      }
    });
  });
}

/**
 * Test data extraction from current page
 */
function testDataExtraction() {
  console.log('🧪 Testing data extraction...');
  const btn = document.getElementById('extractDataBtn');
  const dataDiv = document.getElementById('extractedData');
  
  btn.disabled = true;
  btn.textContent = 'Extracting...';
  dataDiv.style.display = 'block';
  dataDiv.innerHTML = 'Extracting data from page...';
  
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const tab = tabs[0];
    
    if (!tab.url.includes('brightspace.com')) {
      dataDiv.innerHTML = '❌ Please navigate to a Brightspace page first';
      btn.disabled = false;
      btn.textContent = 'Extract Current Page Data';
      return;
    }
    
    chrome.tabs.sendMessage(tab.id, { action: 'extractData' }, function(data) {
      if (chrome.runtime.lastError) {
        console.error('❌ Extraction error:', chrome.runtime.lastError);
        dataDiv.innerHTML = `❌ Error: ${chrome.runtime.lastError.message}<br><br>Make sure:<br>
          • You're on a Brightspace page<br>
          • The page has fully loaded<br>
          • You've refreshed the page after installing the extension`;
        btn.disabled = false;
        btn.textContent = 'Extract Current Page Data';
        return;
      }
      
      console.log('📊 Extracted data:', data);
      
      // Format and display the data
      let html = `<strong>Page Type:</strong> ${data.pageType}<br><br>`;
      
      if (data.courses && data.courses.length > 0) {
        html += `<strong>📚 Courses Found:</strong> ${data.courses.length}<br>`;
        data.courses.slice(0, 3).forEach(course => {
          html += `• ${course.name}<br>`;
        });
        if (data.courses.length > 3) {
          html += `... and ${data.courses.length - 3} more<br>`;
        }
      }
      
      if (data.grades && data.grades.grades) {
        html += `<br><strong>📊 Grades Found:</strong> ${data.grades.grades.length}<br>`;
      }
      
      if (data.assignments && data.assignments.assignments) {
        html += `<br><strong>📝 Assignments Found:</strong> ${data.assignments.assignments.length}<br>`;
      }
      
      if (data.announcements && data.announcements.announcements) {
        html += `<br><strong>📢 Announcements Found:</strong> ${data.announcements.announcements.length}<br>`;
      }
      
      html += `<br><pre>${JSON.stringify(data, null, 2).substring(0, 500)}...</pre>`;
      
      dataDiv.innerHTML = html;
      
      // Store the data
      chrome.storage.local.set({ 
        'latest_extracted_data': data,
        'last_extraction': new Date().toISOString()
      });
      
      btn.disabled = false;
      btn.textContent = 'Extract Current Page Data';
    });
  });
}

/**
 * Test backend connection
 */
function testBackendConnection() {
  console.log('🔌 Testing backend connection...');
  const btn = document.getElementById('testBackendBtn');
  const statusDiv = document.getElementById('backendStatus');
  
  btn.disabled = true;
  btn.textContent = 'Testing...';
  statusDiv.style.display = 'block';
  statusDiv.innerHTML = 'Connecting to backend...';
  
  fetch(`${API_BASE_URL}/health`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}`);
      }
      return response.json();
    })
    .then(health => {
      console.log('✅ Backend health:', health);
      statusDiv.innerHTML = `
        ✅ <strong>Backend Connected!</strong><br>
        Status: ${health.status}<br>
        Version: ${health.version || 'N/A'}
      `;
      btn.disabled = false;
      btn.textContent = 'Test Backend Connection';
    })
    .catch(error => {
      console.error('❌ Backend connection error:', error);
      statusDiv.innerHTML = `
        ❌ <strong>Backend Not Connected</strong><br>
        Error: ${error.message}<br><br>
        Make sure your backend is running at:<br>
        <code>http://localhost:8001</code><br><br>
        Start it with:<br>
        <code>cd backend && python -m uvicorn app.main:app --reload --port 8001</code>
      `;
      btn.disabled = false;
      btn.textContent = 'Test Backend Connection';
    });
}

/**
 * Send test query to backend
 */
function sendTestQuery() {
  console.log('💬 Sending test query...');
  const btn = document.getElementById('sendTestBtn');
  const queryInput = document.getElementById('testQuery');
  const responseDiv = document.getElementById('testResponse');
  
  const query = queryInput.value.trim();
  
  if (!query) {
    alert('Please enter a question');
    return;
  }
  
  btn.disabled = true;
  btn.textContent = 'Sending...';
  responseDiv.style.display = 'block';
  responseDiv.innerHTML = 'Waiting for AI response...';
  
  // Get stored course data
  chrome.storage.local.get(['brightspace_courses', 'latest_extracted_data'], function(stored) {
    const context = {
      courses: stored.brightspace_courses || [],
      currentPage: stored.latest_extracted_data || {}
    };
    
    console.log('📤 Sending query:', query);
    console.log('📦 Context:', context);
    
    // Get or create session ID
    chrome.storage.local.get(['session_id'], function(result) {
      let sessionId = result.session_id;
      if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        chrome.storage.local.set({ session_id: sessionId });
      }
      
      // Send to backend
      fetch(`${API_BASE_URL}/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          context: context,
          sessionId: sessionId
        })
      })
      .then(response => {
        if (!response.ok) {
          return response.text().then(text => {
            throw new Error(`Backend returned ${response.status}: ${text}`);
          });
        }
        return response.json();
      })
      .then(data => {
        console.log('📥 Response:', data);
        responseDiv.innerHTML = `
          <strong>AI Response:</strong><br>
          ${data.response || data.message || JSON.stringify(data)}
        `;
        queryInput.value = '';
        btn.disabled = false;
        btn.textContent = 'Send Test Query';
      })
      .catch(error => {
        console.error('❌ Query error:', error);
        responseDiv.innerHTML = `
          ❌ <strong>Error:</strong><br>
          ${error.message}<br><br>
          Make sure:<br>
          • Backend is running<br>
          • /api/chat/query endpoint exists<br>
          • CORS is configured
        `;
        btn.disabled = false;
        btn.textContent = 'Send Test Query';
      });
    });
  });
}

/**
 * Sync all courses from Brightspace
 */
function syncAllCourses() {
  console.log('🔄 Syncing all courses...');
  const btn = document.getElementById('syncAllBtn');
  const statusDiv = document.getElementById('syncStatus');
  const progressDiv = document.getElementById('syncProgress');
  
  btn.disabled = true;
  btn.textContent = 'Syncing...';
  progressDiv.style.display = 'block';
  progressDiv.innerHTML = 'Starting sync...';
  
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const tab = tabs[0];
    
    if (!tab.url.includes('brightspace.com/d2l/home')) {
      progressDiv.innerHTML = '❌ Please navigate to the Brightspace home page first<br>' +
                             'Go to: https://uottawa.brightspace.com/d2l/home';
      btn.disabled = false;
      btn.textContent = 'Sync All My Courses';
      return;
    }
    
    progressDiv.innerHTML = 'Extracting courses from Shadow DOM...<br>(Waiting for page to load, this may take up to 5 seconds)';
    
    // Wait a bit longer for Shadow DOM to render, then try extraction
    setTimeout(function() {
      // Extract courses
      chrome.tabs.sendMessage(tab.id, { action: 'extractCourses' }, function(result) {
        if (chrome.runtime.lastError) {
          console.error('❌ Sync error:', chrome.runtime.lastError);
          progressDiv.innerHTML = `
            ❌ <strong>Sync Failed:</strong><br>
            ${chrome.runtime.lastError.message}<br><br>
            <strong>Troubleshooting:</strong><br>
            1. Make sure you're on: uottawa.brightspace.com/d2l/home<br>
            2. Wait 2-3 seconds for the page to fully load<br>
            3. Try refreshing the page<br>
            4. Check the browser console (F12) for errors
          `;
          statusDiv.innerHTML = '❌ Sync failed';
          btn.disabled = false;
          btn.textContent = 'Sync All My Courses';
          return;
        }
        
        if (!result || !result.courses || result.courses.length === 0) {
          progressDiv.innerHTML = `
            ❌ <strong>No courses found</strong><br><br>
            Make sure:<br>
            1. You're on the home page<br>
            2. The page has fully loaded (wait 5 seconds)<br>
            3. You can see your course tiles on the page<br><br>
            Try: Close this popup, wait 5 seconds, then open it again and click Sync.
          `;
          statusDiv.innerHTML = '❌ No courses found';
          btn.disabled = false;
          btn.textContent = 'Sync All My Courses';
          return;
        }
        
        const courses = result.courses;
        console.log('✅ Found courses:', courses);
        
        progressDiv.innerHTML = `Found ${courses.length} courses. Saving...`;
        
        // Store courses
        chrome.storage.local.set({ 
          brightspace_courses: courses,
          last_sync: new Date().toISOString()
        }, function() {
          // Display results
          let html = `<strong>✅ Synced ${courses.length} courses:</strong><br><br>`;
          courses.forEach((course, i) => {
            html += `${i + 1}. ${course.name}<br>`;
            html += `   Code: ${course.code}<br>`;
            if (course.homepage) {
              html += `   <a href="${course.homepage}" target="_blank">View Course</a><br>`;
            }
            html += `<br>`;
          });
          
          progressDiv.innerHTML = html;
          statusDiv.innerHTML = `✅ Last synced: ${new Date().toLocaleTimeString()}`;
          
          // Try to send to backend
          chrome.storage.local.get(['user_id'], function(result) {
            let userId = result.user_id;
            if (!userId) {
              userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
              chrome.storage.local.set({ user_id: userId });
            }
            
            fetch(`${API_BASE_URL}/courses/sync`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                courses: courses,
                userId: userId
              })
            })
            .then(response => response.json())
            .then(data => {
              console.log('✅ Courses synced to backend:', data);
            })
            .catch(error => {
              console.warn('⚠️ Could not sync to backend:', error.message);
            });
          });
          
          btn.disabled = false;
          btn.textContent = 'Sync All My Courses';
        });
      });
    }, 3000); // Wait 3 seconds for Shadow DOM to fully render
  });
}

console.log('✅ All functions defined');