import { NextResponse } from "next/server";

export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const body = await request.json();

    try {
        // Proxy to Python Mastering Service
        const pythonRes = await fetch("http://localhost:8000/master", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_id: id,
                ...body
            }),
        });

        if (!pythonRes.ok) {
            const error = await pythonRes.text();
            return NextResponse.json({ error }, { status: pythonRes.status });
        }

        const data = await pythonRes.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error("Mastering proxy error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
