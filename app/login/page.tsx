import { login, signup } from './actions'

type Props = {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function LoginPage(props: Props) {
    const searchParams = await props.searchParams;
    const error = searchParams?.error as string | undefined;

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white px-4 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-900/20 blur-[120px] rounded-full pointer-events-none" />

            <div className="w-full max-w-sm rounded-[24px] bg-[#0a0a0a]/80 border border-white/5 shadow-2xl overflow-hidden backdrop-blur-xl z-10 p-8">
                <form className="flex-1 flex flex-col w-full gap-4 text-neutral-300">
                    <div className="mb-6 text-center">
                        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome Back</h1>
                        <p className="text-sm text-neutral-400">Sign in to your PocketMic account</p>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-neutral-400" htmlFor="email">
                            Email
                        </label>
                        <input
                            className="rounded-xl px-4 py-3 bg-[#111] border border-white/10 text-white placeholder:text-neutral-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 transition-all"
                            name="email"
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
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && (
                        <p className="mt-2 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center font-medium rounded-xl">
                            {error}
                        </p>
                    )}

                    <div className="flex flex-col gap-3 mt-4">
                        <button
                            formAction={login}
                            className="w-full bg-white text-black font-medium rounded-xl px-4 py-3 shadow-[0_4px_14px_0_rgb(255,255,255,10%)] hover:shadow-[0_6px_20px_rgba(255,255,255,20%)] hover:bg-neutral-100 transition-all active:scale-[0.98]"
                        >
                            Sign In
                        </button>
                        <button
                            formAction={signup}
                            className="w-full bg-transparent text-neutral-300 font-medium rounded-xl px-4 py-3 border border-white/10 hover:bg-white/5 hover:text-white transition-all active:scale-[0.98]"
                        >
                            Sign Up
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
