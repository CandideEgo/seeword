"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";
import { Camera, Phone } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Avatar } from "@/components/ui/Avatar";
import { Modal } from "@/components/common/Modal";
import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/errors";
import { AVATAR_GENDERS, type AvatarGender } from "@/lib/avatar";
import { cn } from "@/lib/utils";
import { useSmsCode } from "@/hooks/useSmsCode";
import type { User } from "@/types";
import { Card } from "@/components/ui/Card";

interface ProfileTabProps {
  user: User;
  onUpdate: (user: User) => void;
}

/**
 * 个人资料（1B 设计减法后）：只保留头像/昵称/手机号三个核心项。
 * 简介、英语等级、注册时间已下线（无展示场景/与偏好难度重复/头部已有「加入 N 天」）；
 * 换绑手机是年度级低频动作，收进弹窗，不再占据资料页主视觉。
 */
export default function ProfileTab({ user, onUpdate }: ProfileTabProps) {
  const [name, setName] = useState(user.name || "");
  const [saving, setSaving] = useState(false);

  // Avatar upload
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  // The user's gender decides the built-in default face (see DEC-048).
  const [savingGender, setSavingGender] = useState(false);

  // Change phone (modal)
  const [showChangePhone, setShowChangePhone] = useState(false);
  const [newPhone, setNewPhone] = useState("");
  const [changePhoneCode, setChangePhoneCode] = useState("");
  const [changePhonePassword, setChangePhonePassword] = useState("");
  const [changingPhone, setChangingPhone] = useState(false);
  const { cooldown, sending, sendCode, error: smsError } = useSmsCode(newPhone);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await api<User>("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({ name: name || null }),
      });
      onUpdate(updated);
      toast.success("资料已保存");
    } catch {
      toast.error("保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleGenderChange(next: AvatarGender) {
    if (user.gender === next || savingGender) return;
    setSavingGender(true);
    try {
      const updated = await api<User>("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({ gender: next }),
      });
      onUpdate(updated);
    } catch (err) {
      toast.error(apiErrorMessage(err, "性别保存失败"));
    } finally {
      setSavingGender(false);
    }
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const updated = await api<User>("/api/v1/users/me/avatar", {
        method: "POST",
        body: form,
      });
      onUpdate(updated);
      toast.success("头像已更新");
    } catch (err) {
      toast.error(apiErrorMessage(err, "头像上传失败"));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function closeChangePhone() {
    setShowChangePhone(false);
    setNewPhone("");
    setChangePhoneCode("");
    setChangePhonePassword("");
  }

  async function handleChangePhone(e: React.FormEvent) {
    e.preventDefault();
    setChangingPhone(true);
    try {
      const updated = await api<User>("/api/v1/auth/sms/change-phone", {
        method: "POST",
        body: JSON.stringify({
          new_phone: newPhone,
          code: changePhoneCode,
          password: changePhonePassword,
        }),
      });
      onUpdate(updated);
      closeChangePhone();
      toast.success("手机号已更换");
    } catch (err) {
      toast.error(apiErrorMessage(err, "更换手机号失败"));
    } finally {
      setChangingPhone(false);
    }
  }

  // 说明如实：默认头像跟着性别走，上传的头像优先；没填性别时展示的那张是临时指派的。
  let genderHint = "你还没填性别，当前展示的那张是系统临时指派的；填上就会换成对应的。";
  if (user.avatar_url) {
    genderHint = "上传的头像优先；未上传时展示对应性别的默认插画。";
  } else if (user.gender) {
    genderHint = "当前展示的就是这个性别的默认插画；上传自己的图则以你的图为准。";
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Avatar */}
      <Card padding={5}>
        <label className="block text-copy font-semibold text-ink mb-3">头像</label>
        <div className="flex items-center gap-4">
          <Avatar
            src={user.avatar_url}
            name={user}
            seed={user.id}
            gender={user.gender}
            size="xl"
            alt={user.name ?? "头像"}
            className="w-20 h-20 text-display-sm border border-hairline"
          />
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handleAvatarChange}
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              icon={Camera}
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? "上传中..." : "上传头像"}
            </Button>
            <p className="mt-1.5 text-meta text-muted">支持 JPG/PNG/WebP/GIF，最大 5MB</p>
          </div>
        </div>

        {/* 默认头像跟随用户的性别。此前按用户 id 哈希指派男女，约一半用户被永久
            分配异性插画且无纠正途径——改为在资料里填性别，插画跟着变（DEC-048）。 */}
        <div className="mt-4 pt-4 border-t border-hairline">
          <span className="block text-copy font-semibold text-ink mb-2">性别</span>
          <div className="flex gap-2" role="group" aria-label="性别">
            {AVATAR_GENDERS.map((p) => (
              <button
                key={p}
                type="button"
                aria-pressed={user.gender === p}
                disabled={savingGender}
                onClick={() => handleGenderChange(p)}
                className={cn(
                  "rounded-pill border px-3.5 py-1.5 text-copy transition-colors disabled:opacity-60",
                  user.gender === p
                    ? "border-brand-500 bg-brand-50 text-brand-700 font-semibold"
                    : "border-hairline text-body hover:border-brand-300"
                )}
              >
                {p === "male" ? "男生" : "女生"}
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-meta text-muted">{genderHint}</p>
        </div>
      </Card>

      {/* Name + phone */}
      <Card padding={5} className="space-y-4">
        <div>
          <label className="block text-copy font-semibold text-ink mb-2">昵称</label>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="你的昵称"
            maxLength={100}
            className="w-full"
          />
        </div>

        <div className="flex items-center justify-between border-t border-hairline pt-4">
          <div>
            <p className="text-copy font-semibold text-ink">手机号</p>
            <p className="text-copy text-muted mt-0.5 flex items-center gap-1.5">
              <Phone size={13} />
              {user.phone ? user.phone.replace(/^(\d{3})\d{4}(\d{4})$/, "$1****$2") : "未绑定"}
            </p>
          </div>
          <Button type="button" variant="text" size="sm" onClick={() => setShowChangePhone(true)}>
            更换
          </Button>
        </div>
      </Card>

      <div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "保存中..." : "保存修改"}
        </Button>
      </div>

      {/* Change phone modal — low-frequency heavy flow, kept off the main page */}
      <Modal
        open={showChangePhone}
        onClose={() => !changingPhone && closeChangePhone()}
        title="更换手机号"
        footer={
          <>
            <Button variant="outline" onClick={closeChangePhone} disabled={changingPhone}>
              取消
            </Button>
            <Button type="submit" form="change-phone-form" disabled={changingPhone}>
              {changingPhone ? "更换中..." : "确认更换"}
            </Button>
          </>
        }
      >
        <form id="change-phone-form" onSubmit={handleChangePhone} className="space-y-3">
          <Input
            type="tel"
            inputMode="numeric"
            maxLength={11}
            value={newPhone}
            onChange={(e) => setNewPhone(e.target.value.replace(/\D/g, ""))}
            placeholder="新手机号"
            required
            className="w-full"
          />
          <div className="flex gap-2">
            <Input
              inputMode="numeric"
              maxLength={6}
              value={changePhoneCode}
              onChange={(e) => setChangePhoneCode(e.target.value.replace(/\D/g, ""))}
              placeholder="验证码"
              required
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              disabled={sending || cooldown > 0 || newPhone.length !== 11}
              onClick={() => sendCode("change_phone")}
              className="shrink-0"
            >
              {cooldown > 0 ? `${cooldown}s` : sending ? "发送中..." : "获取验证码"}
            </Button>
          </div>
          <Input
            type="password"
            value={changePhonePassword}
            onChange={(e) => setChangePhonePassword(e.target.value)}
            placeholder="当前密码（用于验证身份）"
            required
            className="w-full"
          />
          {smsError && <p className="text-copy text-error-text">{smsError}</p>}
        </form>
      </Modal>
    </div>
  );
}
