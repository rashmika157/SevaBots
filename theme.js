function initHeaderControls() {
  if (document.querySelector('.top-right-controls')) return; // Avoid duplicates
  
  const container = document.createElement("div");
  container.className = "top-right-controls";

  // Create Language Dropdown
  const langSelect = document.createElement("select");
  langSelect.className = "lang-toggle-select";
  
  const options = [
    { text: '🌐 English', val: 'en' },
    { text: '🌐 Hindi', val: 'hi' },
    { text: '🌐 Kannada', val: 'kn' }
  ];
  
  options.forEach(opt => {
    const option = document.createElement("option");
    option.value = opt.val;
    option.textContent = opt.text;
    langSelect.appendChild(option);
  });
  
  // Default to english
  const currentLang = localStorage.getItem("lang") || "en";
  langSelect.value = currentLang;
  
  langSelect.addEventListener("change", (e) => {
    localStorage.setItem("lang", e.target.value);
    location.reload();
  });

  // Create Theme Toggle button
  const btn = document.createElement("button");
  btn.className = "theme-toggle-btn";
  
  // Set initial theme
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme === "dark") {
    document.documentElement.classList.add("dark-mode");
    btn.textContent = "☀️";
  } else {
    btn.textContent = "🌙";
  }

  // Toggle handler
  btn.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark-mode");
    const isDark = document.documentElement.classList.contains("dark-mode");
    btn.textContent = isDark ? "☀️" : "🌙";
    localStorage.setItem("theme", isDark ? "dark" : "light");
  });

  container.appendChild(langSelect);
  container.appendChild(btn);
  document.body.appendChild(container);
}

// Ensure execution regardless of load state
if (document.readyState === 'loading') {
  document.addEventListener("DOMContentLoaded", initHeaderControls);
} else {
  initHeaderControls();
}
