"use client";

export function IconfontProjectVisual() {
  return (
    <div
      aria-hidden="true"
      className="iconfont-project-visual"
      data-motion-source="iconfont-cn-lottie-inspired"
      data-testid="project-empty-visual"
      data-visual-kind="project-empty-3d"
      data-visual-source="iconfont-cn-3d-inspired"
    >
      <svg fill="none" viewBox="0 0 240 160" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="projectDeck"
            x1="52"
            x2="182"
            y1="42"
            y2="136"
          >
            <stop stopColor="#E0F2FE" />
            <stop offset="0.48" stopColor="#93C5FD" />
            <stop offset="1" stopColor="#8B5CF6" />
          </linearGradient>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="projectPanel"
            x1="74"
            x2="171"
            y1="36"
            y2="111"
          >
            <stop stopColor="#FFFFFF" />
            <stop offset="1" stopColor="#E8F7FF" />
          </linearGradient>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="projectCube"
            x1="104"
            x2="161"
            y1="36"
            y2="92"
          >
            <stop stopColor="#34D399" />
            <stop offset="0.5" stopColor="#06B6D4" />
            <stop offset="1" stopColor="#2563EB" />
          </linearGradient>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="projectWarm"
            x1="167"
            x2="208"
            y1="47"
            y2="93"
          >
            <stop stopColor="#FDE68A" />
            <stop offset="1" stopColor="#F97316" />
          </linearGradient>
        </defs>
        <ellipse
          className="iconfont-visual-shadow"
          cx="121"
          cy="133"
          fill="#0F172A"
          opacity="0.12"
          rx="82"
          ry="14"
        />
        <path d="M52 60 118 28l70 31-63 42-73-41Z" fill="url(#projectDeck)" />
        <path d="m52 60 73 41v34l-73-42V60Z" fill="#2563EB" opacity="0.78" />
        <path d="m125 101 63-42v34l-63 42v-34Z" fill="#7C3AED" opacity="0.8" />
        <g className="iconfont-visual-float">
          <path
            d="M80 48h76c9 0 16 7 16 16v31c0 9-7 16-16 16H80c-9 0-16-7-16-16V64c0-9 7-16 16-16Z"
            fill="url(#projectPanel)"
          />
          <path
            d="M88 68h47M88 84h62M88 100h36"
            stroke="#60A5FA"
            strokeLinecap="round"
            strokeWidth="6"
          />
          <rect
            fill="#7C3AED"
            height="14"
            opacity="0.78"
            rx="4"
            width="14"
            x="144"
            y="69"
          />
          <rect
            fill="#7C3AED"
            height="14"
            opacity="0.78"
            rx="4"
            width="14"
            x="144"
            y="94"
          />
        </g>
        <g className="iconfont-visual-pulse">
          <path d="M128 26 154 39l-26 15-26-15 26-13Z" fill="#A7F3D0" />
          <path d="m102 39 26 15v28l-26-16V39Z" fill="#0EA5E9" />
          <path d="m128 54 26-15v28l-26 15V54Z" fill="url(#projectCube)" />
          <path
            d="M116 52v13l12 7 12-7V52"
            stroke="#FFFFFF"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="4"
          />
        </g>
        <g className="iconfont-visual-spark">
          <circle cx="190" cy="69" fill="url(#projectWarm)" r="16" />
          <path
            d="M184 70h12M190 64v12"
            stroke="#FFFFFF"
            strokeLinecap="round"
            strokeWidth="4"
          />
        </g>
        <g className="iconfont-visual-spark iconfont-visual-spark-secondary">
          <circle cx="51" cy="44" fill="#F472B6" r="9" />
          <path
            d="M47 44h8M51 40v8"
            stroke="#FFFFFF"
            strokeLinecap="round"
            strokeWidth="3"
          />
        </g>
      </svg>
    </div>
  );
}

export function ProjectLoadingMotion() {
  return (
    <div
      className="project-loading-motion"
      data-motion-source="iconfont-cn-lottie-inspired"
      data-testid="project-loading-motion"
    >
      <span aria-hidden="true" className="project-loading-motion-orbit">
        <span />
      </span>
      <span>正在加载项目...</span>
    </div>
  );
}
