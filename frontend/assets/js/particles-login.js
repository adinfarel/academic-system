class AntigravityText {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    
    this.text = options.text || 'Scholaria';
    this.colors = options.colors || ['#000000'];
    this.baseParticleSize = options.particleSize || 2.2;
    this.baseTextGap = options.textGap || 8;
    this.baseFontSize = options.fontSize || 200;
    this.offsetXPercent = options.offsetXPercent !== undefined ? options.offsetXPercent : 0.04;

    // Spring physics params
    this.springForce = 0.0015;
    this.friction = 0.88;

    this.particles = [];
    this.mouse = { x: -9999, y: -9999 };
    this.isRunning = true;

    this.init();
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => {
      this.resize();
      this.createParticles();
    });

    document.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
    });

    if (document.fonts) {
      document.fonts.ready.then(() => {
        this.createParticles();
      });
    } else {
      setTimeout(() => this.createParticles(), 500);
    }

    this.animate();
  }

  resize() {
    const parent = this.canvas.parentElement;
    const rect = parent.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = rect.width;
    this.h = rect.height;
  }

  createParticles() {
    this.particles = [];
    
    // Draw text to offscreen canvas
    const tCanvas = document.createElement('canvas');
    const tCtx = tCanvas.getContext('2d', { willReadFrequently: true });
    
    // --- RESPONSIVE FONT SCALING ---
    // Make text fit in 45% of screen (to not overlap form), or 85% on mobile
    const matchPercent = this.w < 768 ? 0.85 : 0.45;
    const maxTextWidth = this.w * matchPercent;
    
    tCtx.font = `900 100px "Times New Roman", Times, serif`;
    const refWidth = Math.ceil(tCtx.measureText(this.text).width);
    const calculatedFont = (maxTextWidth / refWidth) * 100;
    
    this.fontSize = Math.floor(Math.min(this.baseFontSize, Math.max(40, calculatedFont)));
    
    // Scale gap and particle radius down for smaller screens to preserve letter clarity
    const scaleFactor = this.fontSize / 200;
    this.textGap = Math.max(3, Math.round(this.baseTextGap * Math.pow(scaleFactor, 0.85)));
    this.particleSize = Math.max(1.0, this.baseParticleSize * Math.pow(scaleFactor, 0.6));
    // --------------------------------

    tCtx.font = `900 ${this.fontSize}px "Times New Roman", Times, serif`;
    const textWidth = Math.ceil(tCtx.measureText(this.text).width);
    const textHeight = Math.ceil(this.fontSize * 1.5);
    
    tCanvas.width = textWidth + 20;
    tCanvas.height = textHeight;
    
    tCtx.font = `900 ${this.fontSize}px "Times New Roman", Times, serif`;
    tCtx.textAlign = 'left';
    tCtx.textBaseline = 'top';
    tCtx.fillStyle = '#000';
    tCtx.fillText(this.text, 5, 5);

    const imgData = tCtx.getImageData(0, 0, tCanvas.width, tCanvas.height).data;
    
    // Start drawing at bottom left, natively responsive
    const startX = this.w * this.offsetXPercent;
    const startY = this.h * 0.75 - textHeight;

    const targets = [];
    
    // 1. Gather all target points
    for (let y = 0; y < tCanvas.height; y += this.textGap) {
      for (let x = 0; x < tCanvas.width; x += this.textGap) {
        const idx = (y * tCanvas.width + x) * 4;
        const alpha = imgData[idx + 3];
        if (alpha > 128) {
          targets.push({ x: startX + x, y: startY + y });
        }
      }
    }

    const N = targets.length;
    if (N === 0) return;

    // 2. Generate a full-screen neat grid of exactly N points
    const ratio = this.w / this.h;
    let rows = Math.round(Math.sqrt(N / ratio));
    let cols = Math.ceil(N / rows);
    
    const initialGrid = [];
    const cellW = this.w / cols;
    const cellH = this.h / rows;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (initialGrid.length < N) {
          // Add organic jitter to break the rigid grid, but keep uniform density
          initialGrid.push({
            x: c * cellW + cellW / 2 + (Math.random() - 0.5) * cellW * 0.7,
            y: r * cellH + cellH / 2 + (Math.random() - 0.5) * cellH * 0.7
          });
        }
      }
    }

    // 3. Sort both arrays primarily by X to ensure clean mapping (left goes to left, right to right)
    initialGrid.sort((a, b) => a.x - b.x);
    targets.sort((a, b) => a.x - b.x);

    // 4. Pair them up
    for (let i = 0; i < N; i++) {
      // Cascade Delay: Left side particles start immediately, right side particles wait longer.
      // This forces "Scho" to form before "ria".
      const normalizedX = initialGrid[i].x / this.w;
      const activationDelay = (normalizedX * 160) + (Math.random() * 40);
      const isRogue = Math.random() < 0.035; // ~3.5% particles intentionally go rogue

      this.particles.push({
        x: initialGrid[i].x,
        y: initialGrid[i].y,
        tx: isRogue ? null : targets[i].x,
        ty: isRogue ? null : targets[i].y,
        vx: isRogue ? (Math.random() - 0.5) * 5 : 0, // Rogues get a small initial push
        vy: isRogue ? (Math.random() - 0.5) * 5 : 0,
        color: this.colors[Math.floor(Math.random() * this.colors.length)],
        delay: activationDelay,
        activeFrame: 0,
        isRogue: isRogue
      });
    }
  }

  animate() {
    if (!this.isRunning) return;
    
    this.ctx.clearRect(0, 0, this.w, this.h);
    
    // Sort particles by X every frame to allow fast proximity collision
    // (We soft-sort because they don't jump around too crazily)
    this.particles.sort((a, b) => a.x - b.x);

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.activeFrame++;

      if (p.isRogue) {
        // Rogues wander randomly like dust and don't care about the text targets
        p.vx += (Math.random() - 0.5) * 0.03;
        p.vy += (Math.random() - 0.5) * 0.03;
        if (p.x < -10) p.vx += 0.2;
        if (p.x > this.w + 10) p.vx -= 0.2;
        if (p.y < -10) p.vy += 0.2;
        if (p.y > this.h + 10) p.vy -= 0.2;
      } else if (p.activeFrame > p.delay) {
        // Move towards target with spring physics (adds momentum and slight overshoot)
        p.vx += (p.tx - p.x) * this.springForce;
        p.vy += (p.ty - p.y) * this.springForce;
      }

      // Mouse repel
      const mdx = p.x - this.mouse.x;
      const mdy = p.y - this.mouse.y;
      const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
      
      if (mDist < 120 && mDist > 0) {
        const force = (1 - mDist / 120) * 0.5;
        p.vx += (mdx / mDist) * force;
        p.vy += (mdy / mDist) * force;
      }

      // Localized particle repulsion ("making slot" for new arrivals)
      // Since array is X-sorted, we only check nearby neighbors
      for (let j = i + 1; j < Math.min(i + 15, this.particles.length); j++) {
        const p2 = this.particles[j];
        const dx = p.x - p2.x;
        // If X distance is already > 8, stop checking (thanks to sorting)
        if (dx < -8 || dx > 8) break;
        
        const dy = p.y - p2.y;
        if (dy > -8 && dy < 8) {
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 6 && dist > 0.1) {
            const push = (6 - dist) * 0.05;
            p.vx += (dx / dist) * push;
            p.vy += (dy / dist) * push;
            p2.vx -= (dx / dist) * push;
            p2.vy -= (dy / dist) * push;
          }
        }
      }

      p.vx *= this.friction;
      p.vy *= this.friction;
      p.x += p.vx;
      p.y += p.vy;

      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, this.particleSize, 0, Math.PI * 2);
      this.ctx.fillStyle = p.color;
      this.ctx.fill();
    }
    
    requestAnimationFrame(() => this.animate());
  }

  destroy() {
    this.isRunning = false;
  }
}

