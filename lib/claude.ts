import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

export const claude = {
    async getCompletion(prompt: string, systemPrompt?: string) {
        try {
            const payload = {
                model: "claude-sonnet-4-5",
                max_tokens: 4096,
                system: systemPrompt,
                messages: [
                    {
                        role: "user",
                        content: prompt
                    }
                ],
            };
            const response = await anthropic.messages.create(payload as any);

            const firstContent = response.content[0];
            if (firstContent.type === "text") {
                return firstContent.text;
            }
            return null;
        } catch (error) {
            console.error("Claude API Error:", error);
            throw error;
        }
    },

    async getStructuredOutput<T>(prompt: string, systemPrompt: string, schema: any): Promise<T> {
        const formattedPrompt = `${prompt}\n\nYou MUST return only valid JSON that matches this schema: ${JSON.stringify(
            schema
        )}`;

        const result = await this.getCompletion(formattedPrompt, systemPrompt);
        if (!result) throw new Error("No response from Claude");

        try {
            // Find JSON block if it's wrapped in markdown
            const jsonMatch = result.match(/\{[\s\S]*\}/);
            const jsonStr = jsonMatch ? jsonMatch[0] : result;
            return JSON.parse(jsonStr) as T;
        } catch (error) {
            console.error("Failed to parse Claude JSON output:", result);
            throw new Error("Invalid structured output from Claude");
        }
    },
};
