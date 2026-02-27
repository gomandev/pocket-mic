"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Mic, Square, Trash2, CheckCircle2, Loader2, Play, Pause, Upload } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Waveform from "./Waveform";

type SessionState = "IDLE" | "RECORDING" | "PROCESSING" | "COMPLETED";

export default function AudioRecorder() {
    const router = useRouter();
    const [state, setState] = useState<SessionState>("IDLE");
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            mediaRecorderRef.current = recorder;
            chunksRef.current = [];

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            recorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: "audio/wav" });
                const url = URL.createObjectURL(blob);
                setAudioUrl(url);
                uploadAudio(blob);
            };

            recorder.start();
            setState("RECORDING");
        } catch (err) {
            console.error("Error accessing microphone:", err);
        }
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
        mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
        setState("PROCESSING");
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            uploadAudio(file);
        }
    };

    const uploadAudio = async (blob: Blob) => {
        setState("PROCESSING");
        setProcessingStatus("Uploading...");
        const formData = new FormData();
        formData.append("audio", blob, "vocal_take.wav");

        try {
            const response = await fetch("/api/ingest", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Upload failed");

            const { jobId } = await response.json();

            // REDIRECT TO DEDICATED VISUALIZER
            router.push(`/project/${jobId}`);
        } catch (err) {
            console.error("Upload error:", err);
            setState("IDLE");
        }
    };

    const pollJobStatus = async (jobId: string) => {
        const poll = async () => {
            try {
                const response = await fetch(`/api/jobs/${jobId}`);
                if (!response.ok) throw new Error("Polling failed");

                const job = await response.json();

                // Map job status to UI messages
                const statusMessages: Record<string, string> = {
                    "ANALYZING": "Analyzing your voice...",
                    "DESIGNING": "Designing the beat...",
                    "ARRANGING": "Arranging the track...",
                    "COMPLETED": "Finishing up...",
                };

                if (job.status === "COMPLETED") {
                    setResultPlan(job.result_plan);
                    setState("COMPLETED");
                    return;
                }

                if (job.status === "FAILED") {
                    throw new Error(job.error || "Processing failed");
                }

                setProcessingStatus(statusMessages[job.status] || "Processing...");
                setTimeout(poll, 1500); // Poll every 1.5s
            } catch (err) {
                console.error("Polling error:", err);
                setState("IDLE");
            }
        };

        poll();
    };

    const [processingStatus, setProcessingStatus] = useState("Processing...");
    const [resultPlan, setResultPlan] = useState<any>(null);

    const reset = () => {
        setAudioUrl(null);
        setState("IDLE");
    };

    return (
        <div className="flex flex-col items-center w-full max-w-2xl mx-auto space-y-8 sm:space-y-12 h-full justify-center">
            <div className="w-full relative py-8 sm:py-12 px-4 sm:px-0">
                <AnimatePresence mode="wait">
                    {state === "IDLE" && (
                        <motion.div
                            key="idle"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="text-center space-y-3 sm:space-y-4"
                        >
                            <h2 className="text-3xl sm:text-4xl font-medium text-white tracking-tight">Start Your Session</h2>
                            <p className="text-zinc-400 max-w-sm mx-auto text-sm sm:text-base leading-relaxed">
                                Capture your voice or a melody sketch. Our AI handles the rest.
                            </p>
                        </motion.div>
                    )}

                    {(state === "RECORDING" || state === "PROCESSING") && (
                        <motion.div
                            key="visualizing"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="w-full"
                        >
                            <Waveform isRecording={state === "RECORDING"} />
                            {state === "PROCESSING" && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/60 backdrop-blur-md rounded-2xl z-20 space-y-5">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                                        <Loader2 className="w-10 h-10 text-primary animate-spin relative z-10" />
                                    </div>
                                    <div className="text-center space-y-1">
                                        <p className="text-white font-medium tracking-wide">{processingStatus}</p>
                                        <p className="text-zinc-500 text-xs sm:text-sm uppercase tracking-widest font-bold">Designing the perfect beat</p>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {state === "COMPLETED" && resultPlan && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute inset-0 z-30 flex items-center justify-center p-4 sm:p-6"
                        >
                            <div className="glass-card w-full max-w-sm rounded-[2rem] p-6 sm:p-8 flex flex-col space-y-6 shadow-2xl relative overflow-hidden group">
                                {/* Background Glow */}
                                <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/15 rounded-full blur-3xl group-hover:bg-primary/25 transition-all duration-700" />

                                <div className="flex justify-between items-start relative z-10">
                                    <div>
                                        <h3 className="text-primary text-[10px] sm:text-xs font-bold tracking-[0.2em] uppercase mb-1 drop-shadow-[0_0_10px_rgba(18,212,255,0.3)]">Production Loaded</h3>
                                        <p className="text-xl sm:text-2xl font-bold text-white tracking-tight">{resultPlan.analysis.suggestedGenre}</p>
                                    </div>
                                    <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/20">
                                        <Music2 className="w-5 h-5 text-primary" />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.05]">
                                        <p className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1">Tempo</p>
                                        <p className="text-xl font-medium text-white">{resultPlan.analysis.bpm} <span className="text-xs text-zinc-500">BPM</span></p>
                                    </div>
                                    <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.05]">
                                        <p className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1">Key</p>
                                        <p className="text-xl font-medium text-white">{resultPlan.analysis.key}</p>
                                    </div>
                                </div>

                                <div className="space-y-3 relative z-10">
                                    <button className="w-full py-3.5 sm:py-4 bg-white text-black rounded-2xl font-bold text-sm hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2 group tactile-button">
                                        <Play className="w-4 h-4 fill-current group-hover:scale-110 transition-transform" />
                                        Preview Master
                                    </button>
                                    <button
                                        onClick={reset}
                                        className="w-full py-3.5 sm:py-4 bg-white/[0.03] text-zinc-400 rounded-2xl font-bold text-sm hover:bg-white/[0.08] hover:text-white transition-all border border-white/[0.05] tactile-button"
                                    >
                                        New Session
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {state === "COMPLETED" && (
                        <motion.div
                            key="completed"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="w-full space-y-6"
                        >
                            <div className="glass-card p-6 rounded-2xl">
                                <div className="flex items-center justify-between mb-4 sm:mb-6">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30">
                                            <Music2 className="w-4 h-4 text-primary" />
                                        </div>
                                        <span className="font-semibold text-white tracking-wide">Mastered Result</span>
                                    </div>
                                    <CheckCircle2 className="w-5 h-5 text-primary drop-shadow-[0_0_8px_rgba(18,212,255,0.5)]" />
                                </div>
                                <Waveform audioUrl={audioUrl || undefined} />
                                <div className="flex items-center justify-center space-x-4 sm:space-x-6 mt-6 sm:mt-8">
                                    <button className="p-3 sm:p-4 rounded-full bg-white text-black hover:bg-zinc-200 transition-colors tactile-button">
                                        <Play className="w-5 h-5 sm:w-6 sm:h-6 fill-current ml-0.5" />
                                    </button>
                                    <button onClick={reset} className="text-zinc-400 hover:text-white transition-colors text-xs sm:text-sm font-medium uppercase tracking-wider py-2 px-4 rounded-full hover:bg-white/5 tactile-button">
                                        Try Another Take
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Main Record Action */}
            <div className="relative pb-8 sm:pb-0">
                <AnimatePresence>
                    {state === "IDLE" || state === "RECORDING" ? (
                        <motion.button
                            layoutId="record-btn"
                            onClick={state === "RECORDING" ? stopRecording : startRecording}
                            className={`group tactile-button relative w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center transition-all ${state === "RECORDING" ? "bg-red-500 lg:w-28 lg:h-28" : "bg-card border border-white/10"
                                }`}
                        >
                            <div className={`absolute inset-0 rounded-full transition-all duration-500 ${state === "RECORDING" ? "animate-ping-slow bg-red-400" : "group-hover:bg-primary/20 blur-xl mix-blend-screen"
                                }`} />

                            <div className="relative z-10">
                                {state === "RECORDING" ? (
                                    <Square className="w-6 h-6 sm:w-8 sm:h-8 text-white fill-white" />
                                ) : (
                                    <Mic className="w-8 h-8 sm:w-10 sm:h-10 text-primary group-hover:scale-110 transition-transform drop-shadow-[0_0_8px_rgba(18,212,255,0.4)]" />
                                )}
                            </div>
                        </motion.button>
                    ) : null}
                </AnimatePresence>
            </div>

            {state === "IDLE" && (
                <>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept="audio/*"
                        onChange={handleFileUpload}
                    />
                    <motion.button
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center space-x-2 text-zinc-500 hover:text-white transition-colors text-xs sm:text-sm font-medium py-2 px-4 rounded-full border border-transparent hover:border-white/10 hover:bg-white/5 tactile-button"
                    >
                        <Upload className="w-4 h-4" />
                        <span>or upload existing audio</span>
                    </motion.button>
                </>
            )}
        </div>
    );
}

// Internal icons helper
function Music2(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
        </svg>
    );
}
