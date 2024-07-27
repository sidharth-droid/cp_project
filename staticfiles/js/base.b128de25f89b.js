const side = document.querySelector('aside');
const menu = document.querySelector("#menu-btn");
const close = document.querySelector("#c-btn");
const links = document.querySelectorAll(".sidebar a");
const currentDate = new Date();
const year = currentDate.getFullYear();
const month = String(currentDate.getMonth() + 1).padStart(2, "0");
const day = String(currentDate.getDate()).padStart(2, "0");

document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const themeToggler = document.querySelector('.theme-toggler');
    const lightModeIcon = document.querySelector('.material-icons-sharp.active');
    const darkModeIcon = document.querySelector('.material-icons-sharp:not(.active)');

    // Load the saved theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    body.setAttribute('data-theme', savedTheme);

    // Set the active class based on the saved theme
    if (savedTheme === 'dark') {
        lightModeIcon.classList.remove('active');
        darkModeIcon.classList.add('active');
    } else {
        lightModeIcon.classList.add('active');
        darkModeIcon.classList.remove('active');
    }

    // Toggle the theme and save the preference to localStorage
    themeToggler.addEventListener('click', function() {
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        // Update the active class for the icons
        if (newTheme === 'dark') {
            lightModeIcon.classList.remove('active');
            darkModeIcon.classList.add('active');
        } else {
            lightModeIcon.classList.add('active');
            darkModeIcon.classList.remove('active');
        }
    });
});
menu.addEventListener('click', () => {
    side.style.display = 'block';
    menu.style.display = 'none';
})
close.addEventListener('click', () => {
    side.style.display = 'none';
    menu.style.display = 'inline-block';
})


document.getElementById("todaydate").value = `${year}-${month}-${day}`;
function updateTime() {
    const currentTimeElement = document.getElementById("currentTime");
    const currentTime = new Date().toLocaleTimeString();
    currentTimeElement.textContent = ` Time: ${currentTime}`;
}
setInterval(updateTime, 1000);
updateTime();

links.forEach((link) => {
    link.addEventListener("click", (event) => {
        links.forEach((otherLink) => {
            otherLink.classList.remove("active");
        });
        link.classList.add("active");
    });
});


