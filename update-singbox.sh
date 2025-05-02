#!/bin/bash

set -e

URL=""
LOG_FILE="/var/log/update-singbox.log"
CONFIG_FILE="/etc/sing-box/config.json"
BACKUP_FILE="/etc/sing-box/config.json.bak"
TEMPLATE_FILE="./config.template.json"
DEBUG=0
MAX_LOG_SIZE=1048576

usage() {
  echo "Usage: $0 [-r remarks] [-i index] [-u url] [-d]"
  exit 1
}

rotate_logs() {
  [ -f "$LOG_FILE" ] || return
  log_size=$(stat -c%s "$LOG_FILE" 2>/dev/null) || {
    echo "Ошибка: Не удалось проверить размер $LOG_FILE" >&2
    exit 1
  }
  if [ "$log_size" -gt "$MAX_LOG_SIZE" ]; then
    for i in 5 4 3 2 1; do
      [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
    done
    mv "$LOG_FILE" "$LOG_FILE.1"
    touch "$LOG_FILE" || {
      echo "Ошибка: Не удалось создать $LOG_FILE" >&2
      exit 1
    }
  fi
}

log() {
  echo "[$(date '+%F %T')] $1" >> "$LOG_FILE"
}

debug_log() {
  [ "$DEBUG" -eq 1 ] && log "$1"
}

while getopts ":r:i:u:d" opt; do
  case $opt in
    r) SERVER_REMARKS="$OPTARG" ;;
    i) SERVER_INDEX="$OPTARG" ;;
    u) URL="$OPTARG" ;;
    d) DEBUG=1 ;;
    *) usage ;;
  esac
done

[ -z "$URL" ] && echo "Ошибка: Не указан URL (-u)" && usage

rotate_logs
touch "$LOG_FILE" 2>/dev/null || {
  echo "Ошибка: Нет прав на создание $LOG_FILE" >&2
  exit 1
}

log "=== Запуск обновления конфигурации Sing-box ==="

json_data=$(curl -s -H "User-Agent: ktor-client" "$URL") || {
  log "Ошибка: Не удалось получить конфигурацию с $URL"
  exit 1
}

[ -z "$json_data" ] && { log "Ошибка: Получена пустая конфигурация"; exit 1; }

if [ -n "$SERVER_REMARKS" ]; then
  config=$(echo "$json_data" | jq -r ".[] | select(.remarks == \"$SERVER_REMARKS\") | .outbounds[0]")
else
  SERVER_INDEX=${SERVER_INDEX:-0}
  config=$(echo "$json_data" | jq -r ".[$SERVER_INDEX] | .outbounds[0]")
fi

[ -z "$config" ] && { log "Ошибка: Не найдена конфигурация в outbounds"; exit 1; }

# Extract protocol
protocol=$(echo "$config" | jq -r '.protocol')

# Validate supported protocols
case "$protocol" in
  vless|shadowsocks|vmess|trojan|tuic|hysteria2) ;;
  *) log "Ошибка: Неподдерживаемый протокол: $protocol"; exit 1 ;;
esac

debug_log "Protocol: $protocol"

# Initialize outbound JSON
outbound_json='{
  "type": "'"$protocol"'",
  "tag": "proxy-out"
'

# Protocol-specific parameters
case "$protocol" in
  vless)
    # VLESS parameters
    uuid=$(echo "$config" | jq -r '.settings.vnext[0].users[0].id')
    server=$(echo "$config" | jq -r '.settings.vnext[0].address')
    port=$(echo "$config" | jq -r '.settings.vnext[0].port')
    flow=$(echo "$config" | jq -r '.settings.vnext[0].users[0].flow // empty')
    [ -z "$uuid" ] || [ -z "$server" ] || [ -z "$port" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для VLESS (uuid, server, port)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"uuid\": \"$uuid\""
    [ -n "$flow" ] && outbound_json="$outbound_json, \"flow\": \"$flow\""
    ;;
  shadowsocks)
    # Shadowsocks parameters
    server=$(echo "$config" | jq -r '.settings.servers[0].address')
    port=$(echo "$config" | jq -r '.settings.servers[0].port')
    method=$(echo "$config" | jq -r '.settings.servers[0].method')
    password=$(echo "$config" | jq -r '.settings.servers[0].password')
    plugin=$(echo "$config" | jq -r '.settings.servers[0].plugin // empty')
    plugin_opts=$(echo "$config" | jq -r '.settings.servers[0].plugin_opts // empty')
    [ -z "$server" ] || [ -z "$port" ] || [ -z "$method" ] || [ -z "$password" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для Shadowsocks (server, port, method, password)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"method\": \"$method\",
      \"password\": \"$password\""
    [ -n "$plugin" ] && outbound_json="$outbound_json, \"plugin\": \"$plugin\""
    [ -n "$plugin_opts" ] && outbound_json="$outbound_json, \"plugin_opts\": \"$plugin_opts\""
    ;;
  vmess)
    # VMess parameters
    uuid=$(echo "$config" | jq -r '.settings.vnext[0].users[0].id')
    server=$(echo "$config" | jq -r '.settings.vnext[0].address')
    port=$(echo "$config" | jq -r '.settings.vnext[0].port')
    security=$(echo "$config" | jq -r '.settings.vnext[0].users[0].security // "auto"')
    [ -z "$uuid" ] || [ -z "$server" ] || [ -z "$port" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для VMess (uuid, server, port)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"uuid\": \"$uuid\",
      \"security\": \"$security\""
    ;;
  trojan)
    # Trojan parameters
    server=$(echo "$config" | jq -r '.settings.servers[0].address')
    port=$(echo "$config" | jq -r '.settings.servers[0].port')
    password=$(echo "$config" | jq -r '.settings.servers[0].password')
    [ -z "$server" ] || [ -z "$port" ] || [ -z "$password" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для Trojan (server, port, password)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"password\": \"$password\""
    ;;
  tuic)
    # TUIC parameters
    server=$(echo "$config" | jq -r '.settings.servers[0].address')
    port=$(echo "$config" | jq -r '.settings.servers[0].port')
    uuid=$(echo "$config" | jq -r '.settings.servers[0].uuid')
    password=$(echo "$config" | jq -r '.settings.servers[0].password // empty')
    [ -z "$server" ] || [ -z "$port" ] || [ -z "$uuid" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для TUIC (server, port, uuid)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"uuid\": \"$uuid\""
    [ -n "$password" ] && outbound_json="$outbound_json, \"password\": \"$password\""
    ;;
  hysteria2)
    # Hysteria2 parameters
    server=$(echo "$config" | jq -r '.settings.servers[0].address')
    port=$(echo "$config" | jq -r '.settings.servers[0].port')
    password=$(echo "$config" | jq -r '.settings.servers[0].password')
    [ -z "$server" ] || [ -z "$port" ] || [ -z "$password" ] && {
      log "Ошибка: Отсутствуют обязательные параметры для Hysteria2 (server, port, password)"
      exit 1
    }
    outbound_json="$outbound_json,
      \"server\": \"$server\",
      \"server_port\": $port,
      \"password\": \"$password\""
    ;;
esac

# Security and transport settings (skip for shadowsocks)
if [ "$protocol" != "shadowsocks" ]; then
  security=$(echo "$config" | jq -r '.streamSettings.security // "none"')
  transport=$(echo "$config" | jq -r '.streamSettings.network // "tcp"')

  debug_log "Security: $security, Transport: $transport"

  # Validate transport compatibility
  case "$protocol" in
    vless)
      if [ "$security" = "reality" ]; then
        case "$transport" in
          ws|tuic|hysteria2|shadowtls)
            log "Ошибка: Транспорт $transport несовместим с reality"
            exit 1
            ;;
          tcp|grpc|http) ;;
          *) log "Ошибка: Неизвестный тип транспорта: $transport"; exit 1 ;;
        esac
      fi
      ;;
    vmess|trojan|tuic|hysteria2)
      if [ "$security" = "reality" ]; then
        log "Ошибка: Security reality несовместима с $protocol"
        exit 1
      fi
      ;;
  esac

  # Security-specific parameters
  case "$security" in
    reality)
      [ "$protocol" != "vless" ] && { log "Ошибка: Security reality поддерживается только для VLESS"; exit 1; }
      sni=$(echo "$config" | jq -r '.streamSettings.realitySettings.serverName // empty')
      pbk=$(echo "$config" | jq -r '.streamSettings.realitySettings.publicKey // empty')
      sid=$(echo "$config" | jq -r '.streamSettings.realitySettings.shortId // empty')
      fp=$(echo "$config" | jq -r '.streamSettings.realitySettings.fingerprint // "chrome"')
      [ -z "$pbk" ] || [ -z "$sid" ] && {
        log "Ошибка: Отсутствуют обязательные параметры для reality (publicKey, shortId)"
        exit 1
      }
      tls_json='{
        "enabled": true'
      [ -n "$sni" ] && tls_json="$tls_json, \"server_name\": \"$sni\""
      tls_json="$tls_json, \"reality\": {
          \"enabled\": true,
          \"public_key\": \"$pbk\",
          \"short_id\": \"$sid\"
        }"
      [ -n "$fp" ] && tls_json="$tls_json, \"utls\": { \"enabled\": true, \"fingerprint\": \"$fp\" }"
      tls_json="$tls_json }"
      outbound_json="$outbound_json, \"tls\": $tls_json"
      ;;
    tls)
      sni=$(echo "$config" | jq -r '.streamSettings.tlsSettings.serverName // empty')
      fp=$(echo "$config" | jq -r '.streamSettings.tlsSettings.fingerprint // "chrome"')
      alpn=$(echo "$config" | jq -r '.streamSettings.tlsSettings.alpn // empty')
      [ -z "$sni" ] && {
        log "Ошибка: Отсутствует serverName для tls"
        exit 1
      }
      tls_json='{
        "enabled": true,
        "server_name": "'"$sni"'"
      '
      [ -n "$fp" ] && tls_json="$tls_json, \"utls\": { \"enabled\": true, \"fingerprint\": \"$fp\" }"
      [ -n "$alpn" ] && tls_json="$tls_json, \"alpn\": \"$alpn\""
      tls_json="$tls_json }"
      outbound_json="$outbound_json, \"tls\": $tls_json"
      ;;
    none)
      # No TLS section
      ;;
    *)
      log "Ошибка: Неизвестный тип security: $security"
      exit 1
      ;;
  esac

  # Transport-specific parameters (omit for tcp with reality in VLESS)
  if [ "$security" != "reality" ] || [ "$transport" != "tcp" ] || [ "$protocol" != "vless" ]; then
    case "$transport" in
      ws)
        path=$(echo "$config" | jq -r '.streamSettings.wsSettings.path // empty')
        host=$(echo "$config" | jq -r '.streamSettings.wsSettings.headers.Host // empty')
        transport_json='{
          "type": "ws"'
        [ -n "$path" ] && transport_json="$transport_json, \"path\": \"$path\""
        [ -n "$host" ] && transport_json="$transport_json, \"headers\": { \"Host\": \"$host\" }"
        transport_json="$transport_json }"
        outbound_json="$outbound_json, \"transport\": $transport_json"
        ;;
      grpc)
        service_name=$(echo "$config" | jq -r '.streamSettings.grpcSettings.serviceName // empty')
        [ -z "$service_name" ] && {
          log "Ошибка: Отсутствует serviceName для grpc"
          exit 1
        }
        transport_json='{
          "type": "grpc",
          "service_name": "'"$service_name"'"
        }'
        outbound_json="$outbound_json, \"transport\": $transport_json"
        ;;
      http)
        path=$(echo "$config" | jq -r '.streamSettings.httpSettings.path // empty')
        host=$(echo "$config" | jq -r '.streamSettings.httpSettings.host // empty')
        transport_json='{
          "type": "http"'
        [ -n "$path" ] && transport_json="$transport_json, \"path\": \"$path\""
        [ -n "$host" ] && transport_json="$transport_json, \"headers\": { \"Host\": \"$host\" }"
        transport_json="$transport_json }"
        outbound_json="$outbound_json, \"transport\": $transport_json"
        ;;
      tcp)
        transport_json='{
          "type": "tcp"
        }'
        outbound_json="$outbound_json, \"transport\": $transport_json"
        ;;
      *)
        log "Ошибка: Неизвестный тип транспорта: $transport"
        exit 1
        ;;
    esac
  fi
else
  # For Shadowsocks, warn if security or transport is set
  security=$(echo "$config" | jq -r '.streamSettings.security // "none"')
  transport=$(echo "$config" | jq -r '.streamSettings.network // "tcp"')
  [ "$security" != "none" ] && log "Предупреждение: Security $security игнорируется для Shadowsocks"
  [ "$transport" != "tcp" ] && log "Предупреждение: Transport $transport игнорируется для Shadowsocks"
fi

outbound_json="$outbound_json }"

# Export variables for envsubst
export outbound_json

[ -f "$CONFIG_FILE" ] && cp "$CONFIG_FILE" "$BACKUP_FILE" && log "Создан бэкап $BACKUP_FILE"

envsubst < "$TEMPLATE_FILE" > "$CONFIG_FILE" || {
  log "Ошибка: Не удалось записать конфигурацию"
  exit 1
}

debug_log "Generated config: $(cat $CONFIG_FILE)"

log "Конфигурация обновлена для ${SERVER_REMARKS:-индекс $SERVER_INDEX}"

if systemctl is-active --quiet sing-box.service; then
  systemctl restart sing-box.service && log "Сервис перезапущен" || {
    log "Ошибка: Не удалось перезапустить сервис sing-box"
    exit 1
  }
else
  systemctl start sing-box.service && log "Сервис запущен" || {
    log "Ошибка: Не удалось запустить сервис sing-box"
    exit 1
  }
fi

log "Обновление завершено"