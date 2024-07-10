
function setTheme(theme) {
    document.body.classList.remove('dark-theme');
    document.body.classList.add(theme);

    if (theme === 'dark-theme') {
      themeToggle.querySelector('span:nth-child(1)').classList.add('active');
      themeToggle.querySelector('span:nth-child(2)').classList.remove('active');
    } else {
      themeToggle.querySelector('span:nth-child(1)').classList.remove('active');
      themeToggle.querySelector('span:nth-child(2)').classList.add('active');
    }
  

    localStorage.setItem('theme', theme);
  }
  

  function getTheme() {
    return localStorage.getItem('theme');
  }
 
  const storedTheme = getTheme();
  if (storedTheme) {
    setTheme(storedTheme);
  }
  

  themeToggle.addEventListener('click', () => {
    const currentTheme = document.body.classList.contains('dark-theme') ? '' : 'dark-theme';
    setTheme(currentTheme);
  });
  