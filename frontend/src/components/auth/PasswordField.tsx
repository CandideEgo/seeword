"use client";

import { useId, useState, type ReactNode } from "react";
import { Check } from "lucide-react";
import { passwordByteLength, passwordStrength, PASSWORD_MAX_BYTES } from "@/lib/password";
import { cn } from "@/lib/utils";

const STRENGTH_LABEL = ["强度", "弱", "中", "强"] as const;
const STRENGTH_SEG = ["", "bg-error", "bg-warning", "bg-success"] as const;

const RULES: {
  key: "len" | "upper" | "lower" | "digit" | "bytes";
  label: string;
  test: (v: string) => boolean;
}[] = [
  { key: "len", label: "至少 8 位", test: (v) => v.length >= 8 },
  { key: "upper", label: "含大写字母", test: (v) => /[A-Z]/.test(v) },
  { key: "lower", label: "含小写字母", test: (v) => /[a-z]/.test(v) },
  { key: "digit", label: "含数字", test: (v) => /\d/.test(v) },
  // bcrypt only consumes 72 bytes; a longer password is rejected by both the
  // server and `isPasswordAcceptable`, so the checklist has to say so too.
  {
    key: "bytes",
    label: "不超过 72 个字节",
    test: (v) => passwordByteLength(v) <= PASSWORD_MAX_BYTES,
  },
];

interface PasswordFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  /** 右侧与标签同排的附加内容（例如「忘记密码？」链接）。 */
  labelRight?: ReactNode;
  autoComplete?: string;
  placeholder?: string;
  disabled?: boolean;
  /** 字段级错误文案：传了才标红边框并渲染错误行。 */
  error?: string;
  errorId?: string;
  /** 字段说明（设计 `.field-hint`：12px muted）。 */
  hint?: ReactNode;
  /** 3 段强度条（设计 `.pw-meter`）。 */
  showMeter?: boolean;
  /** 规则清单（设计 `.pw-rules`）：长度 / 大写 / 小写 / 数字 / 72 字节上限。 */
  showRules?: boolean;
  className?: string;
}

/**
 * 密码输入 + 「显示/隐藏」affix + 强度条 + 规则清单 + 字段级错误。
 *
 * 注册 / 设置登录密码 / 找回密码第三步共用同一份实现，保证三处口径一致
 * （设计 `auth.css` 的 `.input-affix` / `.pw-meter` / `.pw-rules` / `.field-error`）。
 * 强度第三档 ⟺ 可提交（复用 `lib/password.ts::passwordStrength`）。
 */
export function PasswordField({
  id,
  label,
  value,
  onChange,
  labelRight,
  autoComplete = "new-password",
  placeholder,
  disabled,
  error,
  errorId,
  hint,
  showMeter = false,
  showRules = false,
  className,
}: PasswordFieldProps) {
  const [show, setShow] = useState(false);
  const fallbackId = useId();
  const messageId = errorId ?? `${id}-error`;
  const strength = passwordStrength(value);

  return (
    <div className={cn("min-w-0", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="block text-copy font-medium text-ink">
          {label}
        </label>
        {labelRight}
      </div>

      <div
        className={cn(
          "mt-1.5 flex h-[46px] items-stretch overflow-hidden rounded-md border-[1.5px] bg-surface-card transition-colors focus-within:border-brand-500 focus-within:bg-canvas focus-within:ring-4 focus-within:ring-brand-500/15",
          error ? "border-error" : "border-hairline hover:border-hairline-strong"
        )}
      >
        <input
          id={id}
          name={id}
          type={show ? "text" : "password"}
          autoComplete={autoComplete}
          disabled={disabled}
          value={value}
          maxLength={128}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? messageId : hint ? `${fallbackId}-hint` : undefined}
          className="min-w-0 flex-1 bg-transparent px-3.5 text-copy text-ink outline-none placeholder:text-muted"
        />
        <button
          type="button"
          aria-label={show ? "隐藏密码" : "显示密码"}
          aria-pressed={show}
          onClick={() => setShow((v) => !v)}
          className="mr-1.5 my-1 flex-none rounded-sm px-2 text-meta font-medium text-body transition-colors hover:bg-surface-soft hover:text-ink"
        >
          {show ? "隐藏" : "显示"}
        </button>
      </div>

      {showMeter && (
        <div className="mt-2 flex items-center gap-2">
          <div
            className="flex flex-1 gap-1"
            role="img"
            aria-label={`密码强度：${STRENGTH_LABEL[strength]}`}
          >
            {[1, 2, 3].map((seg) => (
              <span
                key={seg}
                className={cn(
                  "h-1 flex-1 rounded-full transition-colors",
                  seg <= strength ? STRENGTH_SEG[strength] : "bg-surface-card"
                )}
              />
            ))}
          </div>
          <span className="min-w-8 flex-none text-caption text-muted">
            {STRENGTH_LABEL[strength]}
          </span>
        </div>
      )}

      {showRules && (
        <ul className="mt-2 flex flex-wrap gap-x-3.5 gap-y-1">
          {RULES.map((rule) => {
            const ok = rule.test(value);
            return (
              <li
                key={rule.key}
                className={cn(
                  "inline-flex items-center gap-1 whitespace-nowrap text-caption",
                  ok ? "text-body" : "text-muted"
                )}
              >
                <span aria-hidden="true" className="grid h-3.5 w-3.5 flex-none place-items-center">
                  {/* 未满足时用一个小圆点：空圆环会被读成「可点选的单选按钮」。 */}
                  {ok ? (
                    <span className="grid h-3.5 w-3.5 place-items-center rounded-full border border-success/40 bg-success-soft text-success-text">
                      <Check size={9} strokeWidth={3.2} />
                    </span>
                  ) : (
                    <span className="h-1 w-1 rounded-full bg-hairline-strong" />
                  )}
                </span>
                {rule.label}
              </li>
            );
          })}
        </ul>
      )}

      {error && (
        <p id={messageId} role="alert" className="mt-2 text-meta leading-relaxed text-error-text">
          {error}
        </p>
      )}

      {hint && (
        <p id={`${fallbackId}-hint`} className="mt-2 text-caption leading-relaxed text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
