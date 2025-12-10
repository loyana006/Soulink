/**
 * Soulink Frontend JavaScript
 * This file contains all custom JavaScript for interactive elements,
 * like navigation behavior, form validation, and feature logic.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Example: Add a scroll listener to shrink the navbar on scroll (for non-dashboard pages)
    const navbar = document.querySelector('.navbar-custom');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Since the dashboard uses a sidebar, this script is minimal. 
    // Page-specific JS (like journal submission logic) should be in the respective HTML file 
    // or loaded via a module on that page.
});