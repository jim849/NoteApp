# INJECTION FIX — NotesApp flaws #8 and #9

我检查了 NotesApp 的登录和管理员 ping 功能，保留了已经完成的 SQL 注入修复，并修复了 ping 的命令注入。两处采用同一个原则：把用户输入作为数据传递，不拼接成解释器执行的命令。

## SQL injection — login()

原始漏洞版本将用户名和密码拼接到 SQL。输入用户名 `admin' -- `、密码 `anything` 时，单引号提前结束用户名字符串，`--` 注释掉后面的密码条件，因此原始查询可以绕过密码检查。

当前登录实现已经在提交 `c968e2b` 中修复。我保留参数化用户名查询，以及查询后的 Argon2 密码验证：

```python
cur.execute(
    "SELECT id, username, password, role "
    "FROM users WHERE username = %s",
    (username,),
)
```

同样的 `admin' -- ` 现在作为完整用户名传递，不会改变 SQL 结构。在种子账户中不存在这个用户名，预期结果是登录失败，无法进入管理员页面。密码继续单独验证，不改回明文 SQL 比较。

## Command injection — admin_ping()

原始代码将 `host` 拼接到 `ping -c 1 ` 后，再使用 `shell=True` 执行。输入 `127.0.0.1; id` 时，shell 会把分号解释为命令分隔符，在 ping 后执行 `id`；`127.0.0.1; id; head -2 /etc/passwd` 同理会追加两条命令。

我删除了字符串拼接和 `shell=True`，改成：

```python
result = subprocess.run(
    ["ping", "-c", "1", "--", host],
    capture_output=True, text=True, timeout=10,
)
```

`host` 始终是一个参数，没有 shell 解释分号或命令替换。`--` 表示选项结束，防止输入被当成 ping 选项。相同攻击输入现在只会成为无效主机名，预期不会产生 `id` 或读取 `/etc/passwd` 的输出。普通 `127.0.0.1` 仍按原有参数传给 ping。

## 我的验证结果

我运行了针对实际路由函数体的隔离回归测试，数据库、密码验证器和子进程调用使用测试替身：

```sh
python3 -m unittest discover -s web/tests -p test_injection.py -v
```

结果：**6 项测试全部通过**。

| 检查 | 结果 |
| --- | --- |
| SQL 注入用户名与 SQL 语句分开传递；没有匹配用户时不建立会话 | 通过 |
| Alice 登录流程调用 Argon2 验证，验证成功后建立学生会话 | 通过 |
| 已有明文账户的错误密码不能登录 | 通过 |
| 分号、命令替换和以短横线开头的输入均作为一个参数传递，不启用 shell | 通过 |
| 普通 `127.0.0.1` 参数和 ping 输出保留 | 通过 |
| 非管理员不能触发子进程 | 通过 |

上述结果覆盖路由逻辑的隔离回归测试，不包含 PostgreSQL 和容器内 ping 的端到端验证。

我完成的代码修复是：SQL 使用参数化查询，系统命令使用参数列表。输入中的标点只作为数据，不再获得命令语法的作用。
