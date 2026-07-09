import { ImageResponse } from "next/og";

export const alt = "Warmy Agent Test 3D logo";
export const size = {
  height: 32,
  width: 32,
};
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        alignItems: "center",
        background: "transparent",
        display: "flex",
        height: "32px",
        justifyContent: "center",
        width: "32px",
      }}
    >
      <svg
        fill="none"
        height="32"
        viewBox="0 0 64 64"
        width="32"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="faviconFace"
            x1="13"
            x2="52"
            y1="9"
            y2="54"
          >
            <stop stopColor="#55E6FF" />
            <stop offset="0.45" stopColor="#1677FF" />
            <stop offset="1" stopColor="#7C3AED" />
          </linearGradient>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="faviconEdge"
            x1="20"
            x2="54"
            y1="47"
            y2="23"
          >
            <stop stopColor="#0EA5E9" />
            <stop offset="1" stopColor="#F59E0B" />
          </linearGradient>
          <linearGradient
            gradientUnits="userSpaceOnUse"
            id="faviconCore"
            x1="19"
            x2="45"
            y1="21"
            y2="45"
          >
            <stop stopColor="#FFFFFF" />
            <stop offset="1" stopColor="#DDF6FF" />
          </linearGradient>
        </defs>
        <ellipse cx="33" cy="52" fill="#0F172A" opacity="0.14" rx="23" ry="7" />
        <path
          d="M18 14.5 36 8l15.5 9.5V42L34 55.5 15 45V21.5l3-7Z"
          fill="url(#faviconFace)"
        />
        <path
          d="m36 8 15.5 9.5L34 30.5 18 14.5 36 8Z"
          fill="#A7F3D0"
          opacity="0.9"
        />
        <path d="m34 30.5 17.5-13V42L34 55.5v-25Z" fill="url(#faviconEdge)" />
        <path
          d="M18 14.5 34 30.5v25L15 45V21.5l3-7Z"
          fill="#2563EB"
          opacity="0.74"
        />
        <path
          d="M23 28.5c0-4.7 3.8-8.5 8.5-8.5h5.3c4.5 0 8.2 3.7 8.2 8.2v2.4c0 4.4-3.6 8-8 8h-2.6l-7.2 5.2v-5.2h-3.7A6.5 6.5 0 0 1 17 32.1v-1.6c0-1.1.9-2 2-2h4Z"
          fill="url(#faviconCore)"
        />
        <path
          d="M27 29.5h13M31.5 25v9M26.5 34.5h5.8M36.5 34.5H41"
          stroke="#0B63CE"
          strokeLinecap="round"
          strokeWidth="3"
        />
        <circle cx="49" cy="14" fill="#FFB020" r="4" />
        <circle cx="17" cy="50" fill="#32D583" r="3" />
      </svg>
    </div>,
    {
      ...size,
    },
  );
}
