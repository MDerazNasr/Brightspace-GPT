// content-scripts/brightspace-detector.js
// Complete version using Brightspace API (Phase 2)

console.log('🎓 Brightspace GPT content script loaded');

class BrightspaceExtractor {
  constructor() {
    this.baseUrl = 'https://uottawa.brightspace.com';
    this.courses = [];
  }

  /**
   * Extract courses using Brightspace API (RECOMMENDED - more reliable)
   */
  async extractCoursesViaAPI() {
    try {
      console.log('📡 Fetching courses from Brightspace API...');
      const response = await fetch('https://uottawa.brightspace.com/d2l/api/lp/1.43/enrollments/myenrollments/');
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ API returned ${data.Items.length} enrollments`);
      
      const courses = data.Items.map(item => ({
        name: item.OrgUnit.Name,
        code: item.OrgUnit.Code,
        orgUnitId: item.OrgUnit.Id.toString(),
        homepage: `https://uottawa.brightspace.com/d2l/home/${item.OrgUnit.Id}`,
        type: item.OrgUnit.Type?.Name,
        isActive: item.Access?.IsActive || false,
        startDate: item.OrgUnit.StartDate || null,
        endDate: item.OrgUnit.EndDate || null
      }));
      
      this.courses = courses;
      console.log(`✅ Extracted ${courses.length} courses via API`);
      return courses;
      
    } catch (error) {
      console.error('❌ API extraction failed:', error);
      return [];
    }
  }

  /**
   * Main extraction method
   */
  async extractCourses() {
    return this.extractCoursesViaAPI();
  }

  /**
   * Fetch grades for a specific course via API
   */
  async fetchCourseGrades(orgUnitId) {
    try {
      console.log(`📊 Fetching grades for course ${orgUnitId}...`);
      const response = await fetch(`https://uottawa.brightspace.com/d2l/api/le/1.43/${orgUnitId}/grades/values/myGradeValues/`);
      
      if (!response.ok) {
        throw new Error(`Grades API returned ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ Fetched ${data.length} grade items`);
      
      return {
        orgUnitId,
        grades: data.map(item => ({
          name: item.GradeObjectName,
          displayedGrade: item.DisplayedGrade,
          pointsNumerator: item.PointsNumerator,
          pointsDenominator: item.PointsDenominator,
          weightedNumerator: item.WeightedNumerator,
          weightedDenominator: item.WeightedDenominator
        }))
      };
      
    } catch (error) {
      console.error(`❌ Error fetching grades for ${orgUnitId}:`, error);
      return { orgUnitId, error: error.message, grades: [] };
    }
  }

  /**
   * Fetch grades for all courses
   */
  async fetchAllGrades() {
    try {
      console.log('📊 Fetching grades for all courses...');
      const courses = await this.extractCourses();
      
      const gradesPromises = courses
        .filter(c => c.isActive)
        .map(c => this.fetchCourseGrades(c.orgUnitId));
      
      const allGrades = await Promise.all(gradesPromises);
      
      const gradesWithCourseNames = allGrades.map(gradeData => {
        const course = courses.find(c => c.orgUnitId === gradeData.orgUnitId);
        return {
          ...gradeData,
          courseName: course?.name,
          courseCode: course?.code
        };
      });
      
      console.log(`✅ Fetched grades for ${gradesWithCourseNames.length} courses`);
      return gradesWithCourseNames;
      
    } catch (error) {
      console.error('❌ Error fetching all grades:', error);
      return [];
    }
  }

  /**
   * Fetch assignments for a specific course via API
   */
  async fetchCourseAssignments(orgUnitId) {
    try {
      console.log(`📝 Fetching assignments for course ${orgUnitId}...`);
      const response = await fetch(`https://uottawa.brightspace.com/d2l/api/le/1.43/${orgUnitId}/dropbox/folders/`);
      
      if (!response.ok) {
        throw new Error(`Assignments API returned ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ Fetched ${data.length} assignment folders`);
      
      return {
        orgUnitId,
        assignments: data.map(item => ({
          name: item.Name,
          id: item.Id,
          dueDate: item.DueDate,
          isHidden: item.IsHidden
        }))
      };
      
    } catch (error) {
      console.error(`❌ Error fetching assignments for ${orgUnitId}:`, error);
      return { orgUnitId, error: error.message, assignments: [] };
    }
  }

  /**
   * Fetch assignments for all courses
   */
  async fetchAllAssignments() {
    try {
      console.log('📝 Fetching assignments for all courses...');
      const courses = await this.extractCourses();
      
      const assignmentsPromises = courses
        .filter(c => c.isActive)
        .map(c => this.fetchCourseAssignments(c.orgUnitId));
      
      const allAssignments = await Promise.all(assignmentsPromises);
      
      const assignmentsWithCourseNames = allAssignments.map(assignmentData => {
        const course = courses.find(c => c.orgUnitId === assignmentData.orgUnitId);
        return {
          ...assignmentData,
          courseName: course?.name,
          courseCode: course?.code
        };
      });
      
      console.log(`✅ Fetched assignments for ${assignmentsWithCourseNames.length} courses`);
      return assignmentsWithCourseNames;
      
    } catch (error) {
      console.error('❌ Error fetching all assignments:', error);
      return [];
    }
  }

  /**
   * Fetch announcements for a specific course via API
   */
  async fetchCourseAnnouncements(orgUnitId) {
    try {
      console.log(`📢 Fetching announcements for course ${orgUnitId}...`);
      const response = await fetch(`https://uottawa.brightspace.com/d2l/api/le/1.43/${orgUnitId}/news/`);
      
      if (!response.ok) {
        throw new Error(`Announcements API returned ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ Fetched ${data.length} announcements`);
      
      return {
        orgUnitId,
        announcements: data.map(item => ({
          title: item.Title,
          body: item.Body?.Text || '',
          publishDate: item.PublishedDate,
          isPublished: item.IsPublished
        }))
      };
      
    } catch (error) {
      console.error(`❌ Error fetching announcements for ${orgUnitId}:`, error);
      return { orgUnitId, error: error.message, announcements: [] };
    }
  }

  /**
   * Fetch announcements for all courses
   */
  async fetchAllAnnouncements() {
    try {
      console.log('📢 Fetching announcements for all courses...');
      const courses = await this.extractCourses();
      
      const announcementsPromises = courses
        .filter(c => c.isActive)
        .map(c => this.fetchCourseAnnouncements(c.orgUnitId));
      
      const allAnnouncements = await Promise.all(announcementsPromises);
      
      const announcementsWithCourseNames = allAnnouncements.map(announcementData => {
        const course = courses.find(c => c.orgUnitId === announcementData.orgUnitId);
        return {
          ...announcementData,
          courseName: course?.name,
          courseCode: course?.code
        };
      });
      
      console.log(`✅ Fetched announcements for ${announcementsWithCourseNames.length} courses`);
      return announcementsWithCourseNames;
      
    } catch (error) {
      console.error('❌ Error fetching all announcements:', error);
      return [];
    }
  }

  /**
   * Extract grades from grades page (fallback)
   */
  extractGrades() {
    const grades = [];
    
    try {
      if (!window.location.href.includes('/grades/')) {
        return { error: 'Not on grades page' };
      }

      const gradeRows = document.querySelectorAll('.d2l-table tbody tr, table.d_ggl tbody tr');
      
      gradeRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 3) {
          grades.push({
            item: cells[0]?.textContent.trim(),
            grade: cells[1]?.textContent.trim(),
            outOf: cells[2]?.textContent.trim(),
            weight: cells[3]?.textContent.trim(),
            feedback: cells[4]?.textContent.trim()
          });
        }
      });

      return {
        grades,
        courseId: this.extractCourseIdFromUrl(),
        extractedAt: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('Error extracting grades:', error);
      return { error: error.message };
    }
  }

  /**
   * Extract announcements (fallback)
   */
  extractAnnouncements() {
    const announcements = [];
    
    try {
      const announcementItems = document.querySelectorAll('d2l-labs-list-item, .d2l-homepage-announcement');
      
      announcementItems.forEach(item => {
        const title = item.querySelector('.d2l-heading, h3, h4')?.textContent.trim();
        const date = item.querySelector('.d2l-timestamp, time')?.textContent.trim();
        const content = item.querySelector('.d2l-htmlblock-untrusted, .d2l-body')?.textContent.trim();
        
        if (title) {
          announcements.push({
            title,
            date,
            content: content?.substring(0, 500),
            url: window.location.href
          });
        }
      });

      return {
        announcements,
        courseId: this.extractCourseIdFromUrl(),
        extractedAt: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('Error extracting announcements:', error);
      return { error: error.message };
    }
  }

  /**
   * Extract assignments (fallback)
   */
  extractAssignments() {
    const assignments = [];
    
    try {
      const assignmentRows = document.querySelectorAll('.d2l-datalist-item, d2l-table tbody tr');
      
      assignmentRows.forEach(row => {
        const titleEl = row.querySelector('.d2l-link, a');
        const dueDateEl = row.querySelector('.d2l-date, time, .d2l-due-date');
        const statusEl = row.querySelector('.d2l-status, .d2l-grade-value');
        
        if (titleEl) {
          assignments.push({
            title: titleEl.textContent.trim(),
            dueDate: dueDateEl?.textContent.trim(),
            status: statusEl?.textContent.trim(),
            url: titleEl.href,
            courseId: this.extractCourseIdFromUrl()
          });
        }
      });

      return {
        assignments,
        courseId: this.extractCourseIdFromUrl(),
        extractedAt: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('Error extracting assignments:', error);
      return { error: error.message };
    }
  }

  /**
   * Extract course ID from URL
   */
  extractCourseIdFromUrl() {
    const match = window.location.pathname.match(/\/(\d+)\//);
    return match ? match[1] : null;
  }

  /**
   * Detect current page type
   */
  detectPageType() {
    const path = window.location.pathname;
    
    if (path.includes('/home')) return 'home';
    if (path.includes('/grades')) return 'grades';
    if (path.includes('/dropbox') || path.includes('/assignments')) return 'assignments';
    if (path.includes('/news')) return 'announcements';
    if (path.includes('/content')) return 'content';
    if (path.includes('/calendar')) return 'calendar';
    
    return 'unknown';
  }

  /**
   * Extract all relevant data from current page
   */
  async extractCurrentPageData() {
    const pageType = this.detectPageType();
    const data = {
      pageType,
      url: window.location.href,
      courseId: this.extractCourseIdFromUrl(),
      timestamp: new Date().toISOString()
    };

    switch (pageType) {
      case 'home':
        data.courses = await this.extractCourses();
        data.announcements = this.extractAnnouncements();
        break;
      case 'grades':
        data.grades = this.extractGrades();
        break;
      case 'assignments':
        data.assignments = this.extractAssignments();
        break;
      case 'announcements':
        data.announcements = this.extractAnnouncements();
        break;
      default:
        data.courses = await this.extractCourses();
    }

    return data;
  }
}

// Initialize extractor
const extractor = new BrightspaceExtractor();

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📩 Received message:', request.action);
  
  if (request.action === 'ping') {
    console.log('✅ Responding to ping');
    sendResponse({ status: 'ok' });
    return true;
  }
  
  if (request.action === 'extractData') {
    console.log('📊 Extracting data...');
    extractor.extractCurrentPageData().then(data => {
      console.log('✅ Data extracted:', data);
      sendResponse(data);
    });
    return true;
  }
  
  if (request.action === 'extractCourses') {
    console.log('📚 Extracting courses via API...');
    extractor.extractCourses().then(courses => {
      console.log('✅ Courses extracted:', courses.length);
      sendResponse({ courses });
    });
    return true;
  }
  
  if (request.action === 'fetchAllGrades') {
    console.log('📊 Fetching all grades...');
    extractor.fetchAllGrades().then(grades => {
      console.log('✅ Grades fetched');
      sendResponse({ grades });
    });
    return true;
  }
  
  if (request.action === 'fetchAllAssignments') {
    console.log('📝 Fetching all assignments...');
    extractor.fetchAllAssignments().then(assignments => {
      console.log('✅ Assignments fetched');
      sendResponse({ assignments });
    });
    return true;
  }
  
  if (request.action === 'fetchAllAnnouncements') {
    console.log('📢 Fetching all announcements...');
    extractor.fetchAllAnnouncements().then(announcements => {
      console.log('✅ Announcements fetched');
      sendResponse({ announcements });
    });
    return true;
  }
  
  return true;
});

// Auto-extract when page loads
function initExtraction() {
  setTimeout(async () => {
    const data = await extractor.extractCurrentPageData();
    console.log('📚 Brightspace GPT - Auto-extracted data:', data);
    
    if (data.courses?.length > 0 || data.grades || data.assignments) {
      chrome.storage.local.set({
        'brightspace_latest_data': data,
        'brightspace_courses': data.courses || []
      });
    }
  }, 3000);
}

// Run extraction when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initExtraction);
} else {
  initExtraction();
}

// Re-extract when navigation occurs
let lastUrl = window.location.href;
new MutationObserver(() => {
  const url = window.location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    console.log('🔄 URL changed, re-extracting...');
    initExtraction();
  }
}).observe(document, { subtree: true, childList: true });

console.log('✅ Brightspace GPT content script ready');