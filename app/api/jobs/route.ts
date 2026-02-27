import { NextResponse } from "next/server";
import { Jobs } from "@/lib/jobs";

export async function GET() {
    try {
        const data = await Jobs.list();
        return NextResponse.json(data);
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
