import type { Subtitle } from "@/types";

type WordTiming = NonNullable<Subtitle["words"]>[number];

export function splitSubtitleTextAtTime(
  text: string,
  words: WordTiming[] | null | undefined,
  startTime: number,
  endTime: number,
  splitTime: number
) {
  const normalizedText = text.trim().replace(/\s+/g, " ");
  const alignedText = words?.map(({ word }) => word).join(" ");

  if (words?.length && alignedText === normalizedText) {
    const idx = words.findIndex((word) => word.start >= splitTime);
    const cut = idx === -1 ? words.length : idx;
    return {
      textBefore: words
        .slice(0, cut)
        .map(({ word }) => word)
        .join(" "),
      textAfter: words
        .slice(cut)
        .map(({ word }) => word)
        .join(" "),
    };
  }

  const tokens = text.split(/\s+/).filter(Boolean);
  const ratio = (splitTime - startTime) / Math.max(0.1, endTime - startTime);
  const cut = Math.max(1, Math.min(tokens.length - 1, Math.round(tokens.length * ratio)));
  return {
    textBefore: tokens.slice(0, cut).join(" "),
    textAfter: tokens.slice(cut).join(" "),
  };
}
