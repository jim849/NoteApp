# Class 7 — Fix the login

课程要求：<https://kristenpire.github.io/epita-security-labs/class7/fix-the-login/>

实验日期：2026-10-30。目标为本机 NotesApp。宿主机地址为
`http://localhost:8080`，验证脚本在 web 容器内访问同一服务的
`http://127.0.0.1:5000`。

## 1. 修改前的预测

- After all three fixes, will your old forged tokens still work? **NO.**
- Will a normal login still work? **YES.**

理由：固定 HS256 后，无签名的 `alg:none` 会被拒绝。更换签名密钥后，
用旧密钥 `s3cr3t` 生成的签名不再匹配。正常登录仍由服务器签发 Token，
签发和验证使用同一个新密钥，因此仍能通过。

## 2. 修复代码与密钥配置

实际提交的完整函数见 `web/app.py` 的 `verify_jwt()`。核心逻辑为：

```python
if header.get("alg") != "HS256":
    return None

signing_input = f"{h_b64}.{p_b64}".encode()
expected = _b64url(hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest())
if not hmac.compare_digest(expected, sig_b64):
    return None
return payload
```

先确认 header 和 payload 都是 JSON 对象，并拒绝格式错误的 Token。
算法名称必须精确匹配 `HS256`，不将客户端提供的算法名称转换成小写后接受。
签名检查使用原始的两个编码分段，保留 `hmac.compare_digest` 比较。

`web/app.py` 现在要求显式配置密钥：

```python
JWT_SECRET = os.environ["JWT_SECRET"]
```

`docker-compose.yml` 从本地环境读取，变量缺失或为空时拒绝启动：

```yaml
JWT_SECRET: ${JWT_SECRET:?请在.env中设置随机生成的JWT_SECRET}
```

本次使用 `secrets.token_urlsafe(32)` 从 32 个随机字节生成独立密钥，
保存到被 Git 忽略的本地 `.env`。报告不包含真实密钥。
已有评论加密密钥与导出签名密钥继续保留，未用于 JWT 签名。
`web/Dockerfile` 中残留的旧 JWT 密钥示例也已移除。
生产环境应从 secrets store 注入密钥，不把真实值提交到版本库。

## 3. 用户提供的原始 Token 与核对

本次最终复验直接使用用户在本对话中提供的完整原始字符串，不重新编码、修改身份或生成替代 Token。
Token 保存到被 Git 忽略的 `.jwt-lab-tokens/`，每个文件权限为 0600。
文件仅添加末尾换行，发请求时去掉文件首尾空白；无签名 Token 的末尾 `.` 保留。

| 用户提供的顺序 | 本地文件 | header.alg | payload | 核对结果 |
| --- | --- | --- | --- | --- |
| 1 | `original-student.jwt` | `HS256` | `user_id:6, username:alice, role:student` | 原始学生 Token，签名与旧密钥 `s3cr3t` 匹配 |
| 2 | `original-none.jwt` | `none` | `user_id:9999, username:attacker, role:teacher` | 无签名伪造，第三段为空 |
| 3 | `original-signed.jwt` | `HS256` | `user_id:6, username:alice, role:teacher` | 教师身份伪造，签名与旧密钥 `s3cr3t` 匹配 |

原始字符串（不含文件末尾换行）的 SHA-256，供核对材料是否相同：

```text
original-student.jwt  9d605777a10aa9e40f66eb039bcaff654961f2f5ead1f4d9c81cdc5b964b1567
original-none.jwt     48eab22bb220b91bf46802d006677f5ad190770c5bd087df2fe483da64481944
original-signed.jwt   7a94729b0dcafe5fbacf5a340b5b4901f965b320b70b8aa5ec97298d377f2691
```

所有 Bearer 请求均不携带 Cookie，避免已有 Session 干扰结果。
最终提交证明以第二、第三条原始 Token 的本次 HTTP 复验为准。
第一条用于离线核对原始学生身份与旧密钥签名，未在本次 HTTP 检查中发送。
自动化测试中的人工测试数据仅用于代码回归，不代替原始课堂 Token。

## 4. 重复原始 Token 验证

在项目目录运行：

```sh
docker compose exec -T web python /host/verify_login_fix.py --stage fixed \
  --none-token-file /host/.jwt-lab-tokens/original-none.jwt \
  --signed-token-file /host/.jwt-lab-tokens/original-signed.jwt
```

本次实际执行输出：

```text
Stage: fixed; target: http://127.0.0.1:5000
Samples: user-supplied original Class 6 tokens; no cookies on Bearer requests.
No credentials: HTTP 401 {
  "error": "unauthorized"
}
Forged none: HTTP 401 {
  "error": "unauthorized"
}
Forged HS256: HTTP 401 {
  "error": "unauthorized"
}
Real alice login: HTTP 200 dashboard contains My grades
Fresh genuine JWT, no cookies: HTTP 200; student=alice; note_id=2
PASS: all checks match the selected stage.
```

正常登录使用课程测试账户 `alice` / `alicepw`，从 dashboard 取得服务器新签发的 Token，
然后不带 Cookie 读取 Alice 自己的 note 2，返回 HTTP 200 与 `student: alice`。
之前运行的完整自动化测试共 22 项，全部通过，包括 JWT、评论加密和 PostgreSQL 集成检查。

## 5. 范围说明

本次完成的是课程指定的 JWT 算法限制与密钥更换。
`/api/notes/<id>` 原有的对象归属检查缺失（flaw #7 / IDOR）仍是独立问题；
不能因为两种伪造被拒绝，就推断整个应用的权限控制已经安全。
更换 JWT 密钥也不会自动清除现有 Flask Session。手动验证时先退出再登录；
测试伪造时不携带 Cookie。

## 6. 最终 Audit

```text
LOGIN FIX — NotesApp flaw #4 (auth) closed
  Fix 1:  verify_jwt rejects alg:none and pins algorithm to HS256
  Fix 2:  JWT_SECRET is long + random, read from the environment (no s3cr3t, no default)
  Proof:  original alg:none token      -> HTTP 401 unauthorized
          original s3cr3t-signed token -> HTTP 401 unauthorized
          real alice login            -> works (HTTP 200 dashboard)
          fresh genuine JWT           -> HTTP 200, Alice's own note, no cookies
```
