/**
 * 薄雾咖啡 · MISTY ROAST
 * Interactive JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    initScrollAnimations();
    initCircleText();
    initSmoothScroll();
    initNavBackground();
    initFormInteraction();
});

/**
 * Scroll-triggered animations using Intersection Observer
 */
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');

                // Staggered animation for children
                const children = entry.target.querySelectorAll('.stagger-item');
                children.forEach((child, index) => {
                    child.style.animationDelay = `${index * 0.1}s`;
                    child.classList.add('animate-in');
                });
            }
        });
    }, observerOptions);

    // Observe sections
    const sections = document.querySelectorAll('.story, .menu, .space, .contact');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(40px)';
        section.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(section);
    });

    // Add animate-in styles
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Create circular rotating text in hero section
 */
function initCircleText() {
    const circleTextContainer = document.querySelector('.circle-text');
    if (!circleTextContainer) return;

    const text = circleTextContainer.textContent.trim();
    const chars = text.split('');

    circleTextContainer.innerHTML = '';

    chars.forEach((char, i) => {
        const span = document.createElement('span');
        span.textContent = char;
        span.style.cssText = `
            position: absolute;
            left: 50%;
            top: 0;
            transform-origin: 0 150px;
            transform: rotate(${i * (360 / chars.length)}deg);
        `;
        circleTextContainer.appendChild(span);
    });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = 100;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Dynamic navigation background on scroll
 */
function initNavBackground() {
    const nav = document.querySelector('.nav');
    if (!nav) return;

    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            nav.style.background = 'rgba(245, 240, 232, 0.95)';
            nav.style.backdropFilter = 'blur(10px)';
            nav.style.boxShadow = '0 2px 20px rgba(26, 20, 18, 0.05)';
        } else {
            nav.style.background = 'linear-gradient(to bottom, rgba(245, 240, 232, 1) 0%, transparent 100%)';
            nav.style.backdropFilter = 'none';
            nav.style.boxShadow = 'none';
        }

        // Hide/show nav on scroll direction
        if (currentScroll > lastScroll && currentScroll > 300) {
            nav.style.transform = 'translateY(-100%)';
        } else {
            nav.style.transform = 'translateY(0)';
        }

        nav.style.transition = 'transform 0.3s ease, background 0.3s ease, box-shadow 0.3s ease';
        lastScroll = currentScroll;
    });
}

/**
 * Form interaction enhancements
 */
function initFormInteraction() {
    const form = document.querySelector('.contact-form form');
    if (!form) return;

    // Add floating label effect
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', () => {
            if (!input.value) {
                input.parentElement.classList.remove('focused');
            }
        });
    });

    // Form submission
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('.form-submit');
        const originalText = submitBtn.textContent;

        submitBtn.textContent = '提交中...';
        submitBtn.disabled = true;

        // Simulate submission
        setTimeout(() => {
            submitBtn.textContent = '预约成功 ✓';
            submitBtn.style.background = '#8b6914';

            setTimeout(() => {
                form.reset();
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                submitBtn.style.background = '';
            }, 2000);
        }, 1500);
    });
}

/**
 * Parallax effect for hero section (optional enhancement)
 */
function initParallax() {
    const hero = document.querySelector('.hero');
    if (!hero) return;

    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroContent = hero.querySelector('.hero-content');
        const heroVisual = hero.querySelector('.hero-visual');

        if (heroContent) {
            heroContent.style.transform = `translateY(${scrolled * 0.2}px)`;
            heroContent.style.opacity = 1 - (scrolled / 600);
        }

        if (heroVisual) {
            heroVisual.style.transform = `translateY(${scrolled * 0.3}px)`;
        }
    });
}

// Initialize parallax if desired
// Uncomment the line below to enable
// initParallax();
