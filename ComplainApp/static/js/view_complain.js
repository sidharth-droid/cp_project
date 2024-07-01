const side = document.querySelector('aside');
const menu = document.querySelector("#menu-btn");
const close = document.querySelector("#c-btn");
const themeToggle = document.querySelector('.theme-toggler');
const body = document.body;
const currentTheme = localStorage.getItem('theme');
const links = document.querySelectorAll(".sidebar a");
const currentDate = new Date();
const year = currentDate.getFullYear();
const month = String(currentDate.getMonth() + 1).padStart(2, "0");
const day = String(currentDate.getDate()).padStart(2, "0");


menu.addEventListener('click', () => {
    side.style.display = 'block';
})
close.addEventListener('click', () => {
    side.style.display = 'none';
})

if (currentTheme) {
    body.classList.add(currentTheme);
}
themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    if (body.classList.contains('dark-theme')) {
        localStorage.setItem('theme', 'dark-theme');
    } else {
        localStorage.setItem('theme', '');
    }
    themeToggle.querySelector('span:nth-child(1)').classList.toggle('active');
    themeToggle.querySelector('span:nth-child(2)').classList.toggle('active');
});


document.getElementById("todaydate").value = `${year}-${month}-${day}`;


links.forEach((link) => {
    link.addEventListener("click", (event) => {
        links.forEach((otherLink) => {
            otherLink.classList.remove("active");
        });
        link.classList.add("active");
    });
});


function updateTime() {
    const currentTimeElement = document.getElementById("currentTime");
    const currentTime = new Date().toLocaleTimeString();
    currentTimeElement.textContent = ` Time: ${currentTime}`;
}


setInterval(updateTime, 1000);
updateTime();




// themeToggle.addEventListener('click', () => {
//     document.body.classList.toggle('dark-theme');

//     themeToggle.querySelector('span:nth-child(1)').classList.toggle('active');
//     themeToggle.querySelector('span:nth-child(2)').classList.toggle('active');
// })