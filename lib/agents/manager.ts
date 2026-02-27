import { Jobs } from "../jobs";
import { Production } from "../production";
import { claude } from "../claude";
import { AudioAnalysis, AudioAnalysisSchema, BeatDesign, BeatDesignSchema } from "./types";
import { SYSTEM_PROMPTS, USER_PROMPTS } from "./prompts";

export const AgentManager = {
    async runPipeline(jobId: string, vocalMetadata: any) {
        const updateJob = (status: string, progress: number) => {
            Jobs.update(jobId, { status: status as any, progress });
        };

        console.log("Starting AI Pipeline for session...");

        // 1. Audio Analysis Agent
        updateJob("ANALYZING", 20);
        const analysis = await claude.getStructuredOutput<AudioAnalysis>(
            USER_PROMPTS.ANALYZE_VOCAL(vocalMetadata),
            SYSTEM_PROMPTS.AUDIO_ANALYST,
            AudioAnalysisSchema
        );

        // 2. Beat Design Agent
        updateJob("DESIGNING", 50);
        const beat = await claude.getStructuredOutput<BeatDesign>(
            USER_PROMPTS.DESIGN_BEAT(analysis),
            SYSTEM_PROMPTS.BEAT_DESIGNER,
            BeatDesignSchema
        );

        const result = {
            analysis: {
                ...analysis,
                timingGrid: vocalMetadata.timingGrid,
                energyEnvelope: vocalMetadata.energyEnvelope,
                phraseMarkers: vocalMetadata.phraseMarkers,
            },
            beat,
            status: "PLANNED",
        };

        // Save the comprehensive plan to the job
        await Jobs.update(jobId, { result_plan: result });

        // 4. Production Phase
        updateJob("PRODUCING", 90);
        try {
            // Get vocal URL from job
            const job = await Jobs.get(jobId);
            if (!job?.audio_url) throw new Error("No audio URL found for job");

            await Production.trigger(jobId, job.audio_url, {
                genre: analysis.suggestedGenre,
                bpm: analysis.bpm,
                key: analysis.key,
                mood: analysis.mood
            });
        } catch (error) {
            console.error("Failed to trigger production:", error);
            updateJob("FAILED", 90);
        }

        return result;
    },
};
