"use client";

import { useEffect, useRef, useState } from "react";
import { Play, Pause, Volume2, Download } from "lucide-react";
import { motion } from "framer-motion";

interface AudioPlayerProps {
    audioUrl: string;
    title?: string;
}

export default function AudioPlayer({ audioUrl, title = "Audio Track" }: AudioPlayerProps) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(0.8);
    const [waveformData, setWaveformData] = useState<number[]>([]);

    // Load and decode audio for waveform
    useEffect(() => {
        const loadAudio = async () => {
            try {
                const response = await fetch(audioUrl);
                const arrayBuffer = await response.arrayBuffer();
                const audioContext = new AudioContext();
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

                // Extract waveform data
                const rawData = audioBuffer.getChannelData(0);
                const samples = 100; // Number of bars in waveform
                const blockSize = Math.floor(rawData.length / samples);
                const filteredData = [];

                for (let i = 0; i < samples; i++) {
                    let blockStart = blockSize * i;
                    let sum = 0;
                    for (let j = 0; j < blockSize; j++) {
                        sum += Math.abs(rawData[blockStart + j]);
                    }
                    filteredData.push(sum / blockSize);
                }

                setWaveformData(filteredData);
            } catch (error) {
                console.error("Error loading audio:", error);
            }
        };

        loadAudio();
    }, [audioUrl]);

    // Draw waveform
    useEffect(() => {
        if (!canvasRef.current || waveformData.length === 0) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const width = canvas.offsetWidth;
        const height = canvas.offsetHeight;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        ctx.clearRect(0, 0, width, height);

        const barWidth = width / waveformData.length;
        const progress = duration > 0 ? currentTime / duration : 0;

        waveformData.forEach((value, index) => {
            const barHeight = value * height * 0.8;
            const x = index * barWidth;
            const y = (height - barHeight) / 2;

            // Gradient based on progress
            const isPast = index / waveformData.length < progress;
            ctx.fillStyle = isPast ? "rgba(18, 212, 255, 0.8)" : "rgba(255, 255, 255, 0.2)";
            ctx.fillRect(x, y, barWidth - 2, barHeight);
        });
    }, [waveformData, currentTime, duration]);

    // Audio event handlers
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const updateTime = () => setCurrentTime(audio.currentTime);
        const updateDuration = () => setDuration(audio.duration);
        const handleEnded = () => setIsPlaying(false);

        audio.addEventListener("timeupdate", updateTime);
        audio.addEventListener("loadedmetadata", updateDuration);
        audio.addEventListener("ended", handleEnded);

        return () => {
            audio.removeEventListener("timeupdate", updateTime);
            audio.removeEventListener("loadedmetadata", updateDuration);
            audio.removeEventListener("ended", handleEnded);
        };
    }, []);

    // Volume control
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume;
        }
    }, [volume]);

    const togglePlay = () => {
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    const handleSeek = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!audioRef.current || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = x / rect.width;
        audioRef.current.currentTime = percentage * duration;
    };

    const formatTime = (time: number) => {
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, "0")}`;
    };

    const handleDownload = () => {
        const a = document.createElement("a");
        a.href = audioUrl;
        a.download = `${title}.wav`;
        a.click();
    };

    return (
        <div className="glass-card rounded-[2rem] p-5 sm:p-8 space-y-5 sm:space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-[10px] sm:text-xs font-bold uppercase tracking-[0.2em] text-primary mb-1 drop-shadow-[0_0_8px_rgba(18,212,255,0.4)]">
                        Audio Playback
                    </h3>
                    <p className="text-base sm:text-lg font-medium text-white tracking-tight">{title}</p>
                </div>
                <button
                    onClick={handleDownload}
                    className="p-2.5 sm:p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/10 tactile-button"
                >
                    <Download className="w-5 h-5 text-white" />
                </button>
            </div>

            {/* Waveform */}
            <div className="relative w-full h-20 sm:h-32 rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden">
                <canvas
                    ref={canvasRef}
                    onClick={handleSeek}
                    className="absolute inset-0 w-full h-full cursor-pointer"
                />
            </div>

            {/* Controls */}
            <div className="flex items-center gap-4 sm:gap-6">
                <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={togglePlay}
                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center hover:scale-105 transition-transform shadow-tactile-hover tactile-button shrink-0"
                >
                    {isPlaying ? (
                        <Pause className="w-5 h-5 sm:w-6 sm:h-6 text-black fill-black" />
                    ) : (
                        <Play className="w-5 h-5 sm:w-6 sm:h-6 text-black fill-black ml-1" />
                    )}
                </motion.button>

                <div className="flex-1 space-y-2 min-w-0">
                    <div className="flex items-center justify-between text-[10px] sm:text-xs text-zinc-500 font-medium">
                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-primary to-secondary"
                            style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                        />
                    </div>
                </div>

                <div className="hidden sm:flex items-center gap-3">
                    <Volume2 className="w-5 h-5 text-zinc-500" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        value={volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="w-24 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
                    />
                </div>
            </div>

            <audio ref={audioRef} src={audioUrl} preload="metadata" />
        </div>
    );
}
