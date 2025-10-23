// popup.js - Chat Mode for Brightspace GPT Extension

const API_BASE_URL = 'http://localhost:8001/api';

// State management
let conversationHistory = [];
let isLoading = false;
let currentSessionId = null;
let currentTermOnly = true; // Filter to current term by default

console.log('🚀 Popup script loaded');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ DOM Content Loaded');
  initializeChat();
  setupEventListeners();
  checkInitialStatus();
  loadConversationHistory();
});

/**
 * Initialize chat interface
 */
function initializeChat() {
  const messageInput = document.getElementById('messageInput');
  const sendBtn = document.getElementById('sendBtn');
  
  // Auto-resize textarea
  messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    
    // Enable/disable send button
    sendBtn.disabled = !this.value.trim() || isLoading;
  });
  
  // Send on Enter (but Shift+Enter for new line)
  messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) {
        sendMessage();
      }
    }
  });
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
  // Send message
  document.getElementById('sendBtn').addEventListener('click', sendMessage);
  
  // Header buttons
  document.getElementById('refreshBtn').addEventListener('click', refreshData);
  document.getElementById('settingsBtn').addEventListener('click', toggleSettings);
  document.getElementById('clearBtn').addEventListener('click', clearChat);
  
  // Settings panel buttons
  document.getElementById('syncCoursesBtn').addEventListener('click', syncAllCourses);
  document.getElementById('fetchGradesBtn').addEventListener('click', () => fetchData('grades'));
  document.getElementById('fetchAssignmentsBtn').addEventListener('click', () => fetchData('assignments'));
  document.getElementById('fetchAnnouncementsBtn').addEventListener('click', () => fetchData('announcements'));
  document.getElementById('testBackendBtn').addEventListener('click', testBackend);
  document.getElementById('viewLogsBtn').addEventListener('click', viewLogs);
  
  // Term filter toggle
  document.getElementById('currentTermOnly').addEventListener('change', function(e) {
    currentTermOnly = e.target.checked;
    chrome.storage.local.set({ currentTermOnly: currentTermOnly });
    updateDataInfo();
    console.log(`🎓 Current term filter: ${currentTermOnly ? 'ON' : 'OFF'}`);
  });
  
  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', function() {
      const query = this.dataset.query;
      document.getElementById('messageInput').value = query;
      sendMessage();
    });
  });
  
  // Close settings when clicking outside
  document.addEventListener('click', function(e) {
    const settingsPanel = document.getElementById('settingsPanel');
    const settingsBtn = document.getElementById('settingsBtn');
    
    if (!settingsPanel.contains(e.target) && e.target !== settingsBtn) {
      settingsPanel.classList.remove('show');
    }
  });
}

/**
 * Check initial connection status
 */
async function checkInitialStatus() {
  console.log('🔍 Checking initial status...');
  
  // Load filter preference
  const filterData = await chrome.storage.local.get(['currentTermOnly']);
  if (filterData.currentTermOnly !== undefined) {
    currentTermOnly = filterData.currentTermOnly;
    document.getElementById('currentTermOnly').checked = currentTermOnly;
  }
  
  try {
    // Check if we're on Brightspace
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    
    if (!tab.url.includes('brightspace.com')) {
      updateStatus('Not on Brightspace', 'error');
      return;
    }
    
    // Try to ping content script
    chrome.tabs.sendMessage(tab.id, { action: 'ping' }, function(response) {
      if (chrome.runtime.lastError) {
        updateStatus('Refresh Brightspace page', 'error');
      } else {
        updateStatus('Connected');
        updateDataInfo();
      }
    });
  } catch (error) {
    console.error('❌ Status check error:', error);
    updateStatus('Connection error', 'error');
  }
}

/**
 * Update status indicator
 */
function updateStatus(text, type = 'success') {
  const statusText = document.getElementById('statusText');
  const statusDot = document.getElementById('statusDot');
  
  statusText.textContent = text;
  
  if (type === 'error') {
    statusDot.classList.add('error');
  } else {
    statusDot.classList.remove('error');
  }
}

/**
 * Update data info in status bar
 */
async function updateDataInfo() {
  const data = await chrome.storage.local.get([
    'brightspace_courses',
    'brightspace_grades',
    'brightspace_assignments',
    'brightspace_announcements'
  ]);
  
  // Filter courses if needed
  let courses = data.brightspace_courses || [];
  if (currentTermOnly) {
    courses = filterCurrentTermCourses(courses);
  }
  
  const counts = {
    courses: courses.length,
    grades: data.brightspace_grades?.length || 0,
    assignments: data.brightspace_assignments?.length || 0,
    announcements: data.brightspace_announcements?.length || 0
  };
  
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  
  if (total === 0) {
    document.getElementById('dataInfo').textContent = 'No data loaded';
    document.getElementById('dataStatus').innerHTML = `
      <strong>No data loaded yet</strong><br>
      Click "Sync All Courses" to get started
    `;
  } else {
    const termText = currentTermOnly ? ' (current term)' : ' (all terms)';
    document.getElementById('dataInfo').textContent = 
      `${counts.courses} courses${termText} • ${counts.grades} grades loaded`;
    
    document.getElementById('dataStatus').innerHTML = `
      <strong>Data Loaded:</strong><br>
      Courses: ${counts.courses}${termText}<br>
      Grades: ${counts.grades}<br>
      Assignments: ${counts.assignments}<br>
      Announcements: ${counts.announcements}
    `;
  }
}

/**
 * Filter courses to only current term (4 months)
 */
function filterCurrentTermCourses(courses) {
  if (!courses || courses.length === 0) return [];
  
  const now = new Date();
  const fourMonthsAgo = new Date(now.getTime() - (120 * 24 * 60 * 60 * 1000)); // 120 days
  
  return courses.filter(course => {
    // If course is explicitly marked as active, include it
    if (course.isActive === true) return true;
    
    // Check end date - if course ended more than 4 months ago, exclude it
    if (course.endDate) {
      try {
        const endDate = new Date(course.endDate);
        if (endDate < fourMonthsAgo) {
          console.log(`📅 Filtering out past course: ${course.code} (ended ${endDate.toLocaleDateString()})`);
          return false;
        }
      } catch (e) {
        console.warn(`⚠️ Could not parse end date for ${course.code}`);
      }
    }
    
    // Check start date - if course hasn't started yet and is more than 1 month away, exclude it
    if (course.startDate) {
      try {
        const startDate = new Date(course.startDate);
        const oneMonthFromNow = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
        if (startDate > oneMonthFromNow) {
          console.log(`📅 Filtering out future course: ${course.code} (starts ${startDate.toLocaleDateString()})`);
          return false;
        }
      } catch (e) {
        console.warn(`⚠️ Could not parse start date for ${course.code}`);
      }
    }
    
    // Default: include the course
    return true;
  });
}

/**
 * Load conversation history from storage
 */
async function loadConversationHistory() {
  const data = await chrome.storage.local.get(['conversation_history', 'session_id']);
  
  if (data.conversation_history && data.conversation_history.length > 0) {
    conversationHistory = data.conversation_history;
    currentSessionId = data.session_id;
    
    // Display messages
    const emptyState = document.getElementById('emptyState');
    emptyState.style.display = 'none';
    
    conversationHistory.forEach(msg => {
      displayMessage(msg.role, msg.content, msg.timestamp, false);
    });
    
    scrollToBottom();
  }
}

/**
 * Send message to AI
 */
async function sendMessage() {
  const messageInput = document.getElementById('messageInput');
  const query = messageInput.value.trim();
  
  if (!query || isLoading) return;
  
  // Clear input and disable
  messageInput.value = '';
  messageInput.style.height = 'auto';
  isLoading = true;
  document.getElementById('sendBtn').disabled = true;
  
  // Hide empty state
  document.getElementById('emptyState').style.display = 'none';
  
  // Display user message
  const timestamp = new Date().toISOString();
  displayMessage('user', query, timestamp);
  
  // Add to history
  conversationHistory.push({ role: 'user', content: query, timestamp });
  await saveConversationHistory();
  
  // Show typing indicator
  showTypingIndicator();
  
  try {
    // Get context data
    const context = await getContextData();
    
    // Get or create session ID
    if (!currentSessionId) {
      currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      await chrome.storage.local.set({ session_id: currentSessionId });
    }
    
    // Send to backend
    const response = await fetch(`${API_BASE_URL}/chat/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        context: context,
        sessionId: currentSessionId,
        conversationHistory: conversationHistory.slice(-10) // Last 10 messages for context
      })
    });
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    
    const data = await response.json();
    
    // Hide typing indicator
    hideTypingIndicator();
    
    // Display assistant response
    const responseTimestamp = new Date().toISOString();
    displayMessage('assistant', data.response, responseTimestamp);
    
    // Add to history
    conversationHistory.push({ 
      role: 'assistant', 
      content: data.response, 
      timestamp: responseTimestamp 
    });
    await saveConversationHistory();
    
  } catch (error) {
    console.error('❌ Send message error:', error);
    
    // Hide typing indicator
    hideTypingIndicator();
    
    // Show error message
    const errorMsg = `Sorry, I couldn't process your question. ${error.message}\n\nMake sure the backend is running at ${API_BASE_URL}`;
    displayMessage('assistant', errorMsg, new Date().toISOString());
    
  } finally {
    isLoading = false;
    document.getElementById('sendBtn').disabled = false;
    messageInput.focus();
  }
}

/**
 * Display a message in the chat
 */
function displayMessage(role, content, timestamp, animate = true) {
  const messagesArea = document.getElementById('messagesArea');
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  if (!animate) {
    messageDiv.style.animation = 'none';
  }
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'message-bubble';
  bubbleDiv.textContent = content;
  
  const timeDiv = document.createElement('div');
  timeDiv.className = 'message-time';
  timeDiv.textContent = formatTime(timestamp);
  
  messageDiv.appendChild(bubbleDiv);
  messageDiv.appendChild(timeDiv);
  messagesArea.appendChild(messageDiv);
  
  scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
  const messagesArea = document.getElementById('messagesArea');
  
  const indicatorDiv = document.createElement('div');
  indicatorDiv.className = 'message assistant';
  indicatorDiv.id = 'typingIndicator';
  
  const typingDiv = document.createElement('div');
  typingDiv.className = 'typing-indicator';
  typingDiv.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  
  indicatorDiv.appendChild(typingDiv);
  messagesArea.appendChild(indicatorDiv);
  
  scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
  const indicator = document.getElementById('typingIndicator');
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Scroll messages to bottom
 */
function scrollToBottom() {
  const messagesArea = document.getElementById('messagesArea');
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  
  return date.toLocaleDateString();
}

/**
 * Get context data for AI
 */
async function getContextData() {
  const data = await chrome.storage.local.get([
    'brightspace_courses',
    'brightspace_grades',
    'brightspace_assignments',
    'brightspace_announcements',
    'latest_extracted_data'
  ]);
  
  // Filter courses if needed
  let courses = data.brightspace_courses || [];
  if (currentTermOnly) {
    courses = filterCurrentTermCourses(courses);
    console.log(`🎓 Filtered to ${courses.length} current term courses`);
  }
  
  // Get org unit IDs of current courses for filtering other data
  const currentOrgUnitIds = new Set(courses.map(c => c.orgUnitId).filter(Boolean));
  
  // Filter grades, assignments, and announcements to match current courses
  let grades = data.brightspace_grades || [];
  let assignments = data.brightspace_assignments || [];
  let announcements = data.brightspace_announcements || [];
  
  if (currentTermOnly && currentOrgUnitIds.size > 0) {
    grades = grades.filter(g => currentOrgUnitIds.has(g.orgUnitId));
    assignments = assignments.filter(a => currentOrgUnitIds.has(a.orgUnitId));
    announcements = announcements.filter(a => currentOrgUnitIds.has(a.orgUnitId));
    console.log(`🎓 Filtered to current term: ${grades.length} grade sets, ${assignments.length} assignment sets, ${announcements.length} announcement sets`);
  }
  
  return {
    courses: courses,
    grades: grades,
    assignments: assignments,
    announcements: announcements,
    currentPage: data.latest_extracted_data || {},
    currentTermOnly: currentTermOnly
  };
}

/**
 * Save conversation history to storage
 */
async function saveConversationHistory() {
  await chrome.storage.local.set({
    conversation_history: conversationHistory,
    session_id: currentSessionId,
    last_conversation_update: new Date().toISOString()
  });
}

/**
 * Clear chat history
 */
async function clearChat() {
  // Better confirmation dialog
  const messageCount = conversationHistory.length;
  const confirmMessage = messageCount === 0 
    ? 'Start a new conversation?'
    : `Clear all ${messageCount} messages and start fresh?\n\nThis will delete your entire conversation history.`;
  
  if (!confirm(confirmMessage)) return;
  
  console.log('🗑️ Clearing conversation history...');
  
  conversationHistory = [];
  currentSessionId = null;
  
  await chrome.storage.local.remove(['conversation_history', 'session_id', 'last_conversation_update']);
  
  // Clear UI
  const messagesArea = document.getElementById('messagesArea');
  messagesArea.innerHTML = `
    <div class="empty-state" id="emptyState">
      <div class="empty-state-icon">💬</div>
      <div class="empty-state-title">Chat Cleared!</div>
      <div class="empty-state-text">
        Ask me anything about your courses, grades, assignments, or upcoming deadlines.
      </div>
      <div class="suggestion-chips">
        <div class="suggestion-chip" data-query="What courses do I have?">📚 My courses</div>
        <div class="suggestion-chip" data-query="What's my grade in CSI2532?">📊 Check grades</div>
        <div class="suggestion-chip" data-query="What assignments are due this week?">📝 Due soon</div>
        <div class="suggestion-chip" data-query="Any new announcements?">📢 Announcements</div>
      </div>
    </div>
  `;
  
  // Re-add suggestion chip listeners
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', function() {
      const query = this.dataset.query;
      document.getElementById('messageInput').value = query;
      sendMessage();
    });
  });
  
  console.log('✅ Chat cleared successfully');
}

/**
 * Toggle settings panel
 */
function toggleSettings() {
  const panel = document.getElementById('settingsPanel');
  panel.classList.toggle('show');
}

/**
 * Refresh all data
 */
async function refreshData() {
  updateStatus('Refreshing...', 'loading');
  
  try {
    await syncAllCourses();
    await fetchData('grades');
    await fetchData('assignments');
    await fetchData('announcements');
    
    updateStatus('Data refreshed');
    updateDataInfo();
  } catch (error) {
    console.error('Refresh error:', error);
    updateStatus('Refresh failed', 'error');
  }
}

/**
 * Sync all courses
 */
async function syncAllCourses() {
  console.log('🔄 Syncing courses...');
  const btn = document.getElementById('syncCoursesBtn');
  const originalText = btn.textContent;
  
  btn.disabled = true;
  btn.textContent = 'Syncing...';
  
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    
    if (!tab.url.includes('brightspace.com')) {
      throw new Error('Not on Brightspace');
    }
    
    const result = await new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(tab.id, { action: 'extractCourses' }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    if (result.courses && result.courses.length > 0) {
      await chrome.storage.local.set({
        brightspace_courses: result.courses,
        last_sync: new Date().toISOString()
      });
      
      console.log(`✅ Synced ${result.courses.length} courses`);
      updateDataInfo();
    }
    
  } catch (error) {
    console.error('Sync error:', error);
    alert(`Sync failed: ${error.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

/**
 * Fetch data (grades, assignments, or announcements)
 */
async function fetchData(type) {
  console.log(`📊 Fetching ${type}...`);
  
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    
    const actionMap = {
      'grades': 'fetchAllGrades',
      'assignments': 'fetchAllAssignments',
      'announcements': 'fetchAllAnnouncements'
    };
    
    const result = await new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(tab.id, { action: actionMap[type] }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    if (result[type]) {
      await chrome.storage.local.set({
        [`brightspace_${type}`]: result[type],
        [`last_${type}_fetch`]: new Date().toISOString()
      });
      
      console.log(`✅ Fetched ${result[type].length} ${type}`);
      updateDataInfo();
    }
    
  } catch (error) {
    console.error(`Fetch ${type} error:`, error);
  }
}

/**
 * Test backend connection
 */
async function testBackend() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      alert('✅ Backend connection successful!');
    } else {
      throw new Error(`Status ${response.status}`);
    }
  } catch (error) {
    alert(`❌ Backend connection failed: ${error.message}\n\nMake sure backend is running on ${API_BASE_URL}`);
  }
}

/**
 * View debug logs
 */
async function viewLogs() {
  const data = await chrome.storage.local.get(['conversation_history', 'eventLogs']);
  
  console.log('📋 Conversation History:', data.conversation_history);
  console.log('📋 Event Logs:', data.eventLogs);
  
  alert('Debug logs printed to console (F12)');
}

console.log('✅ Chat functions initialized');