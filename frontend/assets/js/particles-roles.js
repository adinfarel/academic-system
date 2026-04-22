/* ============================================================
   particles-roles.js — DualZoneParticleSystem
   DEDICATED file for the Roles/Akses section ONLY.
   
   Uses offscreen canvas text sampling for THICK BOLD { }.
   "Ant & Sugar" nearest-target approach.
   CRISP, non-glowing particles matching Antigravity ref.
   ============================================================ */

class DualZoneParticleSystem {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.mouse = { x: -9999, y: -9999 };
    this.isRunning = true;
    this.frameId = null;

    // Zone state
    this.leftActive = false;
    this.rightActive = false;
    this.leftProgress = 0;
    this.rightProgress = 0;

    // Options
    this.opts = {
      totalParticles: options.totalParticles || 2500, // HIGH density
      particleSize: options.particleSize || 1.4,      // SMALL, crisp dots
      lerpSpeed: options.lerpSpeed || 0.08,
      progressSpeed: options.progressSpeed || 0.06,
      regressSpeed: options.regressSpeed || 0.04,
      attractRadius: options.attractRadius || 450,
      mouseRepelRadius: options.mouseRepelRadius || 80,
      mouseRepelForce: options.mouseRepelForce || 0.025,
      // Crisp dark/grey dots for scattered state (NO GLOW)
      sparkleColors: options.sparkleColors || [
        'rgba(40, 40, 45, 0.8)',
        'rgba(80, 80, 85, 0.7)',
        'rgba(120, 120, 125, 0.6)',
        'rgba(60, 60, 65, 0.75)',
        'rgba(150, 150, 150, 0.5)',
      ],
      // Crisp blue dots for formed state
      formedColors: options.formedColors || [
        'rgba(26, 115, 232, 1.0)',
        'rgba(66, 133, 244, 1.0)',
        'rgba(26, 115, 232, 0.9)',
      ],
    };

    this.leftTargets = [];
    this.rightTargets = [];

    this.init();
  }

  init() {
    this.resize();
    this._resizeHandler = () => {
      this.resize();
      this.generateTargets();
      this.assignTargets();
    };
    window.addEventListener('resize', this._resizeHandler);

    this._moveHandler = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;

      const midX = this.w / 2;
      const inCanvas = this.mouse.x >= 0 && this.mouse.x <= this.w &&
        this.mouse.y >= 0 && this.mouse.y <= this.h;

      if (inCanvas) {
        this.leftActive = this.mouse.x < midX;
        this.rightActive = this.mouse.x >= midX;
      } else {
        this.leftActive = false;
        this.rightActive = false;
      }
    };
    document.addEventListener('mousemove', this._moveHandler);

    this._leaveHandler = () => {
      this.leftActive = false;
      this.rightActive = false;
      this.mouse.x = -9999;
      this.mouse.y = -9999;
    };
    this.canvas.addEventListener('mouseleave', this._leaveHandler);

    this.createParticles();
    this.generateTargets();
    this.assignTargets();
    this.animate();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = rect.width;
    this.h = rect.height;
  }

  // ══════════════════════════════════════════════════════════════
  // BOUNDARIES CONFIGURATION
  // ══════════════════════════════════════════════════════════════
  getBounds() {
    // Sesuai garis merah lu: horizontal luas (5%), vertikal diluasin juga (margin ditipisin jadi 5%)
    const marginX = this.w * 0.05; 
    const marginY = this.h * 0.05; // Ditipisin sesuai foto lu, jadi nyebar hampir penuh
    return {
      minX: marginX,
      maxX: this.w - marginX,
      minY: marginY,
      maxY: this.h - marginY,
      innerW: this.w - (marginX * 2),
      innerH: this.h - (marginY * 2)
    };
  }

  // ══════════════════════════════════════════════════════════════
  // TEXT SAMPLING for { }
  // ══════════════════════════════════════════════════════════════
  sampleTextShape(text, areaX, areaY, areaW, areaH, maxPoints) {
    const targets = [];
    const RES_W = 1000;
    const RES_H = 600;
    const offCanvas = document.createElement('canvas');
    const offCtx = offCanvas.getContext('2d', { willReadFrequently: true });
    offCanvas.width = RES_W;
    offCanvas.height = RES_H;

    offCtx.clearRect(0, 0, RES_W, RES_H);

    const fontSize = Math.floor(RES_H * 0.85);
    offCtx.font = `900 ${fontSize}px "Inter", "Arial Black", "Segoe UI", sans-serif`;
    offCtx.textAlign = 'center';
    offCtx.textBaseline = 'middle';
    offCtx.fillStyle = '#000';
    offCtx.fillText(text, RES_W / 2, RES_H / 2);

    const imgData = offCtx.getImageData(0, 0, RES_W, RES_H).data;
    const filledPixels = [];
    const step = 2;

    for (let py = 0; py < RES_H; py += step) {
      for (let px = 0; px < RES_W; px += step) {
        const idx = (py * RES_W + px) * 4;
        if (imgData[idx + 3] > 60) {
          filledPixels.push({
            x: areaX + (px / RES_W) * areaW,
            y: areaY + (py / RES_H) * areaH,
          });
        }
      }
    }

    for (let i = filledPixels.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [filledPixels[i], filledPixels[j]] = [filledPixels[j], filledPixels[i]];
    }

    const count = Math.min(maxPoints, filledPixels.length);
    for (let i = 0; i < count; i++) {
      targets.push({
        x: filledPixels[i].x + (Math.random() - 0.5),
        y: filledPixels[i].y + (Math.random() - 0.5),
      });
    }

    return targets;
  }

  // ── Curly Braces { } ──
  generateBracesTargets() {
    // Kurangi lebarnya secara persentase biar gak mepet kotak text/cut off
    const shapeW = this.w * 0.40; 
    const shapeH = this.h * 0.60;
    // KEMBALIKAN KE TENGAH PERSIS (0.25) biar center sama text HTML-nya
    const shapeX = this.w * 0.25 - shapeW / 2;
    const shapeY = this.h * 0.50 - shapeH / 2;

    return this.sampleTextShape('{ }', shapeX, shapeY, shapeW, shapeH, 800);
  }

  // ── Generate five circles — DISTINCT ring layout matching Ref 4 ──
  generateFiveCirclesTargets() {
    const targets = [];
    // KEMBALIKAN KE TENGAH PERSIS (0.75) biar center sama text HTML-nya
    const cx = this.w * 0.75;
    const cy = this.h * 0.50; 

    // Fluid sizing auto-calculate:
    // Box area is W * 0.5. Max radius safe bound is 35% of the side box width to never touch edges.
    const maxRadiusBound = this.w * 0.17; 
    
    // Karena ringRadius + circleRadius (0.5 * ringRadius) = total shape, maka:
    const ringRadius = maxRadiusBound * 0.65;
    const circleRadius = maxRadiusBound * 0.35;
    const strokeW = circleRadius * 0.13; 
    const ptsPerCircle = 250; // VERY DENSE, No gaps!

    // Calculate 5 points around a center (Pentagon shape)
    for (let c = 0; c < 5; c++) {
      const angle = c * ((Math.PI * 2) / 5) - Math.PI / 2;
      const circleCX = cx + Math.cos(angle) * ringRadius;
      const circleCY = cy + Math.sin(angle) * ringRadius;

      for (let i = 0; i < ptsPerCircle; i++) {
        const ptAngle = (i / ptsPerCircle) * Math.PI * 2;
        const rOffset = (Math.random() - 0.5) * strokeW * 2;
        const r = circleRadius + rOffset;

        targets.push({
          x: circleCX + Math.cos(ptAngle) * r + (Math.random() - 0.5), // Less noise
          y: circleCY + Math.sin(ptAngle) * r + (Math.random() - 0.5),
        });
      }
    }

    return targets;
  }

  generateTargets() {
    this.leftTargets = this.generateBracesTargets();
    this.rightTargets = this.generateFiveCirclesTargets();
  }

  // ── "Ant & Sugar": nearby particles get assigned ──
  assignTargets() {
    const maxDist = this.opts.attractRadius;

    // Fast clear
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.hasTarget = false;
      p.targetX = p.homeX;
      p.targetY = p.homeY;
      p.targetSide = null;
    }

    const assign = (targets, side) => {
      for (let i = 0; i < targets.length; i++) {
        const target = targets[i];
        let bestP = null;
        let bestD = maxDist;

        for (let j = 0; j < this.particles.length; j++) {
          const p = this.particles[j];
          if (p.hasTarget) continue;

          const dx = p.homeX - target.x;
          const dy = p.homeY - target.y;
          // quick rect bounds check before sqrt for performance
          if (Math.abs(dx) > maxDist || Math.abs(dy) > maxDist) continue;

          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < bestD) {
            bestD = d;
            bestP = p;
          }
        }

        if (bestP) {
          bestP.hasTarget = true;
          bestP.targetSide = side;
          bestP.targetX = target.x;
          bestP.targetY = target.y;
        }
      }
    };

    assign(this.leftTargets, 'left');
    assign(this.rightTargets, 'right');
  }

  createParticles() {
    this.particles = [];
    const total = this.opts.totalParticles;
    const bounds = this.getBounds();

    for (let i = 0; i < total; i++) {
      const sparkleColor = this.opts.sparkleColors[
        Math.floor(Math.random() * this.opts.sparkleColors.length)
      ];
      const formedColor = this.opts.formedColors[
        Math.floor(Math.random() * this.opts.formedColors.length)
      ];

      // PARTIKEL HANYA MUNCUL DI DALAM KOTAK MERAH LU
      const homeX = bounds.minX + Math.random() * bounds.innerW;
      const homeY = bounds.minY + Math.random() * bounds.innerH;

      this.particles.push({
        x: homeX, y: homeY,
        homeX, homeY,
        targetX: homeX, targetY: homeY,
        hasTarget: false,
        targetSide: null,
        // KONSISTEN. Tidak acak ukurannya (kembalikan konfigurasi yang lu puji)
        size: this.opts.particleSize,
        sparkleColor, formedColor,
        alpha: 0,
        baseAlpha: 1.0,
        fadeIn: Math.random() * 20 + 5,
        frame: 0,
        driftAngle: Math.random() * Math.PI * 2,
        driftSpeed: 0.001 + Math.random() * 0.003,
        driftAmount: 0.05 + Math.random() * 0.1,
        // Glow effect mechanism
        twinklePhase: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.015 + Math.random() * 0.02,
      });
    }
  }

  // ── Color utilities ──
  parseColor(colorStr) {
    const m = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+),?\s*([\d.]*)\)/);
    if (!m) return { r: 128, g: 128, b: 128, a: 1 };
    return {
      r: parseInt(m[1]), g: parseInt(m[2]), b: parseInt(m[3]),
      a: m[4] !== '' ? parseFloat(m[4]) : 1,
    };
  }

  lerpColor(c1Str, c2Str, t) {
    const c1 = this.parseColor(c1Str);
    const c2 = this.parseColor(c2Str);
    return `rgba(${Math.round(c1.r + (c2.r - c1.r) * t)}, ${Math.round(c1.g + (c2.g - c1.g) * t)}, ${Math.round(c1.b + (c2.b - c1.b) * t)}, ${(c1.a + (c2.a - c1.a) * t).toFixed(3)})`;
  }

  // ── Main animation loop ──
  animate() {
    if (!this.isRunning) return;
    this.ctx.clearRect(0, 0, this.w, this.h);

    const pSpeed = this.opts.progressSpeed;
    const rSpeed = this.opts.regressSpeed;
    const bounds = this.getBounds();

    // DETECTION BARU: Cuma kedetect kalo mouse ada DALAM kotak merah lu
    const isMouseInBounds = 
      this.mouse.x >= bounds.minX && this.mouse.x <= bounds.maxX &&
      this.mouse.y >= bounds.minY && this.mouse.y <= bounds.maxY;

    // Kalau mouse di luar garis merah, pudar paksa!
    const effectiveLeftActive = isMouseInBounds && this.leftActive;
    const effectiveRightActive = isMouseInBounds && this.rightActive;

    this.leftProgress = effectiveLeftActive
      ? Math.min(1, this.leftProgress + pSpeed)
      : Math.max(0, this.leftProgress - rSpeed);

    this.rightProgress = effectiveRightActive
      ? Math.min(1, this.rightProgress + pSpeed)
      : Math.max(0, this.rightProgress - rSpeed);

    const lerpSpeed = this.opts.lerpSpeed;

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.frame++;

      if (p.frame < p.fadeIn) {
        p.alpha = (p.frame / p.fadeIn);
      } else {
        p.alpha = 1.0;
      }

      let progress = 0;
      if (p.hasTarget) {
        if (p.targetSide === 'left') progress = this.leftProgress;
        else if (p.targetSide === 'right') progress = this.rightProgress;
      }

      const destX = p.homeX + (p.targetX - p.homeX) * progress;
      const destY = p.homeY + (p.targetY - p.homeY) * progress;

      // Spring
      p.x += (destX - p.x) * lerpSpeed;
      p.y += (destY - p.y) * lerpSpeed;

      // Drift when scattered
      const driftFactor = 1 - progress;
      if (driftFactor > 0.01) {
        p.driftAngle += p.driftSpeed;
        p.x += Math.cos(p.driftAngle) * p.driftAmount * driftFactor;
        p.y += Math.sin(p.driftAngle) * p.driftAmount * driftFactor;

        // Soft BOUNCE so it never scapes along a flat imaginary wall causing flattened clusters!
        if (p.x < bounds.minX || p.x > bounds.maxX) {
          p.driftAngle = Math.PI - p.driftAngle;
          p.x = Math.max(bounds.minX, Math.min(bounds.maxX, p.x));
        }
        if (p.y < bounds.minY || p.y > bounds.maxY) {
          p.driftAngle = -p.driftAngle;
          p.y = Math.max(bounds.minY, Math.min(bounds.maxY, p.y));
        }
      }

      // Mouse repulsion
      const mdx = p.x - this.mouse.x;
      const mdy = p.y - this.mouse.y;
      const dSq = mdx * mdx + mdy * mdy;
      const rSq = this.opts.mouseRepelRadius * this.opts.mouseRepelRadius;
      if (dSq < rSq && dSq > 0) {
        const mDist = Math.sqrt(dSq);
        const force = (1 - mDist / this.opts.mouseRepelRadius) * this.opts.mouseRepelForce;
        p.x += (mdx / mDist) * force * 15;
        p.y += (mdy / mDist) * force * 15;
      }

      // Twinkle calculation
      p.twinklePhase += p.twinkleSpeed;
      const twinkle = 0.65 + 0.35 * Math.sin(p.twinklePhase); 

      // Color lerp
      const color = this.lerpColor(p.sparkleColor, p.formedColor, progress);
      const pc = this.parseColor(color);

      // CRISP dots - use fillRect for sharp form, twinkle used in alpha for glow/shine.
      this.ctx.fillStyle = `rgba(${pc.r}, ${pc.g}, ${pc.b}, ${pc.a * p.alpha * twinkle})`;
      this.ctx.fillRect(p.x - p.size, p.y - p.size, p.size * 2, p.size * 2);
    }

    this.frameId = requestAnimationFrame(() => this.animate());
  }

  destroy() {
    this.isRunning = false;
    if (this.frameId) cancelAnimationFrame(this.frameId);
    if (this._moveHandler) document.removeEventListener('mousemove', this._moveHandler);
    if (this._resizeHandler) window.removeEventListener('resize', this._resizeHandler);
    if (this._leaveHandler) this.canvas.removeEventListener('mouseleave', this._leaveHandler);
  }
}
