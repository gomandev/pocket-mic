import { Logo } from "@/components/ui/Logo";
import AudioRecorder from "@/components/audio/AudioRecorder";
import { Clock, Menu, LogIn } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center overflow-hidden">
      {/* Dynamic Ambient Background Elements */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden flex items-center justify-center">
        {/* Neon Cyan Glow */}
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/15 blur-[150px] rounded-full animate-pulse-slow mix-blend-screen" />
        {/* Electric Purple Glow */}
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-secondary/15 blur-[150px] rounded-full animate-float mix-blend-screen" />
      </div>

      {/* Top Navigation */}
      <nav className="w-full max-w-7xl flex items-center justify-between p-6 sm:p-8 relative z-50">
        <Logo />

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-zinc-400">
          <a href="/projects" className="text-primary font-bold hover:text-white transition-colors flex items-center gap-2">
            <Clock className="w-4 h-4" /> Studio Hub
          </a>
          <a href="#" className="hover:text-white transition-colors">How it works</a>
          <a href="#" className="hover:text-white transition-colors">Pricing</a>
          <a href="/login" className="px-6 py-2.5 rounded-full bg-white text-black font-bold hover:bg-zinc-200 transition-all text-sm flex items-center gap-2">
            <LogIn className="w-4 h-4" /> Sign In
          </a>
        </div>

        {/* Mobile Nav */}
        <div className="flex md:hidden items-center gap-4">
          <a href="/projects" className="p-2 rounded-full bg-white/5 border border-white/10 text-primary">
            <Clock className="w-5 h-5" />
          </a>
          <button className="p-2 text-zinc-400 hover:text-white">
            <Menu className="w-6 h-6" />
          </button>
        </div>
      </nav>

      <div className="flex-1 flex flex-col items-center justify-center w-full max-w-4xl px-4 sm:px-6 relative z-10 pb-20 sm:pb-24">
        {/* Workspace Container */}
        <section className="w-full space-y-16 mt-8 sm:mt-0">
          <AudioRecorder />
        </section>

        {/* Branding Detail */}
        <div className="absolute bottom-8 sm:bottom-12 flex flex-col items-center space-y-4 opacity-70">
          <div className="h-px w-24 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.3em] flex items-center gap-2">
            <span>Crafted for creators</span> <span className="w-1 h-1 rounded-full bg-primary/50" /> <span>Session workspace</span>
          </p>
        </div>
      </div>
    </main>
  );
}
