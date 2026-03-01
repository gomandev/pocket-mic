import { z } from "zod";

export const AudioAnalysisSchema = z.object({
    bpm: z.number().min(60).max(200),
    key: z.string(),
    mood: z.string(),
    energy: z.number().min(0).max(1),
    suggestedGenre: z.string(),
});

export type AudioAnalysis = z.infer<typeof AudioAnalysisSchema>;

export const BeatDesignSchema = z.object({
    kit: z.enum(["Classic", "Drill", "Lofi", "Techno"]),
    pattern: z.string().optional(),
    intensity: z.number().min(0).max(1),
    // Lyria RealTime parameters
    primary_prompt: z.string().optional(),
    density_mode: z.enum(["inverse", "constant", "follow"]).optional().default("inverse"),
    section_prompts: z.array(z.object({
        label: z.string(),
        prompt: z.string(),
    })).optional(),
});

export type BeatDesign = z.infer<typeof BeatDesignSchema>;

export const ArrangementSchema = z.object({
    structure: z.array(z.string()),
    dynamicCurve: z.array(z.number()),
    mixNotes: z.string(),
});

export type Arrangement = z.infer<typeof ArrangementSchema>;
