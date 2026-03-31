document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    const auth = document.querySelector('.auth');

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('active');
            // Check if auth container exists before trying to toggle it
            if (auth) {
                auth.classList.toggle('active');
            }
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target) && (!auth || !auth.contains(e.target))) {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            if (auth) {
                auth.classList.remove('active');
            }
        }
    });

    // Close menu when clicking a link
    const links = document.querySelectorAll('.nav-links a');
    links.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            if (auth) {
                auth.classList.remove('active');
            }
        });
    });
});
