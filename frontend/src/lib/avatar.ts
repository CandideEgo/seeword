/** Shared avatar utilities — hash-based colour, gender-driven default avatar, initial extraction. */

const AVATAR_COLORS = [
  "bg-gradient-to-br from-brand-500 to-brand-400",
  "bg-gradient-to-br from-indigo-500 to-indigo-400",
  "bg-gradient-to-br from-emerald-500 to-emerald-400",
  "bg-gradient-to-br from-amber-500 to-amber-400",
  "bg-gradient-to-br from-rose-500 to-rose-400",
  "bg-gradient-to-br from-sky-500 to-sky-400",
];

/**
 * Decorative avatar hues. Palette classes are allowed only inside explicit maps
 * like this one (DEC-075 §4.3), which is why this file is on the design-system
 * gate's allowlist.
 */
export type AvatarGender = "male" | "female";

/** The genders the built-in default illustrations cover; order = the profile page's buttons. */
export const AVATAR_GENDERS: readonly AvatarGender[] = ["male", "female"];

/** Static illustrations in /public — no mediaUrl() prefix needed. */
export const DEFAULT_AVATAR_URL: Record<AvatarGender, string> = {
  male: "/default-avatar-male.webp",
  female: "/default-avatar-female.webp",
};

/**
 * Deterministic 31-multiplier string hash (unsigned 32-bit), shared by the colour
 * picker and the provisional default face so the two cannot drift apart.
 */
export function hashSeed(seed: string | null | undefined): number {
  const s = seed || "?";
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

/**
 * Pick a deterministic gradient class for a given seed string.
 * Uses a simple hash so the same user always gets the same color.
 */
export function avatarColor(seed: string | null | undefined): string {
  return AVATAR_COLORS[hashSeed(seed) % AVATAR_COLORS.length];
}

/** Deterministic decorative chip classes for a subtitle speaker name. */
/**
 * Which built-in illustration to show while the user has no upload.
 *
 * The user's gender wins: it is a field on their profile and they can change it whenever
 * they like. The hash only supplies a *provisional* face for accounts that have not filled
 * it in, so a brand-new user is not faced with an empty circle — a placeholder, dropped the
 * moment they say otherwise. It is deliberately a fallback and never an assertion: the seed
 * can decide a colour, but it must not decide a face on the user's behalf.
 */
export function defaultAvatarUrl(
  seed: string | null | undefined,
  gender?: AvatarGender | null
): string {
  const chosen: AvatarGender = gender ?? (hashSeed(seed) % 2 === 0 ? "male" : "female");
  return DEFAULT_AVATAR_URL[chosen];
}

/**
 * Extract the first character of a user's display name (or phone suffix) for an avatar.
 * Accepts either a user object with `name`/`phone` or a plain string.
 */
export function userInitial(
  user: { name?: string | null; phone?: string | null } | string | null | undefined
): string {
  if (!user) return "U";
  if (typeof user === "string") return (user[0] || "U").toUpperCase();
  return (user.name?.[0] || user.phone?.slice(-1) || "U").toUpperCase();
}
