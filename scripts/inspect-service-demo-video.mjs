#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";
import { artifactsDir, latestJsonReport, parseArgs, requireFromFrontend, runCommand, writeJson } from "./demo-video-utils.mjs";

async function inspectVideo(options = {}) {
  const outDir = path.resolve(options.outDir || artifactsDir);
  const renderReport = options.input
    ? { output: path.resolve(options.input), seed: options.seed || "manual" }
    : await latestJsonReport(path.join(outDir, "latest-render.json"));
  if (!renderReport.output) {
    throw new Error("Rendered MP4 path is missing. Run demo:render first.");
  }
  const ffprobe = requireFromFrontend("ffprobe-static");
  const ffprobePath = typeof ffprobe === "string" ? ffprobe : ffprobe.path;
  if (!ffprobePath) {
    throw new Error("ffprobe-static binary was not found.");
  }
  const probe = await runCommand(
    ffprobePath,
    ["-v", "error", "-print_format", "json", "-show_streams", "-show_format", renderReport.output],
    { cwd: outDir, timeoutMs: 60000, echo: false },
  );
  const payload = JSON.parse(probe.stdout);
  const videoStream = Array.isArray(payload.streams) ? payload.streams.find((stream) => stream.codec_type === "video") : null;
  const duration = Number(payload.format?.duration || 0);
  const minDuration = Number(options.minDuration || 5);
  const errors = [];
  if (!videoStream) {
    errors.push("video stream was not found");
  }
  if (videoStream && (!Number(videoStream.width) || !Number(videoStream.height))) {
    errors.push("video width/height is invalid");
  }
  if (!duration || duration < minDuration) {
    errors.push(`duration ${duration.toFixed(2)}s is shorter than ${minDuration}s`);
  }
  const report = {
    status: errors.length ? "failed" : "passed",
    seed: renderReport.seed,
    input: renderReport.output,
    duration_seconds: duration,
    width: Number(videoStream?.width || 0),
    height: Number(videoStream?.height || 0),
    codec: videoStream?.codec_name || "",
    errors,
    inspected_at: new Date().toISOString(),
  };
  await writeJson(path.join(outDir, "latest-inspection.json"), report);
  console.log(JSON.stringify(report, null, 2));
  if (errors.length) {
    throw new Error(errors.join("; "));
  }
  return report;
}

async function main() {
  const args = parseArgs();
  await inspectVideo({
    outDir: args["out-dir"],
    input: args.input,
    seed: args.seed,
    minDuration: args["min-duration"],
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
