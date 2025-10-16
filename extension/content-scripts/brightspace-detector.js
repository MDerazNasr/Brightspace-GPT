// extension/content-scripts/brightspace-detector.js
// Phase 1: Basic data detection and extraction from Brightspace

console.log('🎓 uOttawa Brightspace Assistant content script loaded');

class BrightspaceDetector {
  constructor() {
    this.pageType = 'unknown';
    this.courseId = null;
    this.courseName = null;
    
    // Initialize detection
    this.detectPageType();
    this.detectCourseInfo();
  }
  
  detectPageType() {
    const url = window.location.href;
    const pathname = window.location.pathname;
    
    // Basic page type detection based on URL patterns
    if (url.includes('/grades/') || url.includes('my_grades')) {
      this.pageType = 'grades';
    } else if (url.includes('/news/') || url.includes('/announcements/')) {
      this.pageType = 'announcements';
    } else if (url.includes('/dropbox/') || url.includes('/assignments/')) {
      this.pageType = 'assignments';
    } else if (url.includes('/calendar/')) {
      this.pageType = 'calendar';
    } else if (url.includes('/content/')) {
      this.pageType = 'content';
    } else if (url.includes('/home/')) {
      this.pageType = 'homepage';
    } else if (pathname.includes('/d2l/le/')) {
      this.pageType = 'course_page';
    } else {
      this.pageType = 'other';
    }
    
    console.log('Detected page type:', this.pageType);
  }
  
  detectCourseInfo() {
    // Try to extract course ID from URL
    const urlMatch = window.location.href.match(/\/(\d+)\//);
    if (urlMatch) {
      this.courseId = urlMatch[1];
    }
    
    // Try to get course name from page
    const courseNameSelectors = [
      '.d2l-course-name',
      '.d2l-page-title',
      '.d2l-navigation-s-course-name',
      '[data-automation-id="course-name"]',
      '.navbar-course-title'
    ];
    
    for (const selector of courseNameSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        this.courseName = element.textContent.trim();
        break;
      }
    }
    
    console.log('Course info:', { id: this.courseId, name: this.courseName });
  }
  
  extractBasicPageData() {
    const data = {
      pageType: this.pageType,
      courseId: this.courseId,
      courseName: this.courseName,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      dataTypes: [],
      items: [],
      sampleData: {}
    };
    
    // Extract data based on page type
    switch (this.pageType) {
      case 'grades':
        data.items = this.extractGradesData();
        data.dataTypes.push('grades');
        break;
        
      case 'announcements':
        data.items = this.extractAnnouncementsData();
        data.dataTypes.push('announcements');
        break;
        
      case 'assignments':
        data.items = this.extractAssignmentsData();
        data.dataTypes.push('assignments');
        break;
        
      case 'calendar':
        data.items = this.extractCalendarData();
        data.dataTypes.push('calendar');
        break;
        
      case 'homepage':
        // Try to extract multiple types from homepage
        const homeGrades = this.extractGradesData();
        const homeAnnouncements = this.extractAnnouncementsData();
        const homeAssignments = this.extractAssignmentsData();
        
        if (homeGrades.length > 0) {
          data.items.push(...homeGrades);
          data.dataTypes.push('grades');
        }
        if (homeAnnouncements.length > 0) {
          data.items.push(...homeAnnouncements);
          data.dataTypes.push('announcements');
        }
        if (homeAssignments.length > 0) {
          data.items.push(...homeAssignments);
          data.dataTypes.push('assignments');
        }
        break;
        
      default:
        // Try to extract any available data
        data.items = this.extractGenericData();
        data.dataTypes.push('generic');
    }
    
    // Create sample data for testing
    data.sampleData = data.items.slice(0, 3); // First 3 items as sample
    data.itemCount = data.items.length;
    
    return data;
  }
  
  extractGradesData() {
    const grades = [];
    
    // Common selectors for grades in Brightspace
    const gradeSelectors = [
      '.d2l-grades-table-row',
      '.d2l-grade-result',
      '[data-automation-id*="grade"]',
      '.d2l-table-row-last'
    ];
    
    for (const selector of gradeSelectors) {
      const elements = document.querySelectorAll(selector);
      
      elements.forEach((element, index) => {
        const gradeData = this.extractGradeFromElement(element, index);
        if (gradeData) {
          grades.push(gradeData);
        }
      });
      
      if (grades.length > 0) break; // Found grades, stop trying other selectors
    }
    
    return grades;
  }
  
  extractGradeFromElement(element, index) {
    try {
      // Try to extract grade information from element
      const assignmentName = this.getTextFromSelectors(element, [
        '.d2l-link',
        '.d2l-assignment-name',
        '.d2l-grade-name',
        'a',
        'td:first-child'
      ]);
      
      const gradeValue = this.getTextFromSelectors(element, [
        '.d2l-grade',
        '.d2l-grade-value',
        '[data-automation-id*="grade"]',
        'td:last-child',
        '.d2l-grade-result'
      ]);
      
      const feedback = this.getTextFromSelectors(element, [
        '.d2l-feedback',
        '.d2l-grade-feedback',
        '.d2l-comment'
      ]);
      
      if (assignmentName || gradeValue) {
        return {
          type: 'grade',
          assignment: assignmentName || `Assignment ${index + 1}`,
          grade: gradeValue || 'Not graded',
          feedback: feedback || '',
          courseId: this.courseId,
          extractedAt: new Date().toISOString()
        };
      }
    } catch (error) {
      console.log('Error extracting grade:', error);
    }
    
    return null;
  }
  
  extractAnnouncementsData() {
    const announcements = [];
    
    const announcementSelectors = [
      '.d2l-news-item',
      '.d2l-announcement',
      '[data-automation-id*="news"]',
      '.d2l-widget-content'
    ];
    
    for (const selector of announcementSelectors) {
      const elements = document.querySelectorAll(selector);
      
      elements.forEach((element, index) => {
        const announcementData = this.extractAnnouncementFromElement(element, index);
        if (announcementData) {
          announcements.push(announcementData);
        }
      });
      
      if (announcements.length > 0) break;
    }
    
    return announcements;
  }
  
  extractAnnouncementFromElement(element, index) {
    try {
      const title = this.getTextFromSelectors(element, [
        '.d2l-news-title',
        '.d2l-announcement-title',
        'h3',
        'h4',
        '.d2l-link'
      ]);
      
      const content = this.getTextFromSelectors(element, [
        '.d2l-news-body',
        '.d2l-announcement-body',
        '.d2l-content',
        'p'
      ]);
      
      const date = this.getTextFromSelectors(element, [
        '.d2l-news-date',
        '.d2l-date',
        '[data-automation-id*="date"]'
      ]);
      
      if (title || content) {
        return {
          type: 'announcement',
          title: title || `Announcement ${index + 1}`,
          content: content ? content.substring(0, 200) + '...' : '',
          date: date || '',
          courseId: this.courseId,
          extractedAt: new Date().toISOString()
        };
      }
    } catch (error) {
      console.log('Error extracting announcement:', error);
    }
    
    return null;
  }
  
  extractAssignmentsData() {
    const assignments = [];
    
    const assignmentSelectors = [
      '.d2l-assignment-row',
      '.d2l-dropbox-item',
      '[data-automation-id*="assignment"]'
    ];
    
    for (const selector of assignmentSelectors) {
      const elements = document.querySelectorAll(selector);
      
      elements.forEach((element, index) => {
        const assignmentData = this.extractAssignmentFromElement(element, index);
        if (assignmentData) {
          assignments.push(assignmentData);
        }
      });
      
      if (assignments.length > 0) break;
    }
    
    return assignments;
  }
  
  extractAssignmentFromElement(element, index) {
    try {
      const name = this.getTextFromSelectors(element, [
        '.d2l-assignment-name',
        '.d2l-link',
        'a',
        'td:first-child'
      ]);
      
      const dueDate = this.getTextFromSelectors(element, [
        '.d2l-due-date',
        '.d2l-date',
        '[data-automation-id*="due"]'
      ]);
      
      const status = this.getTextFromSelectors(element, [
        '.d2l-status',
        '.d2l-assignment-status'
      ]);
      
      if (name) {
        return {
          type: 'assignment',
          name: name,
          dueDate: dueDate || '',
          status: status || 'Unknown',
          courseId: this.courseId,
          extractedAt: new Date().toISOString()
        };
      }
    } catch (error) {
      console.log('Error extracting assignment:', error);
    }
    
    return null;
  }
  
  extractCalendarData() {
    // Basic calendar extraction
    const events = [];
    
    const eventSelectors = [
      '.d2l-calendar-event',
      '.d2l-event',
      '[data-automation-id*="event"]'
    ];
    
    for (const selector of eventSelectors) {
      const elements = document.querySelectorAll(selector);
      
      elements.forEach((element, index) => {
        const title = this.getTextFromSelectors(element, [
          '.d2l-event-title',
          '.d2l-calendar-title'
        ]);
        
        if (title) {
          events.push({
            type: 'event',
            title: title,
            courseId: this.courseId,
            extractedAt: new Date().toISOString()
          });
        }
      });
      
      if (events.length > 0) break;
    }
    
    return events;
  }
  
  extractGenericData() {
    // Try to extract any structured data from the page
    const genericData = [];
    
    // Look for any lists or tables
    const lists = document.querySelectorAll('ul li, ol li, table tr');
    
    lists.forEach((element, index) => {
      if (index < 5) { // Limit to first 5 items
        const text = element.textContent?.trim();
        if (text && text.length > 10) {
          genericData.push({
            type: 'generic',
            content: text.substring(0, 100),
            courseId: this.courseId,
            extractedAt: new Date().toISOString()
          });
        }
      }
    });
    
    return genericData;
  }
  
  // Utility function to try multiple selectors
  getTextFromSelectors(element, selectors) {
    for (const selector of selectors) {
      const found = element.querySelector(selector);
      if (found && found.textContent?.trim()) {
        return found.textContent.trim();
      }
    }
    
    // If no child selectors work, try the element itself
    const text = element.textContent?.trim();
    if (text && text.length > 0) {
      return text;
    }
    
    return null;
  }
}

// Initialize detector
const detector = new BrightspaceDetector();

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Content script received message:', request);
  
  if (request.action === 'detectPage') {
    sendResponse({
      success: true,
      pageType: detector.pageType,
      courseId: detector.courseId,
      courseName: detector.courseName,
      url: window.location.href
    });
  }
  
  if (request.action === 'extractData') {
    try {
      const data = detector.extractBasicPageData();
      console.log('Extracted data:', data);
      
      sendResponse({
        success: true,
        ...data
      });
    } catch (error) {
      console.error('Error extracting data:', error);
      sendResponse({
        success: false,
        error: error.message
      });
    }
  }
  
  return true; // Keep message channel open for async response
});

// Auto-detect page changes (for single-page app navigation)
let lastUrl = window.location.href;
setInterval(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    console.log('Page changed, re-detecting...');
    detector.detectPageType();
    detector.detectCourseInfo();
  }
}, 1000);