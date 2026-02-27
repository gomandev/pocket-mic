import { NextRequest, NextResponse } from "next/server";
import { Jobs } from "@/lib/jobs";

export async function GET(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const job = await Jobs.get(id);

    if (!job) {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    return NextResponse.json(job);
}

export async function PATCH(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const body = await req.json();

    const job = await Jobs.get(id);
    if (!job) {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Update job with provided fields
    await Jobs.update(id, body);
    const updatedJob = await Jobs.get(id);

    return NextResponse.json(updatedJob);
}
