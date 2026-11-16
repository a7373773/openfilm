/**
 * What this release brings, said to the person after an update, in every language Studio speaks (a release without them
 * all does not compile), grouped as new, improved and fixed. Only this release's: the dialog tells what the version now
 * running brings, and the changelog on GitHub keeps every release's.
 *
 * Written when a release is made (the "Version packages" pull request), in place of the release before's: the
 * changesets say everything that changed, for the changelog; these say every change a person would notice, in their
 * words, one line each (at most 24). A version without them fails the tests (whats-new.test.ts), so that pull request
 * cannot be merged until they are written.
 *
 * After an update they appear once (Studio's prefs keep `seenVersion`). A new install shows none: there is nothing it
 * was updated from.
 */
import type { Language } from '@/i18n';

export type NoteKind = 'new' | 'improved' | 'fixed';
export interface ReleaseNote { kind: NoteKind; text: string }
export interface ReleaseNotes { version: string; date: string; notes: Record<Language, ReleaseNote[]> }

export const RELEASE: ReleaseNotes = {
  "version": "0.3.3",
  "date": "2026-11-16",
  "notes": {
    "en": [
      {
        "kind": "fixed",
        "text": "Recover generated images, videos and audio after interrupted downloads without paying for another generation."
      },
      {
        "kind": "fixed",
        "text": "Resume unfinished batches, stream reference uploads and download large files reliably, including filenames with spaces and multilingual characters."
      }
    ],
    "zh-CN": [
      {
        "kind": "fixed",
        "text": "图片、视频和音频下载中断后取回原结果，避免重试时重新生成扣费。"
      },
      {
        "kind": "fixed",
        "text": "批量生成从未完成的条目继续，改进大文件传输，支持空格、特殊字符和多语言文件名。"
      }
    ],
    "ja": [
      {
        "kind": "fixed",
        "text": "画像・動画・音声のダウンロードが中断しても、再生成せずに元の結果を取得できます。"
      },
      {
        "kind": "fixed",
        "text": "一括生成を未完了の項目から続行し、大容量ファイルの転送と多言語ファイル名への対応を改善しました。"
      }
    ],
    "ko": [
      {
        "kind": "fixed",
        "text": "이미지, 동영상, 오디오 다운로드가 중단되어도 다시 생성하지 않고 원래 결과를 받을 수 있습니다."
      },
      {
        "kind": "fixed",
        "text": "완료하지 못한 항목부터 일괄 생성을 계속하고 대용량 파일 전송과 다국어 파일 이름 지원을 개선했습니다."
      }
    ],
    "es": [
      {
        "kind": "fixed",
        "text": "Recupera imágenes, vídeos y audio tras una descarga interrumpida sin pagar por otra generación."
      },
      {
        "kind": "fixed",
        "text": "Continúa los lotes pendientes y transfiere archivos grandes con más fiabilidad, incluidos nombres con espacios y caracteres de otros idiomas."
      }
    ]
  }
};

/** -1, 0 or 1 as `a` is older than, the same as or newer than `b` (x.y.z; a pre-release is older than its release). */
export function compareVersions(a: string, b: string): number {
  const parse = (v: string) => {
    const at = v.indexOf('-');
    return { parts: (at < 0 ? v : v.slice(0, at)).split('.').map((n) => Number(n) || 0), pre: at < 0 ? '' : v.slice(at + 1) };
  };
  const x = parse(a), y = parse(b);
  for (let i = 0; i < 3; i++) {
    const d = (x.parts[i] ?? 0) - (y.parts[i] ?? 0);
    if (d) return Math.sign(d);
  }
  if (x.pre === y.pre) return 0;
  if (!x.pre) return 1;
  if (!y.pre) return -1;
  return Math.sign(x.pre.localeCompare(y.pre, 'en', { numeric: true }));
}

/** This release's notes when `version` is this release, else null. */
export function releaseNotes(version: string, release: ReleaseNotes = RELEASE): ReleaseNotes | null {
  return compareVersions(release.version, version) === 0 ? release : null;
}

/** Said on the window to show this release's notes again (Settings → About, Developer's preview). */
export const WHATS_NEW_EVENT = 'openfilm:whats-new';
export function showWhatsNew(): void {
  window.dispatchEvent(new CustomEvent(WHATS_NEW_EVENT));
}
