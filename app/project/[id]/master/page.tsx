"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Loader2,
    Music2,
    ArrowLeft,
    Sparkles,
    Settings2,
    Volume2,
    Activity,
    Waves as WaveformIcon,
    Wand2,
    Save,
    RotateCcw,
    Play,
    Pause
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import AudioPlayer from "@/components/audio/AudioPlayer";
import { Job, Jobs } from "@/lib/jobs";

export default function MasteringPage() {
    const { id } = useParams();
    const router = useRouter();
    const [job, setJob] = useState<Job | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"ai" | "manual">("ai");
    const [isProcessing, setIsProcessing] = useState(false);

    // Mastering Controls State
    const [gain, setGain] = useState(0);
    const [width, setWidth] = useState(75);
    const [punch, setPunch] = useState(65);
    const [style, setStyle] = useState("Radio Ready");

    useEffect(() => {
        if (!id) return;
        const fetchJob = async () => {
            try {
                const res = await Jobs.get(id as string);
                if (res) {
                    setJob(res);
                }
            } catch (err) {
                console.error("Failed to fetch job:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchJob();
    }, [id]);

    const handleAISmartEnhance = async () => {
        if (!id) return;
        setIsProcessing(true);
        try {
            await Jobs.master(id as string, style, punch, width);
            // Polling for completion would be better, but for now we wait a bit and refresh
            setTimeout(async () => {
                const updated = await Jobs.get(id as string);
                if (updated) setJob(updated);
                setIsProcessing(false);
            }, 5000);
        } catch (err) {
            console.error("Mastering failed:", err);
            setIsProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-white p-6 md:px-12">
            <header className="max-w-7xl mx-auto flex justify-between items-center mb-8">
                <button
                    onClick={() => router.push("/projects")}
                    className="p-2 -ml-2 text-zinc-500 hover:text-white transition-colors group flex items-center gap-2"
                >
                    <ArrowLeft className="w-6 h-6 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-sm font-medium">Back to Studio</span>
                </button>
                <Logo />
                <div className="flex gap-4">
                    <button className="px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-sm font-bold hover:bg-white/10 transition-colors flex items-center gap-2">
                        <RotateCcw className="w-4 h-4" /> Reset
                    </button>
                    <button className="px-6 py-2 bg-primary text-black rounded-xl text-sm font-bold hover:scale-105 transition-transform flex items-center gap-2">
                        <Save className="w-4 h-4" /> Export Master
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Waveforms & Preview */}
                <div className="lg:col-span-8 space-y-6">
                    <div className="glass-card rounded-[2.5rem] p-8 overflow-hidden relative">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h1 className="text-2xl font-bold mb-1">Mastering Suite</h1>
                                <p className="text-sm text-zinc-500 font-mono uppercase tracking-widest">
                                    {job?.result_plan?.analysis?.suggestedGenre || "Custom Track"} // {id?.toString().slice(0, 8)}
                                </p>
                            </div>
                            <div className="flex p-1 bg-black/40 rounded-xl border border-white/5">
                                <button
                                    onClick={() => setActiveTab("ai")}
                                    className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === "ai" ? "bg-primary text-black" : "text-zinc-500 hover:text-white"}`}
                                >
                                    AI Assist
                                </button>
                                <button
                                    onClick={() => setActiveTab("manual")}
                                    className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === "manual" ? "bg-primary text-black" : "text-zinc-500 hover:text-white"}`}
                                >
                                    Manual
                                </button>
                            </div>
                        </div>

                        {/* Visualizer Placeholder */}
                        <div className="relative aspect-[21/9] bg-black/40 rounded-3xl border border-white/5 overflow-hidden flex items-center justify-center group">
                            <div className="absolute inset-0 flex items-center justify-around px-8 opacity-20">
                                {[...Array(40)].map((_, i) => (
                                    <motion.div
                                        key={i}
                                        animate={{ height: [40, Math.random() * 100 + 20, 40] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.05 }}
                                        className="w-1 bg-primary rounded-full"
                                        style={{ height: '40%' }}
                                    />
                                ))}
                            </div>
                            <div className="relative z-10 flex flex-col items-center">
                                <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center border border-primary/20 backdrop-blur-xl group-hover:scale-110 transition-transform">
                                    <Play className="w-8 h-8 text-primary fill-current ml-1" />
                                </div>
                                <p className="mt-4 text-xs font-bold uppercase tracking-[0.3em] text-primary/60">Tap to Preview</p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="glass-card p-6 rounded-3xl">
                            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <Activity className="w-4 h-4" /> Spectrum Analysis
                            </h3>
                            <div className="h-32 flex items-end gap-1 opacity-40">
                                {[...Array(20)].map((_, i) => (
                                    <div key={i} className="flex-1 bg-white/20 rounded-t-sm" style={{ height: `${Math.random() * 80 + 20}%` }} />
                                ))}
                            </div>
                        </div>
                        <div className="glass-card p-6 rounded-3xl">
                            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <Volume2 className="w-4 h-4" /> Dynamics Meter
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-[10px] uppercase font-bold text-zinc-600 mb-1">
                                        <span>Peak Level</span>
                                        <span>-0.1 dB</span>
                                    </div>
                                    <div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                        <div className="h-full bg-green-500/60 w-[95%]" />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-[10px] uppercase font-bold text-zinc-600 mb-1">
                                        <span>Dynamic Range (LUFS)</span>
                                        <span>-12.4</span>
                                    </div>
                                    <div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                        <div className="h-full bg-primary/60 w-[70%]" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="glass-card p-8 rounded-[2rem] flex flex-col md:flex-row items-center gap-8">
                        <div className="flex-1 w-full">
                            <AudioPlayer
                                audioUrl={job?.result_plan?.processed_audio_url || ""}
                                title="Final Production"
                            />
                        </div>
                        <div className="w-px h-12 bg-white/10 hidden md:block" />
                        <div className="flex flex-col items-center">
                            <p className="text-[10px] uppercase font-black text-zinc-500 mb-2">Reference</p>
                            <button className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors">
                                <Music2 className="w-5 h-5 text-zinc-400" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Column: Controls */}
                <div className="lg:col-span-4 space-y-6">
                    <AnimatePresence mode="wait">
                        {activeTab === "ai" ? (
                            <motion.div
                                key="ai"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="glass-card rounded-[2.5rem] p-8"
                            >
                                <div className="flex items-center gap-4 mb-8">
                                    <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center text-primary">
                                        <Sparkles className="w-6 h-6" />
                                    </div>
                                    <h2 className="text-xl font-bold">AI Mastering</h2>
                                </div>

                                <div className="space-y-8">
                                    <div className="space-y-4">
                                        <p className="text-xs font-bold uppercase tracking-widest text-zinc-500">Mastering Style</p>
                                        <div className="grid grid-cols-2 gap-3">
                                            {["Balanced", "Radio Ready", "Warmer", "Club Punch"].map(s => (
                                                <button
                                                    key={s}
                                                    onClick={() => setStyle(s)}
                                                    className={`py-3 rounded-2xl text-xs font-bold border transition-all ${style === s ? "bg-primary border-primary text-black" : "bg-white/5 border-white/5 text-zinc-500 hover:border-white/10"}`}
                                                >
                                                    {s}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="p-6 rounded-3xl bg-primary/5 border border-primary/10">
                                        <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                                            <Wand2 className="w-4 h-4" /> Smart Enhance
                                        </h3>
                                        <p className="text-xs text-zinc-500 mb-6">Let our AI analyze the transients and harmonic profile for optimal clarity.</p>
                                        <button
                                            onClick={handleAISmartEnhance}
                                            disabled={isProcessing}
                                            className="w-full py-4 bg-primary text-black rounded-2xl font-black text-sm hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
                                        >
                                            {isProcessing ? (
                                                <span className="flex items-center justify-center gap-2">
                                                    <Loader2 className="w-4 h-4 animate-spin" /> Optimizing...
                                                </span>
                                            ) : "Apply AI Polish"}
                                        </button>
                                    </div>

                                    <div className="space-y-6 pt-4 border-t border-white/5">
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <label className="text-xs font-bold uppercase text-zinc-500">Energy Boost</label>
                                                <span className="text-xs font-mono text-primary">{punch}%</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="0"
                                                max="100"
                                                value={punch}
                                                onChange={(e) => setPunch(parseInt(e.target.value))}
                                                className="w-full accent-primary"
                                            />
                                        </div>
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <label className="text-xs font-bold uppercase text-zinc-500">Stereo Width</label>
                                                <span className="text-xs font-mono text-primary">{width}%</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="0"
                                                max="100"
                                                value={width}
                                                onChange={(e) => setWidth(parseInt(e.target.value))}
                                                className="w-full accent-primary"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="manual"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="glass-card rounded-[2.5rem] p-8"
                            >
                                <div className="flex items-center gap-4 mb-8">
                                    <div className="w-12 h-12 rounded-2xl bg-zinc-800 flex items-center justify-center text-zinc-400">
                                        <Settings2 className="w-6 h-6" />
                                    </div>
                                    <h2 className="text-xl font-bold">Manual Precision</h2>
                                </div>

                                <div className="space-y-8">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center">
                                            <span className="text-[10px] font-bold text-zinc-500 uppercase mb-4 tracking-widest">Gain</span>
                                            <div className="h-32 w-2 bg-black/40 rounded-full relative">
                                                <motion.div
                                                    className="absolute bottom-0 w-full bg-primary rounded-full shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                                    style={{ height: `${(gain + 12) / 24 * 100}%` }}
                                                />
                                            </div>
                                            <span className="mt-4 text-xs font-mono">{gain > 0 ? '+' : ''}{gain.toFixed(1)} dB</span>
                                        </div>
                                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center">
                                            <span className="text-[10px] font-bold text-zinc-500 uppercase mb-4 tracking-widest">Output</span>
                                            <div className="h-32 w-2 bg-black/40 rounded-full relative">
                                                <div className="absolute bottom-0 w-full bg-green-500/60 rounded-full h-[80%]" />
                                            </div>
                                            <span className="mt-4 text-xs font-mono">-1.0 dB</span>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h4 className="text-xs font-bold uppercase text-zinc-500 tracking-widest border-b border-white/5 pb-2">EQ Shaping</h4>
                                        <div className="flex justify-between items-end h-24 gap-2">
                                            {[30, 60, 45, 20, 50, 70, 40].map((h, i) => (
                                                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                                                    <div className="w-1.5 h-full bg-black/40 rounded-full relative">
                                                        <div className="absolute bottom-0 w-full bg-primary/40 rounded-full" style={{ height: `${h}%` }} />
                                                    </div>
                                                    <span className="text-[8px] font-mono text-zinc-600">{(i + 1) * 2}k</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="p-6 rounded-3xl bg-white/5 border border-white/10 text-center">
                                        <p className="text-[10px] text-zinc-500 uppercase font-bold mb-2">Pro Feature</p>
                                        <p className="text-xs text-zinc-400 mb-4 italic">Individual stem processing & multi-band compression.</p>
                                        <button className="text-xs font-bold text-primary hover:underline">Upgrade to Studio Pro</button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="p-8 rounded-[2rem] bg-zinc-900 border border-white/5">
                        <h4 className="font-bold mb-2 flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-primary" /> Why AI First?
                        </h4>
                        <p className="text-xs text-zinc-500 leading-relaxed">
                            PocketMic's AI analysis understands the emotional curve of your vocals. Unlike traditional limiters, our smart mastering adjusts to your specific performance intensity.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
