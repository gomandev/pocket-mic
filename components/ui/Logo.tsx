"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function Logo({ className = "" }: { className?: string }) {
    return (
        <Link href="/" className={`flex items-center gap-3 group ${className}`}>
            <div className="relative w-10 h-10 flex items-center justify-center">
                <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full group-hover:bg-primary/30 transition-colors" />
                <svg
                    viewBox="0 0 40 40"
                    className="w-full h-full text-white relative z-10 group-hover:scale-110 transition-transform"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    {/* Microphone Body / Capsule */}
                    <rect x="14" y="8" width="12" height="18" rx="6" fill="currentColor" />
                    {/* Signal Pulse */}
                    <motion.path
                        d="M8 20H14L17 14L23 26L26 20H32"
                        stroke="black"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{ duration: 1.5, repeat: Infinity, repeatDelay: 1 }}
                    />
                    {/* Base */}
                    <path
                        d="M16 28V32M24 28V32M12 32H28"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                    />
                </svg>
            </div>
            <span className="text-xl font-bold tracking-tight text-white uppercase tracking-[0.1em] group-hover:text-primary transition-colors">
                PocketMic
            </span>
        </Link>
    );
}
