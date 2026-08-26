import * as React from 'react';
import { cn } from '../lib/cn';

/**
 * Full-viewport animated forest scene — layered CSS gradients for sky/canopy,
 * SVG tree silhouettes, and drifting mist bands. Sits behind all content as a
 * fixed background. Zero external assets, works offline.
 */
export function ForestBackground({ className }: { className?: string }) {
  return (
    <div
      className={cn('pointer-events-none fixed inset-0 z-0 overflow-hidden', className)}
      aria-hidden="true"
    >
      {/* Sky gradient — deep jungle night */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a1e0f] via-[#0d2818] to-[#08130d]" />

      {/* Canopy glow — subtle green moonlight filtering through leaves */}
      <div className="absolute left-1/4 top-0 h-[60vh] w-[120vw] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(16,160,99,0.08)_0%,transparent_70%)]" />
      <div className="absolute right-0 top-[10vh] h-[40vh] w-[60vw] bg-[radial-gradient(ellipse_at_center,rgba(30,95,168,0.06)_0%,transparent_70%)]" />

      {/* Ground fog — horizontal mist bands */}
      <div className="forest-mist-1 absolute bottom-0 left-0 h-[30vh] w-[200vw] opacity-30" />
      <div className="forest-mist-2 absolute bottom-[5vh] left-0 h-[20vh] w-[200vw] opacity-20" />

      {/* Tree silhouettes — layered at different depths */}
      {/* Far trees (smaller, more transparent) */}
      <svg
        className="absolute bottom-0 left-0 w-full opacity-[0.12]"
        viewBox="0 0 1440 200"
        preserveAspectRatio="none"
        style={{ height: '35vh' }}
      >
        <path
          d="M0,200 L0,120 Q30,60 60,120 Q80,40 100,120 Q130,50 160,120 Q180,30 200,120 Q230,55 260,120 Q280,35 300,120 Q330,60 360,120 Q380,25 400,120 Q430,50 460,120 Q480,40 500,120 Q530,60 560,120 Q580,30 600,120 Q630,55 660,120 Q680,35 700,120 Q730,60 760,120 Q780,25 800,120 Q830,50 860,120 Q880,40 900,120 Q930,60 960,120 Q980,30 1000,120 Q1030,55 1060,120 Q1080,35 1100,120 Q1130,60 1160,120 Q1180,25 1200,120 Q1230,50 1260,120 Q1280,40 1300,120 Q1330,60 1360,120 Q1380,30 1400,120 L1440,120 L1440,200 Z"
          fill="#0a3a27"
        />
      </svg>

      {/* Mid trees */}
      <svg
        className="absolute bottom-0 left-0 w-full opacity-[0.18]"
        viewBox="0 0 1440 200"
        preserveAspectRatio="none"
        style={{ height: '28vh' }}
      >
        <path
          d="M0,200 L0,140 Q40,70 80,140 Q100,50 120,140 Q160,80 200,140 Q220,45 240,140 Q280,75 320,140 Q340,55 360,140 Q400,80 440,140 Q460,40 480,140 Q520,70 560,140 Q580,50 600,140 Q640,80 680,140 Q700,45 720,140 Q760,75 800,140 Q820,55 840,140 Q880,80 920,140 Q940,40 960,140 Q1000,70 1040,140 Q1060,50 1080,140 Q1120,80 1160,140 Q1180,45 1200,140 Q1240,75 1280,140 Q1300,55 1320,140 Q1360,80 1400,140 L1440,140 L1440,200 Z"
          fill="#0d4f34"
        />
      </svg>

      {/* Near trees (tallest, most opaque) */}
      <svg
        className="absolute bottom-0 left-0 w-full opacity-[0.25]"
        viewBox="0 0 1440 200"
        preserveAspectRatio="none"
        style={{ height: '22vh' }}
      >
        <path
          d="M0,200 L0,150 Q50,90 100,150 Q120,70 140,150 Q200,100 260,150 Q280,60 300,150 Q360,95 420,150 Q440,75 460,150 Q520,100 580,150 Q600,65 620,150 Q680,95 740,150 Q760,70 780,150 Q840,100 900,150 Q920,60 940,150 Q1000,95 1060,150 Q1080,75 1100,150 Q1160,100 1220,150 Q1240,65 1260,150 Q1320,95 1380,150 L1440,150 L1440,200 Z"
          fill="#0a3a27"
        />
      </svg>

      {/* Bamboo stalks — thin vertical lines */}
      <div className="absolute bottom-0 left-[8%] h-[45vh] w-[3px] bg-gradient-to-t from-forest-800/20 to-forest-600/10" />
      <div className="absolute bottom-0 left-[12%] h-[38vh] w-[2px] bg-gradient-to-t from-forest-800/15 to-forest-600/8" />
      <div className="absolute bottom-0 right-[10%] h-[42vh] w-[3px] bg-gradient-to-t from-forest-800/20 to-forest-600/10" />
      <div className="absolute bottom-0 right-[15%] h-[35vh] w-[2px] bg-gradient-to-t from-forest-800/15 to-forest-600/8" />

      {/* Jumping pandas — small silhouettes arcing between trees */}
      <div className="forest-panda-jump-1 absolute" style={{ bottom: '30vh', left: '15%' }}>
        <svg viewBox="0 0 40 40" width="28" height="28" fill="none" aria-hidden="true">
          <circle cx="20" cy="22" r="12" fill="#1a1a2e" opacity="0.35" />
          <circle cx="13" cy="12" r="5" fill="#1a1a2e" opacity="0.35" />
          <circle cx="27" cy="12" r="5" fill="#1a1a2e" opacity="0.35" />
          <circle cx="20" cy="22" r="10" fill="#2d2d44" opacity="0.3" />
          <circle cx="16" cy="20" r="2" fill="#4a4a6a" opacity="0.3" />
          <circle cx="24" cy="20" r="2" fill="#4a4a6a" opacity="0.3" />
        </svg>
      </div>
      <div className="forest-panda-jump-2 absolute" style={{ bottom: '25vh', right: '20%' }}>
        <svg viewBox="0 0 40 40" width="22" height="22" fill="none" aria-hidden="true">
          <circle cx="20" cy="22" r="12" fill="#1a1a2e" opacity="0.3" />
          <circle cx="13" cy="12" r="5" fill="#1a1a2e" opacity="0.3" />
          <circle cx="27" cy="12" r="5" fill="#1a1a2e" opacity="0.3" />
          <circle cx="20" cy="22" r="10" fill="#2d2d44" opacity="0.25" />
          <circle cx="16" cy="20" r="2" fill="#4a4a6a" opacity="0.25" />
          <circle cx="24" cy="20" r="2" fill="#4a4a6a" opacity="0.25" />
        </svg>
      </div>
      <div className="forest-panda-jump-3 absolute" style={{ bottom: '35vh', left: '55%' }}>
        <svg viewBox="0 0 40 40" width="20" height="20" fill="none" aria-hidden="true">
          <circle cx="20" cy="22" r="12" fill="#1a1a2e" opacity="0.25" />
          <circle cx="13" cy="12" r="5" fill="#1a1a2e" opacity="0.25" />
          <circle cx="27" cy="12" r="5" fill="#1a1a2e" opacity="0.25" />
          <circle cx="20" cy="22" r="10" fill="#2d2d44" opacity="0.2" />
          <circle cx="16" cy="20" r="2" fill="#4a4a6a" opacity="0.2" />
          <circle cx="24" cy="20" r="2" fill="#4a4a6a" opacity="0.2" />
        </svg>
      </div>

      {/* Vignette — darken edges so content in center pops */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(8,19,13,0.4)_100%)]" />
    </div>
  );
}
