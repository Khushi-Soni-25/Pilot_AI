const state = {
  optionsLoaded: false,
};

const fallbackOptions = {
  domains: [
    "Any",
    "Machine Learning",
    "Data Science",
    "Natural Language Processing",
    "Healthcare AI",
    "Agriculture AI",
  ],
  skill_levels: ["Any", "Beginner", "Intermediate", "Advanced"],
  available_times: ["Any", "1-2 weeks", "2-3 weeks", "3-4 weeks", "4-5 weeks", "5-6 weeks"],
  preferred_languages: ["Any", "Python"],
};

const elements = {
  navToggle: document.querySelector(".nav-toggle"),
  navLinks: document.querySelector(".nav-links"),
  form: document.querySelector("#preferenceForm"),
  domain: document.querySelector("#domain"),
  skillLevel: document.querySelector("#skillLevel"),
  interests: document.querySelector("#interests"),
  availableTime: document.querySelector("#availableTime"),
  preferredLanguage: document.querySelector("#preferredLanguage"),
  topN: document.querySelector("#topN"),
  topNValue: document.querySelector("#topNValue"),
  formError: document.querySelector("#formError"),
  apiStatus: document.querySelector("#apiStatus"),
  loadingState: document.querySelector("#loadingState"),
  emptyState: document.querySelector("#emptyState"),
  resultsGrid: document.querySelector("#resultsGrid"),
  projectDetails: document.querySelector("#projectDetails"),
  detailTitle: document.querySelector("#detailTitle"),
  detailDescription: document.querySelector("#detailDescription"),
  detailMeta: document.querySelector("#detailMeta"),
  closeDetails: document.querySelector("#closeDetails"),
};

document.addEventListener("DOMContentLoaded", init);

function init() {
  bindEvents();
  populateFallbackOptions();
  loadBackendOptions();
  checkBackendHealth();
}

function bindEvents() {
  elements.navToggle.addEventListener("click", () => {
    elements.navLinks.classList.toggle("open");
  });

  document.querySelectorAll(".nav-links a").forEach((link) => {
    link.addEventListener("click", () => elements.navLinks.classList.remove("open"));
  });

  elements.topN.addEventListener("input", () => {
    elements.topNValue.textContent = elements.topN.value;
  });

  elements.form.addEventListener("submit", handleRecommendationSubmit);
  elements.closeDetails.addEventListener("click", () => {
    elements.projectDetails.classList.add("hidden");
  });

  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tab));
  });
}

function populateFallbackOptions() {
  populateSelect(elements.domain, fallbackOptions.domains);
  populateSelect(elements.skillLevel, fallbackOptions.skill_levels);
  populateSelect(elements.availableTime, fallbackOptions.available_times);
  populateSelect(elements.preferredLanguage, fallbackOptions.preferred_languages);
}

async function loadBackendOptions() {
  try {
    const options = await ProjectPilotAPI.options();
    populateSelect(elements.domain, ["Any", ...options.domains]);
    populateSelect(elements.skillLevel, ["Any", ...options.skill_levels]);
    populateSelect(elements.availableTime, ["Any", ...options.available_times]);
    populateSelect(elements.preferredLanguage, ["Any", ...options.preferred_languages]);
    state.optionsLoaded = true;
  } catch {
    state.optionsLoaded = false;
  }
}

async function checkBackendHealth() {
  try {
    const health = await ProjectPilotAPI.health();
    setApiStatus(`API online · ${health.total_projects} projects`, "online");
  } catch {
    setApiStatus("API offline", "offline");
  }
}

function populateSelect(selectElement, values) {
  selectElement.innerHTML = values
    .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
    .join("");
}

async function handleRecommendationSubmit(event) {
  event.preventDefault();
  clearError();

  const payload = getFormPayload();
  const validationMessage = validatePayload(payload);

  if (validationMessage) {
    showError(validationMessage);
    return;
  }

  setLoading(true);

  try {
    const data = await ProjectPilotAPI.recommend(payload);
    renderRecommendations(data.recommendations);
    setApiStatus("API online", "online");
  } catch (error) {
    renderApiError(error.message);
    setApiStatus("API offline", "offline");
  } finally {
    setLoading(false);
  }
}

function getFormPayload() {
  return {
    domain: elements.domain.value,
    skill_level: elements.skillLevel.value,
    interests: elements.interests.value.trim(),
    available_time: elements.availableTime.value,
    preferred_language: elements.preferredLanguage.value,
    top_n: Number(elements.topN.value),
  };
}

function validatePayload(payload) {
  if (!payload.domain) return "Please choose a domain.";
  if (!payload.skill_level) return "Please choose your skill level.";
  if (!payload.interests || payload.interests.length < 2) {
    return "Please enter at least one clear interest.";
  }
  if (!payload.available_time) return "Please choose your available time.";
  if (!payload.preferred_language) return "Please choose a programming language.";
  return "";
}

function setLoading(isLoading) {
  elements.loadingState.classList.toggle("hidden", !isLoading);
  elements.resultsGrid.classList.toggle("hidden", isLoading);

  if (isLoading) {
    elements.emptyState.classList.add("hidden");
  }
}

function renderRecommendations(recommendations) {
  elements.projectDetails.classList.add("hidden");

  if (!recommendations.length) {
    elements.resultsGrid.innerHTML = "";
    elements.emptyState.classList.remove("hidden");
    elements.emptyState.innerHTML = `
      <strong>No matching projects found.</strong>
      <p>Try using broader interests or choosing "Any" in the dropdowns.</p>
    `;
    return;
  }

  elements.emptyState.classList.add("hidden");
  elements.resultsGrid.classList.remove("hidden");
  elements.resultsGrid.innerHTML = recommendations.map(createProjectCard).join("");

  document.querySelectorAll("[data-project-id]").forEach((button) => {
    button.addEventListener("click", () => loadProjectDetails(button.dataset.projectId));
  });
}

function createProjectCard(project) {
  return `
    <article class="project-card">
      <div class="card-top">
        <div>
          <div class="badge-row">
            <span class="badge">${escapeHtml(project.skill_level)}</span>
            <span class="badge purple">${escapeHtml(getCategory(project.domain))}</span>
          </div>
          <h3>${escapeHtml(project.title)}</h3>
        </div>
        <span class="match-score">${project.match_percentage}%</span>
      </div>
      <p>${escapeHtml(project.description)}</p>
      <div class="badge-row">
        <span class="badge green">${escapeHtml(project.available_time)}</span>
        <span class="badge">${escapeHtml(project.domain)}</span>
        <span class="badge">${escapeHtml(project.preferred_language)}</span>
      </div>
      <div class="card-actions">
        <small>Estimated duration · ${escapeHtml(project.available_time)}</small>
        <button class="text-button" type="button" data-project-id="${escapeHtml(project.project_id)}">
          View Details →
        </button>
      </div>
    </article>
  `;
}

async function loadProjectDetails(projectId) {
  elements.projectDetails.classList.remove("hidden");
  elements.detailTitle.textContent = "Loading project details...";
  elements.detailDescription.textContent = "";
  elements.detailMeta.innerHTML = "";

  try {
    const project = await ProjectPilotAPI.project(projectId);
    renderProjectDetails(project);
    elements.projectDetails.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    elements.detailTitle.textContent = "Could not load project details";
    elements.detailDescription.textContent = error.message;
  }
}

function renderProjectDetails(project) {
  elements.detailTitle.textContent = project.title;
  elements.detailDescription.textContent = project.description;
  elements.detailMeta.innerHTML = `
    <span class="badge">${escapeHtml(project.skill_level)}</span>
    <span class="badge green">${escapeHtml(project.available_time)}</span>
    <span class="badge purple">${escapeHtml(project.domain)}</span>
    <span class="badge">${escapeHtml(project.preferred_language)}</span>
  `;

  renderInfoBlocks("tab-roadmap", [
    ["Learning Roadmap", project.learning_roadmap],
  ]);
  renderInfoBlocks("tab-skills", [
    ["Skills Required", project.required_skills],
    ["Required Libraries", project.required_libraries],
  ]);
  renderInfoBlocks("tab-resources", [
    ["Free Dataset Links", project.free_datasets],
    ["Free API Information", project.free_apis],
    ["Learning Resources", project.learning_resources],
  ]);
  renderInfoBlocks("tab-future", [
    ["Future Scope", project.future_scope],
  ]);

  activateTab("roadmap");
}

function renderInfoBlocks(containerId, sections) {
  const container = document.querySelector(`#${containerId}`);
  container.innerHTML = sections
    .map(([title, items]) => {
      const listItems = items.length
        ? items.map((item) => `<li>${linkify(escapeHtml(item))}</li>`).join("")
        : "<li>Not required</li>";

      return `
        <article class="info-block">
          <h3>${escapeHtml(title)}</h3>
          <ul>${listItems}</ul>
        </article>
      `;
    })
    .join("");
}

function activateTab(tabName) {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });

  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.toggle("active", content.id === `tab-${tabName}`);
  });
}

function renderApiError(message) {
  elements.resultsGrid.innerHTML = "";
  elements.emptyState.classList.remove("hidden");
  elements.emptyState.innerHTML = `
    <strong>Unable to reach the backend.</strong>
    <p>${escapeHtml(message)} Make sure FastAPI is running at http://127.0.0.1:8000.</p>
  `;
}

function setApiStatus(message, status) {
  elements.apiStatus.textContent = message;
  elements.apiStatus.classList.remove("online", "offline");
  elements.apiStatus.classList.add(status);
}

function showError(message) {
  elements.formError.textContent = message;
}

function clearError() {
  elements.formError.textContent = "";
}

function getCategory(domain) {
  const normalized = domain.toLowerCase();
  if (normalized.includes("natural language")) return "NLP";
  if (normalized.includes("machine")) return "ML";
  if (normalized.includes("data")) return "Analytics";
  if (normalized.includes("health")) return "Healthcare";
  if (normalized.includes("agriculture")) return "Sustainability";
  return "AI Project";
}

function linkify(text) {
  if (text.startsWith("http://") || text.startsWith("https://")) {
    return `<a href="${text}" target="_blank" rel="noreferrer">${text}</a>`;
  }
  return text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
