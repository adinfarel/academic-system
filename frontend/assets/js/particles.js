/* ============================================================
   particles.js — Enhanced Particle System
   Supports: dense scattered, shape formations (circle, square,
   heart, infinity), colored particles (Google-style)
   Spring-back: particles return to formation after mouse push
   ============================================================ */

class ParticleSystem {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.mouse = { x: -9999, y: -9999 };
    this.isRunning = true;
    this.frameId = null;

    // Options
    this.opts = {
      count: options.count || 120,
      size: options.size || 1.5,
      speed: options.speed || 0.15,
      connectionDistance: options.connectionDistance || 0,
      mouseRadius: options.mouseRadius || 150,
      mouseRepelForce: options.mouseRepelForce || options.mouseForce || 0.05,
      mouseMode: options.mouseMode || 'attract',
      colors: options.colors || null,
      shape: options.shape || null,
      shapeText: options.shapeText || '',
      shapeScale: options.shapeScale || 0.4,
      shapeOffsetX: options.shapeOffsetX || 0,
      shapeOffsetY: options.shapeOffsetY || 0,
      drift: options.drift !== false,
      driftAmount: options.driftAmount || 0.3,
      opacity: options.opacity || 1,
      returnSpeed: options.returnSpeed || 0.025,
      ...options,
    };

    this.init();
  }

  init() {
    this.resize();
    this._resizeHandler = () => this.resize();
    window.addEventListener('resize', this._resizeHandler);

    // Mouse tracking — document level for full interactivity
    this._moveHandler = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
    };
    document.addEventListener('mousemove', this._moveHandler);

    this.createParticles();
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

  // ── Generate shape target positions ──
  getShapeTargets(shape, count) {
    const targets = [];
    const cx = this.w / 2 + (this.opts.shapeOffsetX || 0);
    const cy = this.h / 2 + (this.opts.shapeOffsetY || 0);
    const scale = Math.min(this.w, this.h) * this.opts.shapeScale;

    switch (shape) {
      case 'circle':
        for (let i = 0; i < count; i++) {
          const angle = (i / count) * Math.PI * 2;
          const r = scale + (Math.random() - 0.5) * 12;
          targets.push({ x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
        }
        break;

      case 'shield':
        for (let i = 0; i < count; i++) {
          const t = (i / count) * Math.PI * 2;
          const r = scale * (1 + 0.15 * Math.sin(t * 2));
          let px = Math.sin(t) * r;
          let py = -Math.cos(t) * r * 0.85;
          if (t > Math.PI) py += (t - Math.PI) * scale * 0.25;
          targets.push({ x: cx + px + (Math.random() - 0.5) * 8, y: cy + py + (Math.random() - 0.5) * 8 });
        }
        break;

      case 'infinity':
        for (let i = 0; i < count; i++) {
          const t = (i / count) * Math.PI * 2;
          const r = scale * 1.0;
          const denom = 1 + Math.sin(t) * Math.sin(t);
          targets.push({
            x: cx + (r * Math.cos(t)) / denom + (Math.random() - 0.5) * 6,
            y: cy + (r * Math.sin(t) * Math.cos(t)) / denom + (Math.random() - 0.5) * 6,
          });
        }
        break;

      case 'brackets':
        const quarter = Math.floor(count / 4);
        for (let i = 0; i < quarter * 2; i++) {
          const t = (i / (quarter * 2)) * Math.PI * 2;
          const bx = cx - scale * 0.5 + Math.sin(t) * scale * 0.15;
          const by = cy + (t / (Math.PI * 2) - 0.5) * scale * 1.6;
          targets.push({ x: bx + (Math.random() - 0.5) * 4, y: by + (Math.random() - 0.5) * 4 });
        }
        for (let i = 0; i < count - quarter * 2; i++) {
          const t = (i / (count - quarter * 2)) * Math.PI * 2;
          const bx = cx + scale * 0.5 - Math.sin(t) * scale * 0.15;
          const by = cy + (t / (Math.PI * 2) - 0.5) * scale * 1.6;
          targets.push({ x: bx + (Math.random() - 0.5) * 4, y: by + (Math.random() - 0.5) * 4 });
        }
        break;

      case 'network':
        // 6 circles forming a ring (Screenshot 4: For Organizations)
        const clusters = 6;
        const ptsPerCluster = Math.floor(count / clusters);
        const ringRadius = scale * 0.8;
        const clusterRadius = scale * 0.35;

        for (let c = 0; c < clusters; c++) {
          const cAngle = (c / clusters) * Math.PI * 2 - Math.PI / 2; // start top
          const clusterCenterX = cx + Math.cos(cAngle) * ringRadius;
          const clusterCenterY = cy + Math.sin(cAngle) * ringRadius;

          for (let i = 0; i < ptsPerCluster; i++) {
            const pAngle = Math.random() * Math.PI * 2;
            // Distribute points towards edge of cluster
            const pRadius = clusterRadius * Math.pow(Math.random(), 0.5);
            targets.push({
              x: clusterCenterX + Math.cos(pAngle) * pRadius,
              y: clusterCenterY + Math.sin(pAngle) * pRadius
            });
          }
        }
        // Add remainder to random
        while (targets.length < count) {
          targets.push({ x: cx + (Math.random() - 0.5) * scale, y: cy + (Math.random() - 0.5) * scale });
        }
        break;

      case 'grid':
        const cols = Math.ceil(Math.sqrt(count * (this.w / this.h)));
        const rows = Math.ceil(count / cols);
        const gapX = this.w / cols;
        const gapY = this.h / rows;
        for (let i = 0; i < count; i++) {
          const col = i % cols;
          const row = Math.floor(i / cols);
          targets.push({
            x: col * gapX + gapX / 2 + (Math.random() - 0.5) * gapX * 0.3,
            y: row * gapY + gapY / 2 + (Math.random() - 0.5) * gapY * 0.3,
          });
        }
        break;

      case 'radial-burst':
        // Exploding dashes from center
        for (let i = 0; i < count; i++) {
          const angle = Math.random() * Math.PI * 2;
          // Weighted random so more are further out
          const r = scale * 1.5 * Math.pow(Math.random(), 0.5) + 50;
          targets.push({ x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
        }
        break;

      case 'text': {
        const rawText = this.opts.shapeText || 'POLSRI';
        const txtCanvas = document.createElement('canvas');
        const txtCtx = txtCanvas.getContext('2d');
        const fontSize = this.opts.fontSize || Math.floor(Math.min(this.w, this.h) * 0.12);
        
        txtCtx.font = `900 ${fontSize}px "Times New Roman", Times, serif`;
        const textWidth = txtCtx.measureText(rawText).width;
        txtCanvas.width = textWidth + 20;
        txtCanvas.height = fontSize * 1.5;
        
        txtCtx.font = `900 ${fontSize}px "Times New Roman", Times, serif`;
        txtCtx.textAlign = 'left';
        txtCtx.textBaseline = 'top';
        txtCtx.fillStyle = '#000';
        txtCtx.fillText(rawText, 5, 5);

        const imgData = txtCtx.getImageData(0, 0, txtCanvas.width, txtCanvas.height).data;
        const points = [];
        
        // Grid spacing
        const step = this.opts.textGap || 6;
        
        // Exact positioning
        const startX = this.opts.shapeOffsetX !== undefined ? this.opts.shapeOffsetX : this.w * 0.08; // 8% from left
        const startY = this.opts.shapeOffsetY !== undefined ? this.opts.shapeOffsetY : this.h * 0.7; // 70% down

        for (let yy = 0; yy < txtCanvas.height; yy += step) {
          for (let xx = 0; xx < txtCanvas.width; xx += step) {
            const idx = (yy * txtCanvas.width + xx) * 4;
            if (imgData[idx + 3] > 128) {
              points.push({
                x: startX + xx,
                y: startY + yy
              });
            }
          }
        }

        // Shuffle points to avoid linear formation
        for (let i = points.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [points[i], points[j]] = [points[j], points[i]];
        }
        
        return points;
      }

      default:
        return null;
    }

    return targets;
  }

  getParticleColor() {
    if (this.opts.colors) {
      return this.opts.colors[Math.floor(Math.random() * this.opts.colors.length)];
    }
    return 'rgba(0,0,0,0.35)';
  }

  createParticles() {
    this.particles = [];
    const targets = this.opts.shape ? this.getShapeTargets(this.opts.shape, this.opts.count) : null;

    if (this.opts.shape === 'text' && targets && targets.length > 0) {
      this.opts.count = targets.length;
    }

    const isText = this.opts.shape === 'text';

    for (let i = 0; i < this.opts.count; i++) {
      const color = this.getParticleColor();
      const size = isText ? this.opts.size : this.opts.size * (0.4 + Math.random() * 1.2);

      const p = {
        x: Math.random() * this.w,
        y: Math.random() * this.h,
        vx: (Math.random() - 0.5) * this.opts.speed,
        vy: (Math.random() - 0.5) * this.opts.speed,
        size: size,
        color: color,
        baseAlpha: 0.3 + Math.random() * 0.7,
        alpha: 0,
        fadeIn: Math.random() * 60 + 20,
        frame: 0,
        tx: targets ? targets[i].x : null,
        ty: targets ? targets[i].y : null,
        driftAngle: Math.random() * Math.PI * 2,
        driftSpeed: 0.002 + Math.random() * 0.005,
      };
      this.particles.push(p);
    }
  }

  // ── Smooth transition to a new shape (no blink) ──
  setTargets(shape, colors, shapeScale) {
    if (colors) this.opts.colors = colors;
    if (shapeScale !== undefined) this.opts.shapeScale = shapeScale;
    this.opts.shape = shape;
    const targets = this.getShapeTargets(shape, this.opts.count);
    if (!targets) return;
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.tx = targets[i].x;
      p.ty = targets[i].y;
      if (colors) p.color = colors[Math.floor(Math.random() * colors.length)];
    }
  }

  // ── Smoothly scatter all particles (remove targets) ──
  clearTargets(colors) {
    this.opts.shape = null;
    if (colors) this.opts.colors = colors;
    for (const p of this.particles) {
      p.tx = null;
      p.ty = null;
      p.vx = (Math.random() - 0.5) * this.opts.speed * 2;
      p.vy = (Math.random() - 0.5) * this.opts.speed * 2;
      if (colors) p.color = colors[Math.floor(Math.random() * colors.length)];
    }
  }

  animate() {
    if (!this.isRunning) return;
    this.ctx.clearRect(0, 0, this.w, this.h);

    for (const p of this.particles) {
      p.frame++;

      // Fade in
      if (p.frame < p.fadeIn) {
        p.alpha = (p.frame / p.fadeIn) * p.baseAlpha;
      } else {
        p.alpha = p.baseAlpha;
      }

      if (p.tx !== null && p.ty !== null) {
        // ── Shape mode: spring-back to target ──
        const dx = p.tx - p.x;
        const dy = p.ty - p.y;
        // Slow spring return — particles always pull back to formation
        p.x += dx * this.opts.returnSpeed;
        p.y += dy * this.opts.returnSpeed;

        // Gentle drift around target
        if (this.opts.drift) {
          p.driftAngle += p.driftSpeed;
          p.x += Math.cos(p.driftAngle) * this.opts.driftAmount;
          p.y += Math.sin(p.driftAngle) * this.opts.driftAmount;
        }
      } else {
        // ── Free roam mode ──
        p.x += p.vx;
        p.y += p.vy;

        if (this.opts.drift) {
          p.driftAngle += p.driftSpeed;
          p.vx += Math.cos(p.driftAngle) * 0.002;
          p.vy += Math.sin(p.driftAngle) * 0.002;
          p.vx *= 0.999;
          p.vy *= 0.999;
        }

        // Wrap edges
        if (p.x < -10) p.x = this.w + 10;
        if (p.x > this.w + 10) p.x = -10;
        if (p.y < -10) p.y = this.h + 10;
        if (p.y > this.h + 10) p.y = -10;
      }

      // Mouse interaction
      const mdx = p.x - this.mouse.x;
      const mdy = p.y - this.mouse.y;
      const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
      if (mDist < this.opts.mouseRadius && mDist > 0) {
        const force = (1 - mDist / this.opts.mouseRadius) * this.opts.mouseRepelForce;
        if (this.opts.mouseMode === 'attract') {
          // Gravity attract — particles float toward cursor
          p.x -= (mdx / mDist) * force * 12;
          p.y -= (mdy / mDist) * force * 12;
          // Slight orbital perpendicular force
          p.x += (-mdy / mDist) * force * 2;
          p.y += (mdx / mDist) * force * 2;
        } else {
          // Repel — push away
          p.x += (mdx / mDist) * force * 20;
          p.y += (mdy / mDist) * force * 20;
        }
      }

      // Draw particle
      this.ctx.beginPath();
      if (this.opts.particleStyle === 'dash') {
        const angle = Math.atan2(p.y - (this.h / 2), p.x - (this.w / 2));
        const len = p.size * 5;
        this.ctx.moveTo(p.x, p.y);
        this.ctx.lineTo(p.x + Math.cos(angle) * len, p.y + Math.sin(angle) * len);
        this.ctx.strokeStyle = p.color.replace(/[\d.]+\)$/, (p.alpha * this.opts.opacity) + ')');
        this.ctx.lineWidth = p.size;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();
      } else {
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fillStyle = p.color.replace(/[\d.]+\)$/, (p.alpha * this.opts.opacity) + ')');
        this.ctx.fill();
      }
    }

    // Draw connections
    if (this.opts.connectionDistance > 0) {
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const a = this.particles[i];
          const b = this.particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < this.opts.connectionDistance) {
            const alpha = (1 - dist / this.opts.connectionDistance) * 0.35;
            this.ctx.beginPath();
            this.ctx.moveTo(a.x, a.y);
            this.ctx.lineTo(b.x, b.y);
            // Elegant academic blue/monochrome plexus
            this.ctx.strokeStyle = `rgba(30, 64, 175, ${alpha})`;
            this.ctx.lineWidth = 0.8;
            this.ctx.stroke();
          }
        }
      }
    }

    this.frameId = requestAnimationFrame(() => this.animate());
  }

  destroy() {
    this.isRunning = false;
    if (this.frameId) cancelAnimationFrame(this.frameId);
    // Clean up event listeners
    if (this._moveHandler) document.removeEventListener('mousemove', this._moveHandler);
    if (this._resizeHandler) window.removeEventListener('resize', this._resizeHandler);
  }
}



// ── Global helper functions ──
const particleSystems = {};

function initParticles(canvasId, options = {}) {
  if (particleSystems[canvasId]) {
    particleSystems[canvasId].destroy();
  }
  particleSystems[canvasId] = new ParticleSystem(canvasId, options);
  return particleSystems[canvasId];
}

function destroyParticles(canvasId) {
  if (particleSystems[canvasId]) {
    particleSystems[canvasId].destroy();
    delete particleSystems[canvasId];
  }
}
