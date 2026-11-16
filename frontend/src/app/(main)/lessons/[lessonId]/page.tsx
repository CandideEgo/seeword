import { LessonReader } from "@/components/lessons/LessonReader";

type Query = Record<string, string | string[] | undefined>;

export default async function LessonPage({
  params,
  searchParams,
}: {
  params: Promise<{ lessonId: string }>;
  searchParams: Promise<Query>;
}) {
  const [{ lessonId }, query] = await Promise.all([params, searchParams]);
  const revision = typeof query.revision === "string" ? query.revision : null;
  const conversationId = typeof query.conversation === "string" ? query.conversation : null;
  const segmentId = typeof query.segment === "string" ? query.segment : null;
  const tokens = typeof query.token === "string" ? [query.token] : (query.token ?? []);
  const anchor = segmentId ? { segment_id: segmentId, token_ids: tokens } : null;
  return (
    <LessonReader
      key={JSON.stringify([lessonId, revision, anchor])}
      lessonId={lessonId}
      revision={revision}
      anchor={anchor}
      conversationId={conversationId}
    />
  );
}
