// Main JavaScript for AI Resume Analyzer & ATS Platform

document.addEventListener('DOMContentLoaded', function () {
  // 1. Toast Initialization
  const toastElList = [].slice.call(document.querySelectorAll('.toast'));
  toastElList.map(function (toastEl) {
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
  });

  // 2. Drag & Drop File Upload Handler
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('resume_file');
  const fileInfo = document.getElementById('file-info');
  const fileNameDisplay = document.getElementById('file-name-display');

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateFileName(files[0].name);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        updateFileName(fileInput.files[0].name);
      }
    });

    function updateFileName(name) {
      if (fileNameDisplay) {
        fileNameDisplay.textContent = name;
        if (fileInfo) fileInfo.classList.remove('d-none');
      }
    }
  }

  // 3. Loading overlay for AI / File processing forms
  const uploadForm = document.getElementById('upload-form');
  const jobMatchForm = document.getElementById('job-match-form');
  const improveForm = document.getElementById('improve-form');
  const builderForm = document.getElementById('builder-form');
  const loadingOverlay = document.getElementById('loading-overlay');
  const loadingText = document.getElementById('loading-text');

  function showLoading(text) {
    if (loadingOverlay) {
      if (loadingText) loadingText.textContent = text || 'Processing with AI...';
      loadingOverlay.style.display = 'flex';
    }
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', () => showLoading('Analyzing Resume & Extracting ATS Metrics...'));
  }
  if (jobMatchForm) {
    jobMatchForm.addEventListener('submit', () => showLoading('Comparing Skills & Matching Job Description...'));
  }
  if (improveForm) {
    improveForm.addEventListener('submit', () => showLoading('AI is Rewriting & Optimizing Your Content...'));
  }
  if (builderForm) {
    builderForm.addEventListener('submit', () => showLoading('Compiling ATS-Optimized PDF Resume...'));
  }

  // 4. Copy to Clipboard helper
  window.copyToClipboard = function (elementId, btn) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.value;
    navigator.clipboard.writeText(text).then(() => {
      const originalHTML = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
      btn.classList.add('btn-success');
      setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.classList.remove('btn-success');
      }, 2000);
    }).catch(err => {
      console.error('Copy failed: ', err);
    });
  };

  // 5. Dynamic Row Handlers for Resume Builder
  window.addExperienceRow = function () {
    const container = document.getElementById('experience-container');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'border rounded p-3 mb-3 bg-light position-relative item-card animate-fade-in';
    div.innerHTML = `
      <button type="button" class="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2" onclick="this.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
      <div class="row g-2 mb-2">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Job Title</label>
          <input type="text" name="exp_role[]" class="form-control form-control-sm" placeholder="e.g. Senior Software Engineer" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">Company</label>
          <input type="text" name="exp_company[]" class="form-control form-control-sm" placeholder="e.g. Google" required>
        </div>
      </div>
      <div class="row g-2 mb-2">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Dates / Duration</label>
          <input type="text" name="exp_duration[]" class="form-control form-control-sm" placeholder="e.g. Jan 2022 - Present">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">Location</label>
          <input type="text" name="exp_location[]" class="form-control form-control-sm" placeholder="e.g. New York, NY / Remote">
        </div>
      </div>
      <div>
        <label class="form-label small fw-bold">Description / Achievements (One per line)</label>
        <textarea name="exp_description[]" class="form-control form-control-sm" rows="3" placeholder="• Spearheaded development of...&#10;• Reduced latency by 35% using..."></textarea>
      </div>
    `;
    container.appendChild(div);
  };

  window.addProjectRow = function () {
    const container = document.getElementById('projects-container');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'border rounded p-3 mb-3 bg-light position-relative item-card animate-fade-in';
    div.innerHTML = `
      <button type="button" class="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2" onclick="this.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
      <div class="row g-2 mb-2">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Project Title</label>
          <input type="text" name="proj_title[]" class="form-control form-control-sm" placeholder="e.g. E-Commerce Microservices" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">Technologies Used</label>
          <input type="text" name="proj_tech[]" class="form-control form-control-sm" placeholder="e.g. Python, Flask, Redis, Docker">
        </div>
      </div>
      <div class="mb-2">
        <label class="form-label small fw-bold">Live Link / Repository URL</label>
        <input type="text" name="proj_link[]" class="form-control form-control-sm" placeholder="e.g. github.com/user/project">
      </div>
      <div>
        <label class="form-label small fw-bold">Project Description & Results</label>
        <textarea name="proj_description[]" class="form-control form-control-sm" rows="2" placeholder="• Architected full-stack pipeline handling 10k daily requests..."></textarea>
      </div>
    `;
    container.appendChild(div);
  };

  window.addEducationRow = function () {
    const container = document.getElementById('education-container');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'border rounded p-3 mb-3 bg-light position-relative item-card animate-fade-in';
    div.innerHTML = `
      <button type="button" class="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2" onclick="this.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
      <div class="row g-2 mb-2">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Degree / Major</label>
          <input type="text" name="edu_degree[]" class="form-control form-control-sm" placeholder="e.g. B.S. in Computer Science" required>
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">University / Institution</label>
          <input type="text" name="edu_school[]" class="form-control form-control-sm" placeholder="e.g. Stanford University" required>
        </div>
      </div>
      <div class="row g-2">
        <div class="col-md-6">
          <label class="form-label small fw-bold">Graduation Year / Period</label>
          <input type="text" name="edu_year[]" class="form-control form-control-sm" placeholder="e.g. 2020 - 2024">
        </div>
        <div class="col-md-6">
          <label class="form-label small fw-bold">GPA / Grade (Optional)</label>
          <input type="text" name="edu_score[]" class="form-control form-control-sm" placeholder="e.g. 3.9 / 4.0">
        </div>
      </div>
    `;
    container.appendChild(div);
  };
});
