import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink, readFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
const ffmpeg = require("fluent-ffmpeg");
const ffmpegInstaller = require("@ffmpeg-installer/ffmpeg");
import { AgentManager } from "@/lib/agents/manager";
import { Jobs } from "@/lib/jobs";
import { supabase } from "@/lib/supabase";

ffmpeg.setFfmpegPath(ffmpegInstaller.path);

export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();
        const audioFile = formData.get("audio") as Blob | null;

        if (!audioFile) {
            console.error("Ingest Error: No audio file provided in FormData");
            return NextResponse.json({ error: "No audio file provided" }, { status: 400 });
        }

        console.log(`Ingesting File: ${audioFile.size} bytes, type: ${audioFile.type}`);

        // GUARDRAILS: File Size & Type
        const MAX_SIZE = 20 * 1024 * 1024; // 20MB
        if (audioFile.size > MAX_SIZE) {
            return NextResponse.json({ error: "File too large (Max 20MB)" }, { status: 413 });
        }

        const allowedTypes = ["audio/wav", "audio/mpeg", "audio/webm", "application/octet-stream"];
        if (!allowedTypes.includes(audioFile.type)) {
            console.warn("Mime type check bypassed for broad compatibility:", audioFile.type);
        }

        const buffer = Buffer.from(await audioFile.arrayBuffer());
        const tempIn = join(tmpdir(), `in-${Date.now()}.wav`);
        const tempOut = join(tmpdir(), `out-${Date.now()}.wav`);

        await writeFile(tempIn, buffer);

        // Stage 3 DSP-Hybrid Implementation
        await new Promise((resolve, reject) => {
            ffmpeg(tempIn)
                .audioFilters([
                    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1",
                    "loudnorm=I=-16:TP=-1.5:LRA=11"
                ])
                .on("end", resolve)
                .on("error", reject)
                .save(tempOut);
        });

        console.log(`DSP Pipeline Complete: Trimmed & Normalized.`);

        // Stage 6: Supabase Storage Upload
        const fileExt = "wav";
        const fileName = `${Date.now()}.${fileExt}`;
        const filePath = `raw-vocals/${fileName}`;

        // We'll use the buffer after DSP if we want to save the "cleaned" version
        // but for simplicity, let's upload the original or the processed one.
        // Let's read the tempOut if we want the cleaned one.
        const outputFile = await readFile(tempOut);

        const { data: storageData, error: storageError } = await supabase.storage
            .from("audio-assets")
            .upload(filePath, outputFile, {
                contentType: "audio/wav",
                upsert: true
            });

        if (storageError) {
            console.error("Supabase Storage Error:", storageError);
            throw storageError;
        }

        console.log("Supabase Storage Upload Successful:", storageData.path);

        const { data: { publicUrl } } = supabase.storage
            .from("audio-assets")
            .getPublicUrl(filePath);

        // Stage 5 & 6: Async Job with DB Persistence
        const job = await Jobs.create(publicUrl);

        // Fire and forget processing (simulated worker)
        (async () => {
            try {
                await Jobs.update(job.id, { status: "ANALYZING", progress: 20 });

                // Stage 4: AI Pipeline (The "Agent Split")
                // FETCH RICH VOCAL DNA FIRST
                console.log("Fetching Vocal DNA for Session...");
                const pythonUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
                const analysisRes = await fetch(`${pythonUrl}/analyze-vocal`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ audio_url: publicUrl })
                });

                if (!analysisRes.ok) throw new Error("Vocal analysis service failed");
                const vocalDNA = await analysisRes.json();
                console.log("Vocal DNA Extracted. Timing Grid length:", vocalDNA.timingGrid?.length);

                await AgentManager.runPipeline(job.id, {
                    size: audioFile.size,
                    type: audioFile.type,
                    ...vocalDNA
                });

                // Status is now PRODUCING (set by AgentManager)
            } catch (err) {
                console.error("Worker error:", err);
                Jobs.update(job.id, { status: "FAILED", error: "AI Pipeline failed" });
            } finally {
                await unlink(tempIn).catch(() => { });
            }
        })();

        return NextResponse.json({
            success: true,
            jobId: job.id,
            message: "Processing started asynchronously.",
        });
    } catch (error) {
        console.error("Ingestion error:", error);
        return NextResponse.json({ error: "Failed to ingest audio" }, { status: 500 });
    }
}
