# Session 03 作业：加密 NotesApp 评论列

## 目标与课件依据

截图对应课件第 30 页的第 3 项作业：使用 AES-GCM 加密 `notes.comment`。
第 24 页说明 GCM 同时提供机密性与完整性；第 25 页要求每次加密使用新的
12 字节 nonce；第 27 页强调密钥不能硬编码在源码中或与数据库一起保存。

## 已完成的实现

| 部分 | 实现 |
| --- | --- |
| 算法 | 调用 `cryptography` 库的 `AESGCM`，使用 256 位独立随机密钥 |
| 每次写入 | 新增和修改评论时，先加密再写入数据库；每次调用 `os.urandom(12)` |
| 存储格式 | `aesgcm:v1:` + Base64(nonce + ciphertext + 16 字节认证标签) |
| 密钥 | 从 `COMMENT_ENCRYPTION_KEY` 环境变量读取，本机保存在 Git 忽略的 `.env` |
| 读取 | 学生页面、教师页面、JSON API 和 CSV 导出在服务端解密 |
| 完整性校验 | 密钥错误、密文/nonce/标签被修改时拒绝解密，返回通用错误 |
| 旧数据 | 容器启动前在同一事务中迁移旧评论；重复执行不会二次加密 |
| 异常保护 | 迁移遇到损坏密文或错误密钥时整体回滚；不会回退为明文读取 |
| 空值 | SQL NULL 保持 NULL，空字符串正常加密 |

核心代码位于 `web/comment_crypto.py`，读写接入位于 `web/app.py`，
旧数据迁移位于 `web/migrate_comments.py`。

密钥与现有 CSV 签名使用的 `EXPORT_HMAC_KEY` 分开生成。AAD（额外认证数据）
固定为 `notesapp:notes.comment:v1`，用于认证版本与字段用途。

## 实际验证结果

2026-10-27 已在本机完成以下验证：

- 15 项自动测试全部通过，覆盖加解密、中文与表情、空值、nonce、密文格式、
  错误密钥、篡改检测、迁移回滚、重复迁移，以及所有评论读写入口。
- 原有 60 条评论全部迁移为密文，成绩与评论内容保留。
- 迁移前的完整记录与迁移后解密的完整记录，其 SHA-256 摘要完全一致：

  ```text
  170e2e5b2d4d0112771cec0bb1a3cd8006a501d0b88fc834203afe1e7b00f024
  ```

- 重复运行迁移时更新数为 0，已有密文校验通过。
- 通过正在运行的 HTTP 服务验证师生登录、师生页面、JSON API 和 CSV 导出。
- CSV 仍可读，原有 HMAC 签名验证通过。
- 集成测试使用单独的临时数据库 schema，测试完成后已清理。

## 演示方法

1. 在项目目录执行下面的查询，查看数据库中的密文：

   ```bash
   docker compose exec -T db psql -U notesapp -d notesapp -c "SELECT id, comment FROM notes ORDER BY id LIMIT 3;"
   ```

2. 打开 <http://localhost:8080>，使用 `alice / alicepw` 登录。
   页面里的评论仍应正常显示原文，说明解密成功。

3. 使用 `prof.turing / teach123` 登录，新增或修改一条评论。
   再次查询数据库，确认保存的是 `aesgcm:v1:` 开头的密文。

4. 运行测试，演示包括篡改检测在内的验证结果：

   ```bash
   docker compose exec -T -e RUN_DB_TESTS=1 web python -m unittest discover -s tests -v
   ```

## 说明

这是数据库中评论的静态加密；授权用户查看页面或导出 CSV 时，应用会解密，
所以导出的 CSV 仍含原文。其他课程实验中故意保留的漏洞不属于这次作业的修改范围。

保留并单独备份 `.env` 中的 `COMMENT_ENCRYPTION_KEY`。不要在重启时重新生成它，
也不要将真实密钥上传到 GitHub；丢失该密钥后无法恢复旧评论。

API 参考：[cryptography AESGCM 官方文档](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)。
