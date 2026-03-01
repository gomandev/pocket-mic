'use client'

import { useState } from 'react'
import { login, signup } from './actions'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'

function LoginForm() {
    const [mode, setMode] = useState<'signin' | 'signup'>('signin')
    const searchParams = useSearchParams()
    const error = searchParams.get('error')

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white px-4 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-900/20 blur-[120px] rounded-full pointer-events-none" />

            <div className="w-full max-w-sm rounded-[24px] bg-[#0a0a0a]/80 border border-white/5 shadow-2xl overflow-hidden backdrop-blur-xl z-10 p-8">
                {/* Tab Switcher */}
                <div className="flex bg-white/5 rounded-xl p-1 mb-8">
                    <button
                        type="button"
                        onClick={() => setMode('signin')}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === 'signin'
                            ? 'bg-white text-black shadow-sm'
                            : 'text-neutral-400 hover:text-white'
                            }`}
                    >
                        Sign In
                    </button>
                    <button
                        type="button"
                        onClick={() => setMode('signup')}
                        className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === 'signup'
                            ? 'bg-white text-black shadow-sm'
                            : 'text-neutral-400 hover:text-white'
                            }`}
                    >
                        Sign Up
                    </button>
                </div>

                <form className="flex-1 flex flex-col w-full gap-4 text-neutral-300">
                    <div className="mb-2 text-center">
                        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
                            {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
                        </h1>
                        <p className="text-sm text-neutral-400">
                            {mode === 'signin'
                                ? 'Sign in to your PocketMic account'
                                : 'Start your music production journey'}
                        </p>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-neutral-400" htmlFor="email">
                            Email
                        </label>
                        <input
                            className="rounded-xl px-4 py-3 bg-[#111] border border-white/10 text-white placeholder:text-neutral-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 transition-all"
                            name="email"
                            id="email"
                            type="email"
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-neutral-400" htmlFor="password">
                            Password
                        </label>
                        <input
                            className="rounded-xl px-4 py-3 bg-[#111] border border-white/10 text-white placeholder:text-neutral-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 transition-all"
                            type="password"
                            name="password"
                            id="password"
                            placeholder="••••••••"
                            minLength={6}
                            required
                        />
                    </div>

                    {error && (
                        <p className="mt-2 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center font-medium rounded-xl">
                            {error}
                        </p>
                    )}

                    <div className="mt-4">
                        <button
                            formAction={mode === 'signin' ? login : signup}
                            className="w-full bg-white text-black font-medium rounded-xl px-4 py-3 shadow-[0_4px_14px_0_rgb(255,255,255,10%)] hover:shadow-[0_6px_20px_rgba(255,255,255,20%)] hover:bg-neutral-100 transition-all active:scale-[0.98]"
                        >
                            {mode === 'signin' ? 'Sign In' : 'Create Account'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default function LoginPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center min-h-screen bg-[#050505]">
                <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
        }>
            <LoginForm />
        </Suspense>
    )
}

