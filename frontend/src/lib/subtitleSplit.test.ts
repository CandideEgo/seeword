import { describe, expect, it } from "vitest";
import { splitSubtitleTextAtTime } from "./subtitleSplit";

describe("splitSubtitleTextAtTime", () => {
  it("uses current text when word timestamps belong to older text", () => {
    const result = splitSubtitleTextAtTime(
      "We like corrected words",
      [
        { word: "We", start: 0, end: 0.4 },
        { word: "liked", start: 0.5, end: 1 },
        { word: "old", start: 1.1, end: 1.5 },
        { word: "words", start: 1.6, end: 2 },
      ],
      0,
      4,
      2
    );

    expect(result).toEqual({ textBefore: "We like", textAfter: "corrected words" });
  });

  it("uses word boundaries when timestamps match current text", () => {
    const result = splitSubtitleTextAtTime(
      "hello there friend",
      [
        { word: "hello", start: 0, end: 1 },
        { word: "there", start: 1.5, end: 2 },
        { word: "friend", start: 2.5, end: 3.5 },
      ],
      0,
      4,
      2.2
    );

    expect(result).toEqual({ textBefore: "hello there", textAfter: "friend" });
  });
});
