import { staticFile } from 'remotion';

export async function loadAnalysis(videoPath: string) {
  try {
    if (!videoPath) return null;

    // Convert renders/scene_SC_01.mp4 -> renders/analysis/scene_SC_01_analysis.json
    const parts = videoPath.split('/');
    const filename = parts[parts.length - 1];
    const basename = filename.split('.')[0];

    const analysisPath = `renders/analysis/${basename}_analysis.json`;
    const response = await fetch(staticFile(analysisPath));

    if (!response.ok) {
        return null;
    }

    return await response.json();
  } catch (error) {
    return null;
  }
}
