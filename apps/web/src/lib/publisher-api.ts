export type ToolId = "translation" | "bibliography" | "proofcheck";
export type JobStatus = "queued" | "running" | "done" | "failed";

export type Project = {
  project_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type ProjectFile = {
  file_id: string;
  project_id: string;
  original_name: string;
  stored_path: string;
  size_bytes: number;
  created_at: string;
};

export type Artifact = {
  kind: string;
  path: string;
};

export type Job = {
  job_id: string;
  tool: ToolId;
  status: JobStatus;
  project_id: string | null;
  file_id: string | null;
  input_path: string;
  output_dir: string;
  options: Record<string, unknown>;
  message: string;
  artifacts: Artifact[];
  created_at: string;
  updated_at: string;
};

async function readOrThrow(res: Response) {
  const contentType = res.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    if (typeof data === "object" && data && "error" in data) {
      throw new Error((data as { error: { message?: string } }).error?.message ?? "Request failed");
    }
    throw new Error(typeof data === "string" ? data : "Request failed");
  }
  return data;
}

export async function listProjects(): Promise<Project[]> {
  const res = await fetch("/api/publisher/projects", { cache: "no-store" });
  const data = (await readOrThrow(res)) as { projects: Project[] };
  return data.projects;
}

export async function createProject(name: string): Promise<Project> {
  const res = await fetch("/api/publisher/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return (await readOrThrow(res)) as Project;
}

export async function listProjectFiles(projectId: string): Promise<ProjectFile[]> {
  const res = await fetch(`/api/publisher/projects/${projectId}/files`, { cache: "no-store" });
  const data = (await readOrThrow(res)) as { files: ProjectFile[] };
  return data.files;
}

export async function uploadProjectFile(projectId: string, file: File): Promise<ProjectFile> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`/api/publisher/projects/${projectId}/files`, {
    method: "POST",
    body: form,
  });
  return (await readOrThrow(res)) as ProjectFile;
}

export async function startProjectJob(projectId: string, fileId: string, tool: ToolId): Promise<Job> {
  const res = await fetch(`/api/publisher/projects/${projectId}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, tool, options: {} }),
  });
  return (await readOrThrow(res)) as Job;
}

export async function listProjectJobs(projectId: string): Promise<Job[]> {
  const res = await fetch(`/api/publisher/projects/${projectId}/jobs`, { cache: "no-store" });
  const data = (await readOrThrow(res)) as { jobs: Job[] };
  return data.jobs;
}
