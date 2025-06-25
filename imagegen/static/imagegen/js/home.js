document.addEventListener('DOMContentLoaded', function() {
    // Navbar transparency control on scroll
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        const opacity = Math.max(0.3, 1 - (scrollPosition / 100));
        navbar.style.opacity = opacity;
    });
    
    // Floating UI animation
    const floatingUI = document.querySelector('.floating-ui');
    
    function animateFloatingUI() {
        let y = 0;
        let direction = 1;
        
        setInterval(() => {
            if (y >= 10) direction = -1;
            if (y <= 0) direction = 1;
            
            y += direction;
            floatingUI.style.transform = `translateY(${y}px)`;
        }, 50);
    }
    
    animateFloatingUI();
});