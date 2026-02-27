import { supabase } from "./supabase";

export type JobStatus = "QUEUED" | "ANALYZING" | "DESIGNING" | "ARRANGING" | "PRODUCING" | "COMPLETED" | "FAILED";

export interface Job {
    id: string;
    status: JobStatus;
    progress: number;
    audio_url?: string;
    processed_audio_url?: string;
    result_plan?: any;
    error?: string;
    name?: string;
    version?: number;
    created_at: string;
    updated_at?: string;
}

export const Jobs = {
    async create(audioUrl?: string, name?: string): Promise<Job> {
        const defaultName = name || `Studio Session ${new Date().toLocaleDateString()}`;
        const { data, error } = await supabase
            .from("jobs")
            .insert([{
                status: "QUEUED",
                progress: 0,
                audio_url: audioUrl,
                name: defaultName,
                version: 1
            }])
            .select()
            .single();

        if (error) throw error;
        return data as Job;
    },

    async get(id: string): Promise<Job | null> {
        const { data, error } = await supabase
            .from("jobs")
            .select("*")
            .eq("id", id)
            .single();

        if (error) return null;
        return data as Job;
    },

    async list(): Promise<Job[]> {
        const { data, error } = await supabase
            .from("jobs")
            .select("*")
            .order("created_at", { ascending: false });

        if (error) throw error;
        return data as Job[];
    },

    async update(id: string, updates: Partial<Job>) {
        const { data, error } = await supabase
            .from("jobs")
            .update({
                ...updates,
                updated_at: new Date().toISOString(),
            })
            .eq("id", id)
            .select()
            .single();

        if (error) throw error;
        return data as Job;
    },

    async rerun(id: string) {
        const job = await this.get(id);
        if (!job) throw new Error("Job not found");

        // Preserve previous result in version history
        const previousVersion = job.version || 1;
        const versionHistory = job.result_plan?.version_history || [];

        if (job.result_plan) {
            // Clone result_plan but EXCLUDE version_history to prevent circular reference
            const { version_history, ...cleanResultPlan } = job.result_plan;

            versionHistory.push({
                version: previousVersion,
                timestamp: new Date().toISOString(),
                result_plan: cleanResultPlan,  // Store without nested version_history
                status: job.status
            });
        }

        const { data, error } = await supabase
            .from("jobs")
            .update({
                status: "QUEUED",
                progress: 0,
                version: previousVersion + 1,
                updated_at: new Date().toISOString(),
                error: null,
                result_plan: {
                    version_history: versionHistory  // Preserve all previous versions
                }
            })
            .eq("id", id)
            .select()
            .single();

        if (error) throw error;
        return data as Job;
    },

    async master(id: string, style: string, punch: number, width: number): Promise<any> {
        const res = await fetch(`/api/jobs/${id}/master`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style, punch, width })
        });
        if (!res.ok) {
            const error = await res.text();
            throw new Error(error || 'Mastering request failed');
        }
        return res.json();
    }
};
