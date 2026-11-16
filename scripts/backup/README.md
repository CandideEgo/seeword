# 备份与恢复

`backup.sh` 生成 DB custom dump、TOC、revision、行数、媒体/配置归档、校验和与 manifest；成功才写 SUCCESS。`restore.sh` 校验后恢复并对比 revision/行数，可选恢复媒体。它们不自动替你安装定时任务或完成异地备份。

配置和参数认两个脚本的帮助/环境变量。站外传输由 `BACKUP_OFFHOST_CMD` 配置，加密由 `BACKUP_GPG_RECIPIENT` 配置；不把凭据、数据库归档和私钥放本目录。发布前的一次性回退点另认 deploy skill。

只读归档校验仍需要可用的 pg_restore 运行环境：

```bash
bash scripts/backup/restore.sh --from /path/to/backup-run --verify-only
```

**恢复会写库。`--recreate` 删除目标库，`--force` 允许覆盖非空库。** 必须先确认目标库名、容器、归档和回退点；演练使用独立库，不能顺手填生产库。媒体、OSS、参考词典/试卷数据和镜像的备份边界不同，不能只凭 DB dump 声称整站可恢复。

RPO（最多丢多久的数据）取决于备份实际频率，RTO（恢复要多久）必须用演练计时证明。本轮未执行生产备份或恢复，也未确认宿主定时任务已安装。
