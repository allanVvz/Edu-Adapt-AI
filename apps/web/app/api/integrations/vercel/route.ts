import { NextRequest, NextResponse } from "next/server";

const VERCEL_API = "https://api.vercel.com";

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token");
  const projectId = req.nextUrl.searchParams.get("projectId");
  const teamId = req.nextUrl.searchParams.get("teamId");

  if (!token || !projectId) {
    return NextResponse.json({ error: "token e projectId são obrigatórios" }, { status: 400 });
  }

  const teamQuery = teamId ? `?teamId=${teamId}` : "";

  const [projectRes, deployRes] = await Promise.all([
    fetch(`${VERCEL_API}/v9/projects/${projectId}${teamQuery}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
    fetch(`${VERCEL_API}/v6/deployments?projectId=${projectId}&target=production&limit=1${teamId ? `&teamId=${teamId}` : ""}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  ]);

  if (!projectRes.ok) {
    const err = await projectRes.json().catch(() => ({}));
    return NextResponse.json({ error: err.error?.message || "Projeto não encontrado" }, { status: projectRes.status });
  }

  const project = await projectRes.json();
  const deployData = deployRes.ok ? await deployRes.json() : { deployments: [] };
  const latest = deployData.deployments?.[0];

  return NextResponse.json({
    name: project.name,
    productionUrl: project.targets?.production?.alias?.[0]
      ? `https://${project.targets.production.alias[0]}`
      : latest?.url ? `https://${latest.url}` : null,
    latestDeployment: latest
      ? {
          id: latest.uid,
          state: latest.state,
          createdAt: latest.createdAt,
          url: `https://${latest.url}`,
        }
      : null,
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { token, deployHookUrl, projectId, teamId } = body;

  if (!token) {
    return NextResponse.json({ error: "token é obrigatório" }, { status: 400 });
  }

  if (deployHookUrl) {
    const res = await fetch(deployHookUrl, { method: "POST" });
    if (!res.ok) {
      return NextResponse.json({ error: "Falha ao chamar deploy hook" }, { status: 502 });
    }
    const data = await res.json().catch(() => ({}));
    return NextResponse.json({ triggered: true, job: data.job });
  }

  if (!projectId) {
    return NextResponse.json({ error: "deployHookUrl ou projectId é obrigatório" }, { status: 400 });
  }

  const teamQuery = teamId ? `?teamId=${teamId}` : "";
  const latestRes = await fetch(
    `${VERCEL_API}/v6/deployments?projectId=${projectId}&target=production&limit=1${teamId ? `&teamId=${teamId}` : ""}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  if (!latestRes.ok) {
    return NextResponse.json({ error: "Não foi possível obter o último deploy" }, { status: 502 });
  }

  const { deployments } = await latestRes.json();
  const latest = deployments?.[0];
  if (!latest) {
    return NextResponse.json({ error: "Nenhum deploy encontrado para redeploy" }, { status: 404 });
  }

  const redeployRes = await fetch(`${VERCEL_API}/v13/deployments${teamQuery}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ deploymentId: latest.uid, name: latest.name, target: "production" }),
  });

  const redeployData = await redeployRes.json();
  if (!redeployRes.ok) {
    return NextResponse.json({ error: redeployData.error?.message || "Falha no redeploy" }, { status: redeployRes.status });
  }

  return NextResponse.json({
    triggered: true,
    deploymentId: redeployData.id,
    url: redeployData.url ? `https://${redeployData.url}` : null,
  });
}
