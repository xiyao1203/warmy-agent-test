import { ImageResponse } from "next/og";

export const alt = "Warmy Agent Test product mark";
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
        background: "#e94b43",
        borderRadius: "8px",
        display: "flex",
        height: "28px",
        justifyContent: "center",
        margin: "2px",
        width: "28px",
      }}
    >
      <svg
        fill="none"
        height="20"
        viewBox="0 0 24 24"
        width="20"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M12 2.5c.4 5.3 4.2 9.1 9.5 9.5-5.3.4-9.1 4.2-9.5 9.5-.4-5.3-4.2-9.1-9.5-9.5 5.3-.4 9.1-4.2 9.5-9.5Z"
          fill="white"
        />
        <circle cx="12" cy="12" fill="#e94b43" r="2" />
      </svg>
    </div>,
    size,
  );
}
