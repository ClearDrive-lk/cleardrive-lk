"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export default function SplashScreen() {
  const [active, setActive] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setActive(false), 1400);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div
      className={cn("splash-screen", !active && "splash-screen--hide")}
      aria-hidden={!active}
    >
      <div className="splash-card">
        <div className="splash-badge">Direct Import Lane</div>
        <div className="splash-wheel" aria-hidden="true">
          <div className="splash-wheel__spin">
            <svg
              className="splash-wheel__svg"
              viewBox="0 0 160 160"
              aria-hidden="true"
            >
              <defs>
                <linearGradient id="wheelRim" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" />
                  <stop offset="50%" stopColor="hsl(var(--secondary))" />
                  <stop offset="100%" stopColor="hsl(var(--primary))" />
                </linearGradient>
              </defs>
              <circle cx="80" cy="80" r="74" className="wheel-tire" />
              <circle cx="80" cy="80" r="60" className="wheel-rim" />
              <g className="wheel-spokes">
                <line
                  x1="80"
                  y1="20"
                  x2="80"
                  y2="52"
                  className="wheel-spoke--strong"
                />
                <line x1="80" y1="108" x2="80" y2="140" />
                <line x1="20" y1="80" x2="52" y2="80" />
                <line x1="108" y1="80" x2="140" y2="80" />
                <line x1="32" y1="32" x2="54" y2="54" />
                <line x1="106" y1="106" x2="128" y2="128" />
                <line x1="128" y1="32" x2="106" y2="54" />
                <line x1="32" y1="128" x2="54" y2="106" />
              </g>
              <circle cx="80" cy="80" r="18" className="wheel-hub" />
              <circle cx="80" cy="16" r="7" className="wheel-marker" />
              <circle cx="120" cy="44" r="5" className="wheel-valve" />
            </svg>
          </div>
        </div>
        <div className="splash-title">ClearDrive.lk</div>
        <div className="splash-subtitle">
          Japan Auction Imports - Sri Lanka Delivery
        </div>
        <div className="splash-vin">VIN PLATE: CD-JP-2026-AX04</div>
        <div className="splash-meta">
          <span>Auction</span>
          <span>Shipping</span>
          <span>Customs</span>
        </div>
        <div className="splash-route">
          <span className="splash-route__label">Tokyo -&gt; Hambantota</span>
          <span className="splash-route__line">
            <span className="splash-route__dot" />
          </span>
        </div>
        <div className="splash-lane">
          <span className="splash-lane__ship" />
        </div>
        <div className="splash-status">Confirming shipping slots...</div>
        <div className="splash-progress">
          <span />
        </div>
        <div className="splash-metrics">
          <div>
            <span className="splash-metrics__label">Auctions</span>
            <span className="splash-metrics__value">USS - JAA - CAI</span>
          </div>
          <div>
            <span className="splash-metrics__label">ETA</span>
            <span className="splash-metrics__value">14-18 Days</span>
          </div>
        </div>
      </div>
    </div>
  );
}
