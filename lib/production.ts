/**
 * Production Service Client
 * Calls the Python FastAPI service to trigger the audio production pipeline
 */
export const Production = {
    async trigger(jobId: string, audioUrl: string, blueprint: any) {
        console.log(`Triggering production for job ${jobId}...`);

        try {
            const response = await fetch(`${process.env.PYTHON_BACKEND_URL || "http://localhost:8000"}/process`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    job_id: jobId,
                    audio_url: audioUrl,
                    blueprint: blueprint
                }),
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Production service error: ${error}`);
            }

            const result = await response.json();
            console.log("Production queued:", result);
            return result;
        } catch (error) {
            console.error("Failed to trigger production:", error);
            throw error;
        }
    }
};
