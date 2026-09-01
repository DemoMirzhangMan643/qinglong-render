#!/bin/bash
# 青龙面板 Render 启动脚本（接管镜像默认入口 docker-entrypoint.sh）

# 1. 后台初始化：等待面板就绪 → 自动初始化 → 同步 Cookie → 拉取脚本仓库
(
  QL_USER="${QL_USERNAME:-admin}"
  QL_PASS="${QL_PASSWORD:-Qinglong@2026}"

  # 1.1 等待后端 API 就绪（最长约 10 分钟）
  j=0
  while [ $j -lt 60 ]; do
    curl -s -o /dev/null http://127.0.0.1:5700/api/system && break
    sleep 10
    j=$((j+1))
  done
  echo "[entrypoint] 面板 API 已就绪"

  # 1.2 首次启动自动初始化面板（免费套餐重新部署会重置磁盘，这里自动设置账号密码）
  SYS_JSON=$(curl -s http://127.0.0.1:5700/api/system)
  if echo "$SYS_JSON" | grep -q '"isInitialized":false'; then
    curl -s -X PUT http://127.0.0.1:5700/api/user/init \
      -H 'Content-Type: application/json' \
      -d "{\"username\":\"$QL_USER\",\"password\":\"$QL_PASS\"}" >/dev/null
    echo "[entrypoint] 面板已自动初始化（账号: $QL_USER 密码: $QL_PASS）"
  else
    echo "[entrypoint] 面板已初始化过"
  fi

  # 1.3 等待 auth.json 出现（初始化完成后即生成，最长约 5 分钟）
  i=0
  while [ $i -lt 30 ]; do
    [ -f /ql/data/config/auth.json ] && break
    sleep 10
    i=$((i+1))
  done
  echo "[entrypoint] 面板已就绪，开始初始化脚本"

  # 1.4 同步 Render 环境变量中的 Cookie 到青龙 config.sh（可选入口）
  #     也可以不用这里，直接用面板里的【京东扫码获取Cookie】任务自动写入
  for VAR in JD_COOKIE JD_WSCK; do
    val=$(printenv $VAR)
    if [ -n "$val" ]; then
      sed -i "/^export $VAR=/d" /ql/data/config/config.sh 2>/dev/null
      echo "export $VAR=\"$val\"" >> /ql/data/config/config.sh
      echo "[entrypoint] 已同步环境变量 $VAR"
    fi
  done

  # 1.5 拉取脚本仓库（失败自动重试 3 次）
  pull() {
    local n=0
    while [ $n -lt 3 ]; do
      if "$@" >/dev/null 2>&1; then
        echo "[entrypoint] 拉取成功: $1 $2 $3"
        return 0
      fi
      n=$((n+1))
      sleep 30
    done
    echo "[entrypoint] 拉取失败(已重试3次): $1 $2 $3"
  }

  # 公告脚本仓库（微信小程序/日常签到等）
  pull ql repo https://github.com/smallfawn/QLScriptPublic.git
  # wskey 自动转换（Cookie 过期自动续期：JD_WSCK → JD_COOKIE）
  pull ql repo https://github.com/Zy143L/wskey.git "wskey"
  # 京豆/京东活动脚本合集（京豆签到、种豆得豆、农场等，任务名均为中文）
  pull ql repo https://github.com/shufflewzc/faker2.git "jd_|jx_|getJDCookie" "activity|backUp" "^jd[^_]|USER|function|sendNotify|utils|JDJR|jxAlgo|depend"
  # 京东扫码获取Cookie（扫码后自动写入 JD_COOKIE，手动运行即可）
  pull ql raw https://raw.githubusercontent.com/DemoMirzhangMan643/qinglong-render/main/scripts/jd_cookie_scan.py

  echo "[entrypoint] 所有脚本仓库初始化完成"
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
