import asyncio


async def run_start_command():
    # Windows 示例：使用 start 运行记事本
    command = 'echo 123'

    print(f"执行命令: {command}")

    # 创建子进程
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # 等待命令启动（start命令通常会立即完成）
    stdout, stderr = await process.communicate()

    print(f'命令已启动, PID: {process.pid}')
    print(stdout, stderr)


# 运行异步任务
asyncio.run(run_start_command())