import { api } from "@/lib/api";

export interface LessonCatalogItem {
  lesson_id: string;
  revision_id: string;
  title: string;
  fingerprint_version: string;
  fingerprint: string;
}

export interface LessonCatalogPage {
  items: LessonCatalogItem[];
  total: number;
  offset: number;
  limit: number;
}

export const LESSON_CATALOG_PAGE_SIZE = 20;

export function searchLessonCatalog(query: string, offset: number, signal: AbortSignal) {
  const params = new URLSearchParams({
    q: query.trim(),
    offset: String(offset),
    limit: String(LESSON_CATALOG_PAGE_SIZE),
  });
  return api<LessonCatalogPage>(`/api/v1/lessons/_search?${params}`, {
    signal,
    cache: "no-store",
  });
}
