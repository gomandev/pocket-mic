"use client";

import { useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";

interface WaveformProps {
    audioUrl?: string;
    isRecording?: boolean;
}

export default function Waveform({ audioUrl, isRecording }: WaveformProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const wavesurferRef = useRef<WaveSurfer | null>(null);

    useEffect(() => {
        if (!containerRef.current || isRecording) return;

        wavesurferRef.current = WaveSurfer.create({
            container: containerRef.current,
            waveColor: "rgba(255, 255, 255, 0.1)",
            progressColor: "#8b5cf6",
            cursorColor: "#c084fc",
            barWidth: 3,
            barGap: 4,
            barRadius: 4,
            height: 120,
            normalize: true,
        });

        if (audioUrl) {
            wavesurferRef.current.load(audioUrl);
        }

        return () => {
            wavesurferRef.current?.destroy();
        };
    }, [audioUrl, isRecording]);

    return (
        <div className="relative w-full h-[140px] bg-zinc-900/30 rounded-3xl border border-white/5 overflow-hidden p-4">
            {isRecording && (
                <div className="waveform-vibe">
                    {[...Array(40)].map((_, i) => (
                        <div
                            key={i}
                            className="bar"
                            style={{
                                height: `${Math.random() * 60 + 20}%`,
                                animation: `pulseVibe 1.2s ease-in-out infinite`,
                                animationDelay: `${i * 0.04}s`,
                            }}
                        />
                    ))}
                    <style jsx>{`
            @keyframes pulseVibe {
              0%, 100% { height: 20%; opacity: 0.3; }
              50% { height: 80%; opacity: 1; }
            }
          `}</style>
                </div>
            )}
            <div ref={containerRef} className="w-full" />
        </div>
    );
}
