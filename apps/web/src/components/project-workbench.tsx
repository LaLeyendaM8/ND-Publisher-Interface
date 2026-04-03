"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  Job,
  Project,
  ProjectFile,
  ToolId,
  createProject,
  listProjectFiles,
  listProjectJobs,
  listProjects,
  startProjectJob,
  uploadProjectFile,
} from "@/lib/publisher-api";

const tools: ToolId[] = ["translation", "bibliography", "proofcheck"];

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("de-DE");
}

function statusClass(status: Job["status"]) {
  if (status === "done") return "nd-status nd-status-done";
  if (status === "failed") return "nd-status nd-status-failed";
  if (status === "running") return "nd-status nd-status-running";
  return "nd-status nd-status-queued";
}

export function ProjectWorkbench() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [projectFiles, setProjectFiles] = useState<ProjectFile[]>([]);
  const [projectJobs, setProjectJobs] = useState<Job[]>([]);
  const [newProjectName, setNewProjectName] = useState("");
  const [selectedTool, setSelectedTool] = useState<ToolId>("proofcheck");
  const [selectedFileId, setSelectedFileId] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState("Bereit.");

  const refreshProjects = useCallback(async () => {
    const data = await listProjects();
    setProjects(data);
    if (!selectedProjectId && data.length > 0) {
      setSelectedProjectId(data[0].project_id);
    }
  }, [selectedProjectId]);

  const refreshProjectData = useCallback(async (projectId: string) => {
    const [files, jobs] = await Promise.all([listProjectFiles(projectId), listProjectJobs(projectId)]);
    setProjectFiles(files);
    setProjectJobs(jobs);
    if (!selectedFileId && files.length > 0) {
      setSelectedFileId(files[0].file_id);
    }
  }, [selectedFileId]);

  useEffect(() => {
    void refreshProjects().catch((err: Error) => setMessage(err.message));
  }, [refreshProjects]);

  useEffect(() => {
    if (!selectedProjectId) {
      setProjectFiles([]);
      setProjectJobs([]);
      return;
    }
    void refreshProjectData(selectedProjectId).catch((err: Error) => setMessage(err.message));
  }, [refreshProjectData, selectedProjectId]);

  async function onCreateProject(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setIsBusy(true);
    try {
      const project = await createProject(newProjectName.trim());
      setNewProjectName("");
      setMessage(`Projekt erstellt: ${project.name}`);
      await refreshProjects();
      setSelectedProjectId(project.project_id);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Projekt konnte nicht erstellt werden.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onUploadFile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedProjectId) return;
    const input = document.getElementById("upload-file-input") as HTMLInputElement | null;
    const file = input?.files?.[0];
    if (!file) return;
    setIsBusy(true);
    try {
      const uploaded = await uploadProjectFile(selectedProjectId, file);
      setMessage(`Datei hochgeladen: ${uploaded.original_name}`);
      await refreshProjectData(selectedProjectId);
      setSelectedFileId(uploaded.file_id);
      if (input) input.value = "";
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload fehlgeschlagen.");
    } finally {
      setIsBusy(false);
    }
  }

  async function onStartJob(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedProjectId || !selectedFileId) return;
    setIsBusy(true);
    try {
      const job = await startProjectJob(selectedProjectId, selectedFileId, selectedTool);
      setMessage(`Job gestartet (${job.tool}): ${job.job_id}`);
      await refreshProjectData(selectedProjectId);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Job konnte nicht gestartet werden.");
    } finally {
      setIsBusy(false);
    }
  }

  const selectedProject = projects.find((p) => p.project_id === selectedProjectId) ?? null;

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <section className="nd-card rounded-2xl p-5 xl:col-span-4">
        <h2 className="serif-heading text-3xl">Projekte</h2>
        <form className="mt-4 space-y-3" onSubmit={onCreateProject}>
          <input
            className="nd-input"
            placeholder="Neues Projekt"
            value={newProjectName}
            onChange={(event) => setNewProjectName(event.target.value)}
          />
          <button className="nd-button w-full" disabled={isBusy} type="submit">
            Projekt anlegen
          </button>
        </form>

        <div className="mt-5 max-h-[420px] space-y-2 overflow-auto pr-1">
          {projects.map((project) => (
            <button
              key={project.project_id}
              onClick={() => setSelectedProjectId(project.project_id)}
              className={`w-full rounded-xl border px-3 py-2 text-left transition ${
                selectedProjectId === project.project_id
                  ? "border-[var(--color-accent)] bg-[var(--color-surface)]"
                  : "border-[var(--color-border)] bg-[var(--color-background)]"
              }`}
              type="button"
            >
              <div className="font-medium">{project.name}</div>
              <div className="text-xs text-[var(--color-text-secondary)]">{formatDate(project.created_at)}</div>
            </button>
          ))}
        </div>
      </section>

      <section className="nd-card rounded-2xl p-5 xl:col-span-8">
        <h2 className="serif-heading text-3xl">{selectedProject ? selectedProject.name : "Projekt waehlen"}</h2>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{message}</p>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <form className="space-y-3" onSubmit={onUploadFile}>
            <h3 className="font-semibold">Datei hochladen</h3>
            <input className="nd-input" id="upload-file-input" type="file" />
            <button className="nd-button w-full" disabled={isBusy || !selectedProjectId} type="submit">
              Upload starten
            </button>
          </form>

          <form className="space-y-3" onSubmit={onStartJob}>
            <h3 className="font-semibold">Tool Job starten</h3>
            <select
              className="nd-input"
              value={selectedTool}
              onChange={(event) => setSelectedTool(event.target.value as ToolId)}
            >
              {tools.map((tool) => (
                <option key={tool} value={tool}>
                  {tool}
                </option>
              ))}
            </select>
            <select
              className="nd-input"
              value={selectedFileId}
              onChange={(event) => setSelectedFileId(event.target.value)}
            >
              <option value="">Datei waehlen</option>
              {projectFiles.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.original_name}
                </option>
              ))}
            </select>
            <button className="nd-button w-full" disabled={isBusy || !selectedFileId} type="submit">
              Job starten
            </button>
          </form>
        </div>

        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <div>
            <h3 className="font-semibold">Dateien</h3>
            <div className="mt-3 max-h-[300px] space-y-2 overflow-auto pr-1">
              {projectFiles.map((file) => (
                <a
                  key={file.file_id}
                  className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm"
                  href={`/api/publisher/projects/${file.project_id}/files/${file.file_id}/download`}
                >
                  <div className="font-medium">{file.original_name}</div>
                  <div className="text-xs text-[var(--color-text-secondary)]">
                    {Math.round(file.size_bytes / 1024)} KB - {formatDate(file.created_at)}
                  </div>
                </a>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold">Jobs</h3>
            <div className="mt-3 max-h-[300px] space-y-2 overflow-auto pr-1">
              {projectJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium">{job.tool}</span>
                    <span className={statusClass(job.status)}>{job.status}</span>
                  </div>
                  <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{job.message || "..."}</p>
                  {job.artifacts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {job.artifacts.map((artifact, idx) => (
                        <a
                          key={`${job.job_id}-${idx}`}
                          className="rounded-full border border-[var(--color-border)] px-2 py-1 text-xs"
                          href={`/api/publisher/projects/${job.project_id}/jobs/${job.job_id}/artifacts/${idx}`}
                        >
                          {artifact.kind}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
