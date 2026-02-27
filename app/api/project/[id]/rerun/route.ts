import { NextRequest, NextResponse } from "next/server";
import { Jobs } from "@/lib/jobs";

export async function POST(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        // Next.js 15: params is now async
        const { id } = await params;

        // EFFICIENCY: Rerun reuses the existing job row instead of creating new DB entries
        // It just resets status, increments version, and preserves previous results in history
        const job = await Jobs.rerun(id);

        if (!job.audio_url) {
            return NextResponse.json({ error: "No audio URL found for this job" }, { status: 400 });
        }

        // Trigger production service (with progress tracking)
        // This sends the job to the Python backend which updates progress in real-time
        const productionRes = await fetch("http://localhost:8000/process", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_id: job.id,
                audio_url: job.audio_url,
                blueprint: job.result_plan?.analysis || {
                    genre: "Alt-R&B",
                    mood: "Introspective",
                    bpm: 105,
                    key: "D minor"
                }
            })
        });

        if (!productionRes.ok) {
            throw new Error("Production service failed to start");
        }

        return NextResponse.json({ success: true, job });
    } catch (error: any) {
        console.error("Rerun Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
