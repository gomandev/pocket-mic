"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Loader2,
    Music2,
    ChevronRight,
    Search,
    Clock,
    Plus,
    Play,
    MoreVertical,
    FileAudio,
    Calendar,
    LogOut
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Job, Jobs } from "@/lib/jobs";
import { logout } from "@/app/login/actions";

export default function ProjectsPage() {
    const router = useRouter();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                const res = await Jobs.list();
                setJobs(res);
            } catch (err) {
                console.error("Failed to fetch jobs:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchJobs();
    }, []);

    const filteredJobs = jobs.filter(job =>
        (job.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-background text-white p-6 md:p-12 font-sans selection:bg-primary/30">
            <header className="max-w-7xl mx-auto flex justify-between items-center mb-16">
                <Logo />
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => logout()}
                        className="flex items-center justify-center p-2.5 rounded-full text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                        title="Sign Out"
                    >
                        <LogOut className="w-5 h-5" />
                    </button>
                    <button
                        onClick={() => router.push("/")}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white text-black rounded-full font-bold hover:bg-zinc-200 transition-all text-sm"
                    >
                        <Plus className="w-4 h-4" />
                        New Session
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
                    <div>
                        <h1 className="text-5xl font-black tracking-tight mb-4 text-white">Studio Hub</h1>
                        <p className="text-zinc-500 font-medium max-w-lg">
                            Your handcrafted music workspace. Manage and refine your professional sessions.
                        </p>
                    </div>

                    <div className="relative group max-w-sm w-full">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-white transition-colors" />
                        <input
                            type="text"
                            placeholder="Find a session..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-2xl py-3 pl-12 pr-6 focus:outline-none focus:border-white/20 transition-all text-sm placeholder:text-zinc-600"
                        />
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-32 opacity-20">
                        <Loader2 className="w-8 h-8 text-white animate-spin" />
                    </div>
                ) : filteredJobs.length === 0 ? (
                    <div className="text-center py-32 glass-card rounded-[3rem] border-dashed border border-white/5">
                        <FileAudio className="w-12 h-12 text-zinc-800 mx-auto mb-6" />
                        <h3 className="text-lg font-bold text-zinc-400 mb-2">Workspace Empty</h3>
                        <p className="text-zinc-600 text-sm mb-8">Ready to start your first handcrafted session?</p>
                        <button
                            onClick={() => router.push("/")}
                            className="px-8 py-3 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-colors text-sm font-bold"
                        >
                            Start Session
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <AnimatePresence>
                            {filteredJobs.map((job) => (
                                <motion.div
                                    key={job.id}
                                    layout
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    whileHover={{ y: -4 }}
                                    onClick={() => router.push(`/project/${job.id}`)}
                                    className="group relative bg-[#121212] border border-white/5 p-8 rounded-[2.5rem] cursor-pointer hover:border-white/10 transition-all"
                                >
                                    <div className="flex justify-between items-start mb-10">
                                        <div className="w-14 h-14 rounded-3xl bg-white/[0.03] flex items-center justify-center border border-white/5 group-hover:scale-105 transition-transform">
                                            <Music2 className="w-6 h-6 text-zinc-500 group-hover:text-white transition-colors" />
                                        </div>
                                        <button className="p-2 text-zinc-600 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                                            <MoreVertical className="w-5 h-5" />
                                        </button>
                                    </div>

                                    <div className="space-y-1 mb-8">
                                        <h3 className="text-xl font-bold text-zinc-100 group-hover:text-white transition-colors truncate">
                                            {job.name || job.result_plan?.analysis?.suggestedGenre || "Untitled Session"}
                                        </h3>
                                        <p className="text-xs text-zinc-500 font-medium tracking-wide flex items-center gap-2">
                                            <Calendar className="w-3 h-3" />
                                            {new Date(job.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                        </p>
                                    </div>

                                    <div className="flex items-center justify-between pt-6 border-t border-white/5">
                                        <div className="flex items-center gap-4">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1">Status</span>
                                                <div className="flex items-center gap-2">
                                                    <div className={`w-1.5 h-1.5 rounded-full ${job.status === 'COMPLETED' ? 'bg-green-500' : job.status === 'FAILED' ? 'bg-red-500' : 'bg-primary animate-pulse'}`} />
                                                    <span className="text-[10px] font-bold text-zinc-400 capitalize">{job.status.toLowerCase()}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center scale-75 opacity-0 group-hover:opacity-100 group-hover:scale-100 transition-all shadow-xl">
                                            <Play className="w-4 h-4 fill-current ml-0.5" />
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}
            </main>
        </div>
    );
}
