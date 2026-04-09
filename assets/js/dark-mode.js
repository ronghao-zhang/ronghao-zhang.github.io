(function () {
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  // Enable transitions only after the initial theme is applied,
  // so there is no flash when the page first loads.
  function enableTransitions() {
    root.classList.add('theme-ready');
  }

  // Expose toggle function for the button onclick handler.
  window.toggleDarkMode = function () {
    var current = root.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  };

  // Mark transitions as allowed once the page has fully painted.
  if (document.readyState === 'complete') {
    enableTransitions();
  } else {
    window.addEventListener('load', enableTransitions);
  }
})();
