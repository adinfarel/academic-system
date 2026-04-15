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

      case 'circles-double':
        const half = Math.floor(count / 2);
        for (let i = 0; i < half; i++) {
          const angle = (i / half) * Math.PI * 2;
          const r = scale * 0.75 + (Math.random() - 0.5) * 10;
          targets.push({ x: cx - scale * 0.4 + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
        }
        for (let i = 0; i < count - half; i++) {
          const angle = (i / (count - half)) * Math.PI * 2;
          const r = scale * 0.75 + (Math.random() - 0.5) * 10;
          targets.push({ x: cx + scale * 0.4 + Math.cos(angle) * r, y: cy + Math.sin(angle) * r });
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

      case 'wave':
      case 'dna':
        // DNA double helix — two intertwining strands + rungs
        const strandCount = Math.floor(count * 0.4);
        const rungCount = count - strandCount * 2;
        const amplitude = scale * 0.6;
        // Strand 1
        for (let i = 0; i < strandCount; i++) {
          const p = i / strandCount;
          const x = p * this.w;
          const y = cy + Math.sin(p * Math.PI * 6) * amplitude + (Math.random() - 0.5) * 6;
          targets.push({ x, y });
        }
        // Strand 2 (phase shifted)
        for (let i = 0; i < strandCount; i++) {
          const p = i / strandCount;
          const x = p * this.w;
          const y = cy + Math.sin(p * Math.PI * 6 + Math.PI) * amplitude + (Math.random() - 0.5) * 6;
          targets.push({ x, y });
        }
        // Connecting rungs
        for (let i = 0; i < rungCount; i++) {
          const p = i / rungCount;
          const x = p * this.w;
          const y1 = cy + Math.sin(p * Math.PI * 6) * amplitude;
          const y2 = cy + Math.sin(p * Math.PI * 6 + Math.PI) * amplitude;
          const t = Math.random();
          targets.push({ x: x + (Math.random() - 0.5) * 4, y: y1 + (y2 - y1) * t });
        }
        break;

      case 'text': {
        // Multi-line text → particle formation with optional rotation
        const rawText = this.opts.shapeText || 'POLSRI';
        const lines = rawText.split('\n');
        const numLines = lines.length;
        const rotation = (this.opts.shapeRotation || 0) * Math.PI / 180; // degrees → radians

        // High-res offscreen canvas for sharp sampling
        const RES_W = 1200;
        const RES_H = 800;
        const txtCanvas = document.createElement('canvas');
        const txtCtx = txtCanvas.getContext('2d');
        txtCanvas.width = RES_W;
        txtCanvas.height = RES_H;

        // Find the longest line to determine font size
        txtCtx.font = '800 100px Inter, Arial, sans-serif';
        let maxLineWidth = 0;
        for (const line of lines) {
          const w = txtCtx.measureText(line).width;
          if (w > maxLineWidth) maxLineWidth = w;
        }

        // Scale font — fill ~70% of width (leave room for rotation)
        const fontSize = Math.floor((RES_W * 0.65 / maxLineWidth) * 100);
        const lineHeight = fontSize * 1.35;
        const totalTextHeight = lineHeight * numLines;
        const startY = -totalTextHeight / 2 + fontSize * 0.35;

        // Apply rotation around center
        txtCtx.save();
        txtCtx.translate(RES_W / 2, RES_H / 2);
        txtCtx.rotate(rotation);

        txtCtx.font = `800 ${fontSize}px Inter, Arial, sans-serif`;
        txtCtx.textAlign = 'center';
        txtCtx.textBaseline = 'top';
        txtCtx.fillStyle = '#000';

        for (let li = 0; li < numLines; li++) {
          txtCtx.fillText(lines[li], 0, startY + li * lineHeight);
        }
        txtCtx.restore();

        // Sample filled pixels
        const imgData = txtCtx.getImageData(0, 0, RES_W, RES_H).data;
        const points = [];
        const step = Math.max(2, Math.floor(Math.sqrt((RES_W * RES_H) / (count * 2))));
        const scaleX = this.w / RES_W;
        const scaleY = this.h / RES_H;
        const offsetY = this.opts.shapeOffsetY || 0;

        for (let yy = 0; yy < RES_H; yy += step) {
          for (let xx = 0; xx < RES_W; xx += step) {
            const idx = (yy * RES_W + xx) * 4;
            if (imgData[idx + 3] > 128) {
              points.push({
                x: xx * scaleX + (Math.random() - 0.5) * step * scaleX * 0.4,
                y: yy * scaleY + (Math.random() - 0.5) * step * scaleY * 0.4 + offsetY,
              });
            }
          }
        }

        // Distribute particles across sampled points
        if (points.length > 0) {
          for (let i = points.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [points[i], points[j]] = [points[j], points[i]];
          }
          for (let i = 0; i < count; i++) {
            targets.push(points[i % points.length]);
          }
        } else {
          for (let i = 0; i < count; i++) {
            targets.push({ x: Math.random() * this.w, y: Math.random() * this.h });
          }
        }
        break;
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

    for (let i = 0; i < this.opts.count; i++) {
      const color = this.getParticleColor();
      const size = this.opts.size * (0.4 + Math.random() * 1.2);

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
      this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      this.ctx.fillStyle = p.color.replace(/[\d.]+\)$/, (p.alpha * this.opts.opacity) + ')');
      this.ctx.fill();
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
            const alpha = (1 - dist / this.opts.connectionDistance) * 0.15;
            this.ctx.beginPath();
            this.ctx.moveTo(a.x, a.y);
            this.ctx.lineTo(b.x, b.y);
            this.ctx.strokeStyle = `rgba(0,0,0,${alpha * 0.5})`;
            this.ctx.lineWidth = 0.5;
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
