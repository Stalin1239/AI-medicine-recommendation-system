// MediOps — Cyberpunk Beauty Injector v3.0
// Smooth fonts, aurora effects, magnetic interactions, premium polish
(function() {
    'use strict';

    // 1. Scanline overlay
    if (!document.querySelector('.scanline-overlay')) {
        const scanline = document.createElement('div');
        scanline.className = 'scanline-overlay';
        document.body.insertBefore(scanline, document.body.firstChild);
    }

    // 2. Floating Medical Stickers — More variety & beauty
    const stickers = ['💊','🏥','🚑','🩺','🔬','💉','🧬','🫀','🩻','❤️','🌡️','🧪','🥼','⚕️','🫁','🩸','🫶','⭐','✨','💫'];
    const stickerContainer = document.createElement('div');
    stickerContainer.className = 'med-stickers-container';
    document.body.appendChild(stickerContainer);

    function createSticker() {
        const s = document.createElement('div');
        s.className = 'med-sticker';
        s.textContent = stickers[Math.floor(Math.random() * stickers.length)];
        s.style.position = 'absolute';
        s.style.left = (5 + Math.random() * 90) + 'vw';
        s.style.bottom = '-80px';
        s.style.fontSize = (18 + Math.random() * 26) + 'px';
        s.style.pointerEvents = 'none';
        const dur = 18 + Math.random() * 22;
        s.style.animationDuration = dur + 's';
        s.style.animationDelay = (Math.random() * 3) + 's';
        stickerContainer.appendChild(s);
        setTimeout(() => s.remove(), (dur + 4) * 1000);
    }

    for (let i = 0; i < 10; i++) setTimeout(createSticker, i * 700);
    setInterval(createSticker, 2200);

    // 3. Particle Dots — Beautiful neon dust
    const pc = document.createElement('div');
    pc.className = 'particles-container';
    document.body.appendChild(pc);

    const colors = ['#00D4FF', '#8B5CF6', '#FF6B9D', '#10B981', '#F59E0B'];
    for (let i = 0; i < 35; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const color = colors[Math.floor(Math.random() * colors.length)];
        p.style.cssText = `
            position: absolute;
            left: ${Math.random() * 100}vw;
            bottom: -10px;
            width: ${2 + Math.random() * 4}px;
            height: ${2 + Math.random() * 4}px;
            background: ${color};
            box-shadow: 0 0 8px ${color};
            border-radius: 50%;
            animation-duration: ${12 + Math.random() * 20}s;
            animation-delay: ${Math.random() * 12}s;
        `;
        pc.appendChild(p);
    }

    // 4. 3D Mouse-tracking Tilt on Cards
    function addTiltEffect(el) {
        el.addEventListener('mousemove', e => {
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const cx = rect.width / 2;
            const cy = rect.height / 2;
            const rx = ((y - cy) / cy) * -6;
            const ry = ((x - cx) / cx) * 6;
            el.style.transform = `perspective(1200px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px) scale(1.015)`;
            el.style.boxShadow = `0 20px 50px rgba(0,212,255,0.18), ${ry > 0 ? -1 : 1}${Math.abs(ry)}px 0 15px rgba(139,92,246,0.1)`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = '';
            el.style.boxShadow = '';
        });
    }

    // Apply tilt to all glass-cards and stat-cards
    function applyTilts() {
        document.querySelectorAll('.glass-card:not(.no-tilt), .stat-card:not(.no-tilt)').forEach(card => {
            if (!card.dataset.tiltApplied) {
                addTiltEffect(card);
                card.dataset.tiltApplied = 'true';
            }
        });
    }
    applyTilts();
    // Re-apply when content is added dynamically
    const mo = new MutationObserver(applyTilts);
    mo.observe(document.body, { childList: true, subtree: true });

    // 5. Magnetic button effect — Buttons slightly follow cursor
    function addMagneticEffect(btn) {
        btn.addEventListener('mousemove', e => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.18}px, ${y * 0.18}px) scale(1.04)`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    }

    function applyMagnetic() {
        document.querySelectorAll('.btn-neon:not([data-mag])').forEach(btn => {
            addMagneticEffect(btn);
            btn.dataset.mag = 'true';
        });
    }
    applyMagnetic();
    mo.observe(document.body, { childList: true, subtree: true });

    // 6. Ripple effect on button clicks
    document.addEventListener('click', e => {
        const btn = e.target.closest('.btn-neon');
        if (!btn) return;
        const ripple = document.createElement('span');
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 1.5;
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px; height: ${size}px;
            left: ${e.clientX - rect.left - size/2}px;
            top: ${e.clientY - rect.top - size/2}px;
            background: rgba(255,255,255,0.35);
            border-radius: 50%;
            pointer-events: none;
            animation: rippleEffect 0.6s ease-out forwards;
        `;
        // Ensure btn has relative positioning
        const oldPos = btn.style.position;
        if (!oldPos) btn.style.position = 'relative';
        btn.style.overflow = 'hidden';
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 700);
    });

    // Inject ripple keyframe
    const style = document.createElement('style');
    style.textContent = `
        @keyframes rippleEffect {
            from { transform: scale(0); opacity: 1; }
            to   { transform: scale(1); opacity: 0; }
        }
        /* Fix font to use Sora instead of Orbitron/blocky fonts */
        * {
            font-feature-settings: 'kern' 1, 'liga' 1;
            -webkit-font-smoothing: antialiased;
        }
        .cyber-label, .section-title, .topbar-title, .stat-label, .badge {
            font-family: 'Sora', sans-serif !important;
        }
        .logo-text {
            font-family: 'Sora', sans-serif !important;
            font-weight: 800 !important;
        }
        .btn-neon {
            font-family: 'Sora', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.3px !important;
        }
        /* Beautiful animated underlines for links */
        a:not(.btn-neon):not(.mediops-logo):not(.nav-item-btn) {
            background-image: linear-gradient(135deg, var(--c-cyan), var(--c-purple));
            background-size: 0% 2px;
            background-position: 0 100%;
            background-repeat: no-repeat;
            transition: background-size 0.3s ease;
        }
        a:not(.btn-neon):not(.mediops-logo):not(.nav-item-btn):hover {
            background-size: 100% 2px;
        }
        /* Cursor enhancement */
        .btn-neon, .nav-item-btn, .glass-card { cursor: pointer; }
        /* Number glow for stat values */
        .stat-value {
            filter: drop-shadow(0 0 8px currentColor);
            opacity: 0.9;
        }
        /* Input focus glow animation */
        .cyber-input:focus {
            animation: inputGlow 0.3s ease forwards;
        }
        @keyframes inputGlow {
            from { box-shadow: 0 0 0 0 rgba(0,212,255,0); }
            to   { box-shadow: 0 0 0 3px rgba(0,212,255,0.15), 0 4px 20px rgba(0,212,255,0.08); }
        }
        /* Beautiful section title decoration */
        .section-title::before {
            background: linear-gradient(180deg, #00D4FF, #8B5CF6) !important;
            box-shadow: 0 0 10px rgba(0,212,255,0.6) !important;
        }
        /* Sidebar nav item hover glow */
        .sidebar-nav li .nav-item-btn.active {
            background: linear-gradient(90deg, rgba(0,212,255,0.15), rgba(139,92,246,0.08)) !important;
        }
        /* Beautiful empty states */
        .empty-icon { animation: iconBounce 3s ease-in-out infinite; filter: drop-shadow(0 0 12px rgba(0,212,255,0.3)); }
        @keyframes iconBounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        /* Stat card hover light beam */
        .stat-card:hover .stat-icon { filter: drop-shadow(0 0 16px rgba(0,212,255,0.6)); }
        /* Beautiful scrollbar */
        * { scrollbar-width: thin; scrollbar-color: rgba(0,212,255,0.3) transparent; }
    `;
    document.head.appendChild(style);

    // 7. Typewriter effect for page titles
    function typeWriter(el, text, speed = 60) {
        el.textContent = '';
        let i = 0;
        const interval = setInterval(() => {
            el.textContent += text[i];
            i++;
            if (i >= text.length) clearInterval(interval);
        }, speed);
    }

    // 8. Scroll-triggered entrance animations
    const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -30px 0px' };
    const entranceObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                entranceObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    function applyEntranceAnimations() {
        document.querySelectorAll('.glass-card:not([data-entrance]), .stat-card:not([data-entrance])').forEach((el, i) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = `opacity 0.6s ease ${i * 0.07}s, transform 0.6s cubic-bezier(0.34,1.56,0.64,1) ${i * 0.07}s`;
            el.dataset.entrance = 'true';
            entranceObserver.observe(el);
        });
    }

    // Run after a brief delay to let the page load
    setTimeout(applyEntranceAnimations, 300);

    // 9. Animated clock if present
    function updateClock() {
        const el = document.getElementById('topbarClock') || document.getElementById('liveTime');
        if (el) {
            const now = new Date();
            el.textContent = now.toLocaleTimeString('en-US', { hour12: false });
        }
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 10. Auto-remove "Welcome Back" text
    document.querySelectorAll('h1, h2, h3, p, span').forEach(el => {
        if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
            el.textContent = el.textContent.replace(/Welcome Back[,!.]*/gi, 'MediOps Portal');
        }
    });

    // 11. Cursor sparkle trail
    const cursorTrail = document.createElement('div');
    cursorTrail.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;z-index:99999;';
    document.body.appendChild(cursorTrail);

    document.addEventListener('mousemove', e => {
        if (Math.random() > 0.85) {
            const spark = document.createElement('div');
            const colors = ['#00D4FF', '#8B5CF6', '#FF6B9D'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            spark.style.cssText = `
                position: fixed;
                left: ${e.clientX}px;
                top: ${e.clientY}px;
                width: 5px; height: 5px;
                border-radius: 50%;
                background: ${color};
                box-shadow: 0 0 8px ${color};
                pointer-events: none;
                transform: translate(-50%, -50%);
                animation: sparkFade 0.7s ease-out forwards;
            `;
            cursorTrail.appendChild(spark);
            setTimeout(() => spark.remove(), 800);
        }
    });

    const sparkStyle = document.createElement('style');
    sparkStyle.textContent = `
        @keyframes sparkFade {
            0%   { transform: translate(-50%, -50%) scale(1); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(0) translateY(-15px); opacity: 0; }
        }
    `;
    document.head.appendChild(sparkStyle);

    console.log('%c✨ MediOps Cyberpunk Engine v3.0 Active', 'color: #00D4FF; font-family: Sora; font-size: 14px; font-weight: 700;');

})();
