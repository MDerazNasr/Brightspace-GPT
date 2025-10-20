// content-scripts/brightspace-detector.js
// Complete version using Brightspace API (more reliable than Shadow DOM)

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
      
      // Filter to only active courses (optional)
      // const activeCourses = courses.filter(c => c.isActive);
      
      this.courses = courses;
      console.log(`✅ Extracted ${courses.length} courses via API`);
      return courses;
      
    } catch (error) {
      console.error('❌ API extraction failed:', error);
      console.log('⚠️ Falling back to Shadow DOM extraction...');
      // Fallback to Shadow DOM method
      return this.extractCoursesViaShadowDOM();
    }
  }

  /**
   * Extract courses from Shadow DOM (FALLBACK - has timing issues)
   */
  async extractCoursesViaShadowDOM() {
    return new Promise((resolve) => {
      const maxRetries = 10;
      let attempt = 0;
      
      const tryExtract = () => {
        try {
          attempt++;
          console.log(`🔄 Shadow DOM extraction attempt ${attempt}/${maxRetries}`);
          
          const courses = [];
          
          const myCoursesWidget = document.querySelector('d2l-my-courses');
          if (!myCoursesWidget?.shadowRoot) {
            console.log('❌ d2l-my-courses not found');
            if (attempt < maxRetries) {
              setTimeout(tryExtract, 1000);
              return;
            }
            resolve([]);
            return;
          }
          
          const container = myCoursesWidget.shadowRoot.querySelector('d2l-my-courses-container');
          if (!container?.shadowRoot) {
            console.log('❌ d2l-my-courses-container not found');
            if (attempt < maxRetries) {
              setTimeout(tryExtract, 1000);
              return;
            }
            resolve([]);
            return;
          }
          
          const contentPanels = container.shadowRoot.querySelectorAll('d2l-my-courses-content');
          console.log(`✅ Found ${contentPanels.length} content panels`);
          
          let foundDataInAnyPanel = false;
          
          contentPanels.forEach((panel, panelIndex) => {
            if (!panel.shadowRoot) return;
            
            const cardGrid = panel.shadowRoot.querySelector('d2l-my-courses-card-grid');
            if (!cardGrid?.shadowRoot) return;
            
            const enrollmentCards = cardGrid.shadowRoot.querySelectorAll('d2l-enrollment-card');
            
            enrollmentCards.forEach((card) => {
              try {
                const org = card._organization;
                const enrollment = card._enrollment;
                
                if (!org || !org.properties) {
                  return;
                }
                
                foundDataInAnyPanel = true;
                
                const courseData = {
                  name: org.properties.name || 'Unknown Course',
                  code: org.properties.code || 'N/A',
                  orgUnitId: org.properties.orgUnitId || null,
                  homepage: org._linksByRel?.['https://api.brightspace.com/rels/organization-homepage']?.[0]?.href,
                  gradesUrl: enrollment?.links?.find(link => link.rel?.includes('user-course-grades'))?.href,
                  finalGradeUrl: enrollment?.links?.find(link => link.rel?.includes('user-final-grade'))?.href,
                  startDate: org.properties.startDate || null,
                  endDate: org.properties.endDate || null,
                  isActive: org.properties.isActive !== false
                };
                
                courses.push(courseData);
              } catch (error) {
                console.error(`❌ Error extracting card:`, error);
              }
            });
          });
          
          if (courses.length > 0) {
            console.log(`✅ Shadow DOM extracted ${courses.length} courses`);
            this.courses = courses;
            resolve(courses);
          } else if (foundDataInAnyPanel) {
            console.log(`⚠️ Found data but extracted 0 courses`);
            if (attempt < maxRetries) {
              setTimeout(tryExtract, 1000);
            } else {
              resolve([]);
            }
          } else {
            console.log(`⏳ No course data loaded yet (attempt ${attempt}/${maxRetries})`);
            if (attempt < maxRetries) {
              setTimeout(tryExtract, 1000);
            } else {
              console.log('❌ Gave up after', maxRetries, 'attempts');
              resolve([]);
            }
          }
          
        } catch (error) {
          console.error('❌ Error in Shadow DOM extraction:', error);
          if (attempt < maxRetries) {
            setTimeout(tryExtract, 1000);
          } else {
            resolve([]);
          }
        }
      };
      
      tryExtract();
    });
  }

  /**
   * Main extraction method - tries API first, falls back to Shadow DOM
   */
  async extractCourses() {
    return this.extractCoursesViaAPI();
  }

  /**
   * Extract grades from grades page
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
   * Extract announcements
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
   * Extract assignments
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
    return true; // Keep channel open for async
  }
  
  if (request.action === 'extractCourses') {
    console.log('📚 Extracting courses via API...');
    extractor.extractCourses().then(courses => {
      console.log('✅ Courses extracted:', courses.length);
      sendResponse({ courses });
    });
    return true; // Keep channel open for async
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
  }, 3000); // Wait 3 seconds for page to settle
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