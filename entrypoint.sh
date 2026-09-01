#!/bin/bash
# 青龙面板 Render 启动脚本（接管镜像默认入口 docker-entrypoint.sh）

# 1. 后台等待面板初始化完成后，自动拉取脚本仓库（失败重试，共约 10 分钟）
(
  i=0
  while [ $i -lt 60 ]; do
    sleep 10
    if ql repo https://github.com/smallfawn/QLScriptPublic.git >/dev/null 2>&1; then
      echo "[entrypoint] 脚本仓库拉取成功"
      break
    fi
    i=$((i+1))
  done
) &

# 2. 自保活：定期访问公网地址，防止免费套餐因无流量休眠（休眠会清空磁盘数据）
(
  if [ -n "$RENDER_EXTERNAL_URL" ]; then
    sleep 600
    while true; do
      curl -s -o /dev/null "$RENDER_EXTERNAL_URL" 2>/dev/null || true
      sleep 600
    done
  fi
) &

# 3. 启动青龙面板（转发到镜像原始入口）
exec /bin/bash /ql/docker/docker-entrypoint.sh
