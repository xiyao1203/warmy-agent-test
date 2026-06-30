"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";

type VideoPlayerProps = {
  src: string;
  onDownload?: () => void;
};

export function VideoPlayer({ src, onDownload }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handlePlayPause = () => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleToggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleDownloadClick = () => {
    if (onDownload) {
      onDownload();
    } else {
      // 默认下载行为
      const link = document.createElement("a");
      link.href = src;
      link.download = "video.mp4";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      {/* 视频元素 */}
      <video
        ref={videoRef}
        src={src}
        className="w-full rounded-[var(--radius-md)]"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />

      {/* 控制栏 */}
      <div className="flex items-center gap-2">
        <Button variant="secondary" onClick={handlePlayPause}>
          {isPlaying ? "暂停" : "播放"}
        </Button>

        <Button variant="secondary" onClick={handleToggleMute}>
          {isMuted ? "静音" : "音量"}
        </Button>

        <span className="flex-1 text-center text-sm text-[var(--text-muted)]">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <Button variant="secondary" onClick={handleDownloadClick}>
          下载
        </Button>
      </div>
    </div>
  );
}
