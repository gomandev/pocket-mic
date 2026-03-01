"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Music2, Cpu, CheckCircle2, AlertCircle, XCircle, Play, ArrowLeft, Sparkles, LogOut } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import AudioPlayer from "@/components/audio/AudioPlayer";
import { logout } from "@/app/login/actions";

export default function ProjectVisualizer() {
    const { id } = useParams();
    const router = useRouter();
    const [job, setJob] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isCancelling, setIsCancelling] = useState(false);
    const [isRerunning, setIsRerunning] = useState(false);

    const rerunSession = async () => {
        if (!id || isRerunning) return;
        setIsRerunning(true);
        try {
            const res = await fetch(`/api/project/${id}/rerun`, { method: 'POST' });
            if (!res.ok) throw new Error("Rerun failed");
            const data = await res.json();
            setJob(data.job);
        } catch (err) {
            console.error("Rerun error:", err);
            setError("Failed to start rerun.");
        } finally {
            setIsRerunning(false);
        }
    };

    const cancelJob = async () => {
        if (!id || isCancelling) return;

        setIsCancelling(true);
        try {
            const res = await fetch(`/api/jobs/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'FAILED', error: 'Cancelled by user' }),
            });

            if (res.ok) {
                const data = await res.json();
                setJob(data);
            }
        } catch (err) {
            console.error("Cancel error:", err);
        } finally {
            setIsCancelling(false);
        }
    };

    useEffect(() => {
        if (!id) return;

        let pollCount = 0;
        const poll = async () => {
            try {
                const res = await fetch(`/api/jobs/${id}`);
                if (!res.ok) throw new Error("Failed to fetch job");
                const data = await res.json();
                setJob(data);
                setError(null);  // Clear any previous errors

                // Check if job completed or failed
                if (data.status === "COMPLETED" || data.status === "FAILED") {
                    return;  // Stop polling
                }

                // Continue polling with exponential backoff (but cap at 2s)
                pollCount++;
                const interval = Math.min(1000 + (pollCount * 100), 2000);
                setTimeout(poll, interval);
            } catch (err) {
                console.error("Polling error:", err);
                setError("Connection lost. Retrying...");
                // Retry after 3 seconds on error
                setTimeout(poll, 3000);
            }
        };

        poll();
    }, [id]);

    if (!job && !error) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
            </div>
        );
    }

    const steps = [
        { key: "QUEUED", label: "Waiting", icon: Cpu },
        { key: "ANALYZING", label: "Analyzing Voice", icon: Music2 },
        { key: "DESIGNING", label: "Building Beat", icon: Cpu },
        { key: "ARRANGING", label: "Final Polish", icon: CheckCircle2 },
    ];

    const currentStepIndex = steps.findIndex(s => s.key === job?.status);

    return (
        <div className="min-h-screen bg-background text-white p-6 md:p-12">
            <header className="max-w-4xl mx-auto flex justify-between items-center mb-12">
                <button onClick={() => router.push("/")} className="p-2 -ml-2 text-zinc-500 hover:text-white transition-colors">
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <Logo />
                <button
                    onClick={() => logout()}
                    className="flex items-center justify-center p-2 rounded-full text-zinc-500 hover:text-white hover:bg-white/10 transition-colors"
                    title="Sign Out"
                >
                    <LogOut className="w-5 h-5" />
                </button>
            </header>

            <main className="max-w-4xl mx-auto">
                <div className="mb-12">
                    <h1 className="text-4xl font-bold tracking-tight mb-2">Track Blueprint</h1>
                    <p className="text-zinc-500">Job ID: <span className="font-mono text-xs">{id}</span></p>
                </div>

                <AnimatePresence mode="wait">
                    {job?.status !== "COMPLETED" && job?.status !== "FAILED" ? (
                        <motion.div
                            key="processing"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="glass-card rounded-3xl p-8 mb-8"
                        >
                            <div className="flex items-center gap-6 mb-8">
                                <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/20">
                                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                                </div>
                                <div className="flex-1">
                                    <h2 className="text-xl font-bold uppercase tracking-widest text-primary mb-1">{job?.status || "PROCESSING"}</h2>
                                    <p className="text-zinc-400">
                                        {job?.status === "QUEUED" && "Preparing your session..."}
                                        {job?.status === "ANALYZING" && "Extracting vocal DNA..."}
                                        {job?.status === "DESIGNING" && "Generating AI instrumentation..."}
                                        {job?.status === "ARRANGING" && "Mixing and mastering..."}
                                        {!job?.status && "Our AI producer is working its magic."}
                                    </p>
                                    {typeof job?.progress === 'number' && (
                                        <div className="mt-3">
                                            <div className="flex justify-between text-xs text-zinc-500 mb-1">
                                                <span>Progress</span>
                                                <span>{job.progress}%</span>
                                            </div>
                                            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary transition-all duration-500"
                                                    style={{ width: `${job.progress}%` }}
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="space-y-4">
                                {steps.map((step, idx) => {
                                    const isDone = idx < currentStepIndex || job?.status === "COMPLETED";
                                    const isCurrent = idx === currentStepIndex;

                                    return (
                                        <div key={step.key} className="flex items-center gap-4">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center border transition-all duration-500 ${isDone ? "bg-primary border-primary" :
                                                isCurrent ? "border-primary animate-pulse" : "border-white/10 text-zinc-600"
                                                }`}>
                                                {isDone ? <CheckCircle2 className="w-5 h-5 text-black" /> : <step.icon className="w-4 h-4" />}
                                            </div>
                                            <span className={`font-medium ${isDone ? "text-white" : isCurrent ? "text-primary" : "text-zinc-600"}`}>
                                                {step.label}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="mt-12 h-2 bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${job?.progress || 0}%` }}
                                    className="h-full bg-primary shadow-[0_0_20px_rgba(139,92,246,0.5)]"
                                />
                            </div>

                            <button
                                onClick={cancelJob}
                                disabled={isCancelling}
                                className="mt-6 w-full py-3 bg-red-500/10 text-red-400 rounded-2xl font-medium text-sm hover:bg-red-500/20 transition-colors border border-red-500/20 disabled:opacity-50"
                            >
                                {isCancelling ? "Cancelling..." : "Cancel Processing"}
                            </button>
                        </motion.div>
                    ) : job?.status === "FAILED" ? (
                        <motion.div
                            key="failed"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-red-500/10 border border-red-500/20 rounded-3xl p-12 text-center"
                        >
                            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-6" />
                            <h2 className="text-2xl font-bold text-white mb-2">Production Failed</h2>
                            <p className="text-zinc-400 mb-8 max-w-md mx-auto">{job?.error || "An unexpected error occurred in the AI pipeline."}</p>
                            <div className="flex flex-col sm:flex-row gap-4 justify-center">
                                <button onClick={() => window.location.reload()} className="px-8 py-3 bg-white text-black rounded-xl font-bold text-sm">
                                    Refresh Page
                                </button>
                                <button
                                    onClick={rerunSession}
                                    disabled={isRerunning}
                                    className="px-8 py-3 bg-white/10 text-white rounded-xl font-bold text-sm hover:bg-white/20 transition-colors border border-white/10 flex items-center justify-center gap-2"
                                >
                                    {isRerunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                                    Rerun Production
                                </button>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="completed"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
                        >
                            {/* Main Result Card */}
                            <div className="lg:col-span-2 space-y-8">
                                <div className="glass-card rounded-[2.5rem] p-10 relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-8">
                                        <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/20">
                                            <Music2 className="w-8 h-8 text-primary" />
                                        </div>
                                    </div>

                                    <div className="relative z-10">
                                        <h3 className="text-xs font-bold tracking-[0.3em] uppercase text-zinc-500 mb-4">Production Blueprint</h3>
                                        <h2 className="text-6xl font-black text-white tracking-tighter mb-8 leading-none">
                                            {job?.result_plan?.analysis?.suggestedGenre || "Unknown Genre"}
                                        </h2>

                                        <div className="flex flex-wrap gap-4 mb-12">
                                            <div className="px-6 py-3 bg-white/5 rounded-2xl border border-white/10">
                                                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Tempo</p>
                                                <p className="text-2xl font-bold">{job?.result_plan?.analysis?.bpm} BPM</p>
                                            </div>
                                            <div className="px-6 py-3 bg-white/5 rounded-2xl border border-white/10">
                                                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Musical Key</p>
                                                <p className="text-2xl font-bold">{job?.result_plan?.analysis?.key}</p>
                                            </div>
                                            <div className="px-6 py-3 bg-white/5 rounded-2xl border border-white/10">
                                                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Mood</p>
                                                <p className="text-2xl font-bold capitalize">{job?.result_plan?.analysis?.mood}</p>
                                            </div>
                                            <div className="px-6 py-3 bg-white/5 rounded-2xl border border-white/10">
                                                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Version</p>
                                                <p className="text-2xl font-bold">V{job?.version || 1}</p>
                                            </div>
                                        </div>

                                        {/* Processed Audio Player */}
                                        <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
                                            <div className="flex items-center gap-3 mb-3">
                                                <Music2 className="w-5 h-5 text-primary" />
                                                <h4 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">
                                                    Final Production
                                                </h4>
                                            </div>

                                            {job?.result_plan?.processed_audio_url ? (
                                                <div className="space-y-4">
                                                    <p className="text-sm text-zinc-400 mb-4">
                                                        AI-generated beat mixed with your vocals.
                                                    </p>
                                                    <AudioPlayer
                                                        audioUrl={job.result_plan.processed_audio_url}
                                                        title="Mastered Track"
                                                    />
                                                    <button
                                                        onClick={() => router.push(`/project/${id}/master`)}
                                                        className="w-full py-4 bg-primary text-black rounded-xl font-bold text-sm hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
                                                    >
                                                        <Sparkles className="w-4 h-4" /> Open Mastering Suite
                                                    </button>
                                                    <button
                                                        onClick={rerunSession}
                                                        disabled={isRerunning}
                                                        className="w-full py-3 bg-white/5 text-zinc-400 rounded-xl font-medium text-xs hover:text-white transition-all flex items-center justify-center gap-2 border border-white/5"
                                                    >
                                                        {isRerunning ? (
                                                            <Loader2 className="w-3 h-3 animate-spin" />
                                                        ) : (
                                                            <Sparkles className="w-3 h-3" />
                                                        )}
                                                        Not liking the result? Rerun Production
                                                    </button>
                                                </div>
                                            ) : (
                                                <>
                                                    <p className="text-sm text-zinc-400 mb-4">
                                                        AI-generated beat with your vocals will be available here once synthesis is complete.
                                                    </p>
                                                    <button
                                                        disabled
                                                        className="w-full py-4 bg-white/5 text-zinc-600 rounded-xl font-bold text-sm cursor-not-allowed border border-white/5"
                                                    >
                                                        <Play className="w-5 h-5 inline mr-2" />
                                                        Processing Audio...
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="glass-card rounded-[2rem] p-8">
                                    <h4 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500 mb-6 underline decoration-primary underline-offset-8">Agent Feedback</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                                            <h5 className="font-bold text-primary mb-2 flex items-center gap-2">
                                                <Cpu className="w-4 h-4" /> Beat Designer
                                            </h5>
                                            <p className="text-sm text-zinc-400 italic">"Detected high energy in the vocal performance. Optimized the drum transients for maximum punch."</p>
                                        </div>
                                        <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                                            <h5 className="font-bold text-primary mb-2 flex items-center gap-2">
                                                <Music2 className="w-4 h-4" /> Audio Analyst
                                            </h5>
                                            <p className="text-sm text-zinc-400 italic">"Vocal resonance identified in the mid-range. Suggested {job?.result_plan?.analysis?.key} for instrumental harmonic balance."</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Sidebar / Metadata */}
                            <div className="space-y-6">
                                <AudioPlayer
                                    audioUrl={job?.audio_url || ""}
                                    title="Original Vocal Take"
                                />

                                <div className="p-8 rounded-[2rem] bg-primary flex flex-col items-center text-center">
                                    <div className="w-12 h-12 bg-black rounded-xl mb-4 flex items-center justify-center">
                                        <Logo />
                                    </div>
                                    <h4 className="font-bold text-black mb-2">Unlock Stem Exports</h4>
                                    <p className="text-black/60 text-xs mb-6">Get WAV stems for every generated instrument layer.</p>
                                    <button className="w-full py-3 bg-black text-white rounded-xl font-bold text-sm">
                                        Upgrade to Pro
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
}
