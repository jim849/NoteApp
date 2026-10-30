# Class 6 JWT 实验记录

## 实验目标与记录来源

在本地 NotesApp 教学项目中完成两部分实验：

1. **Part 1 — Unsigned JWT Forgery**：不使用签名密钥，构造声明教师身份的无签名 JWT，尝试读取另一名学生的成绩。
2. **Part 2 — Crack the Secret and Sign a Teacher Token**：对原始 JWT 进行弱密钥字典猜测，再用恢复的密钥签发声明教师身份的 HS256 JWT。

本文依据根目录的 `forged-token-finding.txt` 补全实验过程和结果，并对照 `web/app.py`、`docker-compose.yml`、`db/init.sql` 与 `jwt-secrets.txt` 核对代码逻辑和静态数据。下文的“记录结果”来自该实验记录；本次整理未重新启动服务或发送 HTTP 请求。

来源文件未保存完整原始 JWT、请求命令、HTTP 状态码、响应头或原始响应体，因此不补写这些证据。漏洞修复与 MFA 不在本次实验记录范围内。

## 完成清单

- [x] 检查 JWT 验证逻辑与成绩接口。
- [x] 整理 Part 1 的实验前预测及理由。
- [x] 记录原始学生 JWT 的 header 与 payload。
- [x] 根据来源记录补全无签名 JWT 的构造方式与读取结果。
- [x] 根据来源记录补全字典猜测、弱密钥恢复与 HS256 伪造结果。
- [x] 核对字典中的密钥位置与随机密钥搜索空间估算。
- [x] 区分 JWT 认证缺陷、成绩接口授权缺陷与教师页面的 Session 校验。
- [ ] 补存实际运行时的 API 地址、无凭证对照请求，以及两次伪造请求的完整 HTTP 证据。

## 实验环境与目标接口

| 项目 | 内容 |
| --- | --- |
| 应用 | 本地 NotesApp 教学项目 |
| 默认 API 地址 | 按 `docker-compose.yml` 的端口映射为 `http://localhost:8080`；来源记录未注明实测地址 |
| 目标接口 | `GET /api/notes/3` |
| 原始身份 | `alice`，`user_id: 6`，`role: student` |
| 目标记录 | 初始化数据中的第 3 条成绩，属于学生 `bob`，课程为 `Mathematics` |

接口使用 `Authorization: Bearer <JWT>` 接收 Token，也可能回退到现有 Session。复现时应不携带 Cookie，避免现有登录态影响判断。

无 Cookie、无 Bearer Token 时，按 `current_identity()` 和 `api_notes()` 的代码，预期返回 HTTP `401`，内容为 `{"error":"unauthorized"}`。来源记录未包含该对照请求，因此这里仅记录代码预期。

## Part 1 — 无签名 JWT 伪造

### 实验前预测

**问题：服务器会接受完全没有签名的 Token 吗？**

**预测：YES。**

理由：`web/app.py` 中的 `verify_jwt()` 读取 JWT header 的 `alg` 字段。当算法为 `none` 时，函数直接返回 payload，没有验证签名。因此，按当前代码逻辑，一个格式正确、payload 非空的无签名 JWT 预计会被接受。

### Step 1 — 检查原始 JWT

来源记录中的原始 Token 解码结果如下。

Header：

```json
{"alg":"HS256","typ":"JWT"}
```

Payload：

```json
{"user_id":6,"username":"alice","role":"student"}
```

Payload 表示 Alice 是学生。JWT 的 header 和 payload 使用 Base64URL 编码，没有加密，解码它们不需要密钥。修改内容后能否被接受，取决于服务器是否正确校验签名。

### Steps 2–4 — 构造并发送无签名 Token

将 header 的算法改为 `none`，将 payload 中的角色改为 `teacher`，签名段留空。

Header：

```json
{"alg":"none","typ":"JWT"}
```

Payload 构造示意（来源记录未逐字保存本次无签名 Token 的完整 payload）：

```json
{"user_id":6,"username":"alice","role":"teacher"}
```

Token 结构为：

```text
Base64URL(header).Base64URL(payload).
```

编码时去掉 Base64URL 的尾部 `=` 填充，保留 Token 最后的点，使其仍包含三个分段，第三段为空。使用该 Token 作为 Bearer Token 请求 `/api/notes/3`。

**记录结果：请求成功，读取到 Bob 的成绩。**

| 字段 | 来源记录中的值 |
| --- | --- |
| 学生 | `bob` |
| 课程 | `Mathematics` |
| 成绩 | `12.6` |
| 评论 | `Solid work, keep it up.` |

来源记录未给出实际 HTTP 状态码或原始响应体。若当前代码成功返回该记录，通常会产生 HTTP `200`；这属于代码预期，不能代替实测状态码。

## Part 2 — 破解弱密钥并签发教师 Token

### 实验前预测

**预测：如果 HS256 签名密钥很弱，即使拒绝 `alg: none`，仍可能伪造 Token。**

可以对 Alice 的原始 Token 进行离线字典猜测，找到匹配签名的密钥，再用它为修改后的 payload 生成有效的 HS256 签名。

### Step 5 — 字典猜测签名密钥

来源记录使用 `jwt-secrets.txt` 中的候选词，逐一计算 Alice 原始 JWT 的 HMAC-SHA256 签名，并与原始签名比较。

计算时保留原始 Token 的前两个编码分段，签名输入为：

```text
original_header_base64url.original_payload_base64url
```

对该输入使用候选密钥计算 HMAC-SHA256，再将结果编码为不带 `=` 填充的 Base64URL，与原始 Token 的第三段比较。不能先解码再重新序列化 header 或 payload，否则空格等变化可能改变签名输入。

**记录结果：匹配的密钥为 `s3cr3t`，位于字典第 8 行。**

本次整理确认，当前 `jwt-secrets.txt` 共 15 个候选词，`s3cr3t` 确实排第 8；它也与 `docker-compose.yml` 中的 `JWT_SECRET` 和 `web/app.py` 的默认值一致。由于来源记录未保留完整原始 Token，本次未重新执行签名匹配；配置核对不能代替该实验步骤。

#### 随机密钥的搜索空间估算

假设每个位置从 95 个字符中独立、均匀随机选择，一个 32 字符密钥共有：

```text
95^32 ≈ 1.94 × 10^63 种组合
```

若每秒尝试 `10^9` 个候选密钥，遍历整个空间约需：

```text
95^32 / (10^9 × 365.25 × 24 × 3600) ≈ 6.14 × 10^46 年
```

这是给定猜测速度下遍历全空间的理论估算；平均搜索时间约为一半。它依赖均匀随机的假设，不能套用于可被短字典命中的 `s3cr3t`。

### Step 6 — 使用恢复的密钥签发 Token

保持 HS256 算法，保留 Alice 的身份字段，仅将角色从 `student` 改为 `teacher`。

Header：

```json
{"alg":"HS256","typ":"JWT"}
```

Payload：

```json
{"user_id":6,"username":"alice","role":"teacher"}
```

使用恢复的密钥 `s3cr3t`，对新 header 与 payload 的编码分段计算 HMAC-SHA256 签名，组成完整 JWT，再作为 Bearer Token 请求 `/api/notes/3`。

**记录结果：请求成功，再次读取到 Bob 的 Mathematics 成绩 `12.6` 和评论 `Solid work, keep it up.`。** 来源记录同样未保留实际 HTTP 状态码与原始响应体。

仅拒绝 `alg: none` 无法阻止这次伪造，因为该 Token 使用 HS256，签名由恢复的密钥正确计算，能通过当前签名校验。

## 结果解释与证据边界

两次实验涉及相互关联的缺陷：

1. **JWT 认证缺陷（flaw #4）**：`verify_jwt()` 接受 `alg: none`，允许无签名 payload 成为认证身份；HS256 密钥又可被字典猜中，使攻击者能够生成有效签名。
2. **成绩接口授权缺陷（flaw #7，IDOR）**：`/api/notes/<note_id>` 只要求存在认证身份，没有检查成绩归属，也没有要求教师角色。因此，持有有效学生身份的请求按代码逻辑也能读取其他学生的成绩。

伪造 Token 的 payload 声明了教师角色，来源记录表明该 Token 被接受并用于读取数据。但这个接口没有执行教师角色校验，所以不能仅凭读取成功就断言“教师权限校验被绕过”或“已登录教师页面”。`/teacher` 使用 `login_required("teacher")` 检查 Session，Bearer JWT 被 API 接受并不等同于获得该页面的教师 Session。

当前初始化 SQL 中的目标记录与来源记录一致；实际运行数据库可能发生变化。本文保留历史实验结果，不将初始化数据视为新一次 HTTP 验证。

## Final Finding

**FORGED-TOKEN FINDING — NotesApp flaw #4 (auth)，结合 flaw #7 (IDOR)**

- **读取内容**：通过 `/api/notes/3` 读取 Bob 的 Mathematics 成绩 `12.6` 与评论 `Solid work, keep it up.`。
- **Break 1**：使用 `alg: none`、空签名且声明 `role: teacher` 的 JWT，成功读取目标记录。
- **Break 2**：用字典恢复 HS256 密钥 `s3cr3t`，保留 Alice 的身份并将角色改为 `teacher`，签发的新 Token 同样成功读取目标记录。
- **原因**：服务器接受客户端声明的无签名算法，签名密钥容易猜测，且成绩 API 缺少对象归属与角色授权检查。
- **证据范围**：以上成功结果来自 `forged-token-finding.txt`；代码、配置、初始化数据、字典位置与数学估算已核对，完整 HTTP 证据仍待补存。
