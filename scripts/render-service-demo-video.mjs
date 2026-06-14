#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";
import { artifactsDir, ensureDir, latestJsonReport, parseArgs, requireFromFrontend, runCommand, writeJson } from "./demo-video-utils.mjs";

async function renderVideo(options = {}) {
  const outDir = path.resolve(options.outDir || artifactsDir);
  const report = options.input
    ? { raw_video_path: path.resolve(options.input), seed: options.seed || "manual", run_dir: path.dirname(path.resolve(options.input)) }
    : await latestJsonReport(path.join(outDir, "latest-report.json"));
  if (!report.raw_video_path) {
    throw new Error("Raw WebM video path is missing. Run demo:record without --dry-run first.");
  }
  const ffmpegPath = requireFromFrontend("ffmpeg-static");
  if (!ffmpegPath) {
    throw new Error("ffmpeg-static binary was not found.");
  }
  const outputPath = path.resolve(options.output || path.join(outDir, `service-demo-${report.seed}.mp4`));
  await ensureDir(path.dirname(outputPath));
  await runCommand(
    ffmpegPath,
    [
      "-y",
      "-i",
      report.raw_video_path,
      "-movflags",
      "+faststart",
      "-pix_fmt",
      "yuv420p",
      "-vcodec",
      "libx264",
      "-crf",
      String(options.crf || 23),
      outputPath,
    ],
    { cwd: outDir, timeoutMs: 180000 },
  );
  const renderReport = {
    status: "completed",
    seed: report.seed,
    input: report.raw_video_path,
    output: outputPath,
    created_at: new Date().toISOString(),
  };
  await writeJson(path.join(outDir, "latest-render.json"), renderReport);
  if (report.run_dir) {
    await writeJson(path.join(report.run_dir, "render-report.json"), renderReport);
  }
  console.log(JSON.stringify(renderReport, null, 2));
  return renderReport;
}

async function main() {
  const args = parseArgs();
  await renderVideo({
    outDir: args["out-dir"],
    input: args.input,
    output: args.output,
    seed: args.seed,
    crf: args.crf,
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
