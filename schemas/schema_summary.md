# Complete Sing-Box Schema Summary

Generated from documentation analysis.

## Outbound Protocols

Total: 19

### anytls
Fields: 0


### block
Fields: 2

- type: str ❌
- tag: str ❌

### direct
Fields: 0


### dns
Fields: 2

- type: str ❌
- tag: str ❌

### http
Fields: 0


### hysteria
Fields: 0


### hysteria2
Fields: 0


### selector
Fields: 5

- type: str ❌
- tag: str ❌
- outbounds: list ❌
- default: str ❌
- interrupt_exist_connections: bool ❌

### shadowsocks
Fields: 0


### shadowtls
Fields: 2

- Value: Protocol Version ❌
- [ShadowTLS v2](https://github.com/ihciah/shadow-tls/blob/master/docs/protocol-en.md#v2):  ❌

### socks
Fields: 0


### ssh
Fields: 0


### tor
Fields: 0


### trojan
Fields: 0


### tuic
Fields: 1

- Mode: Description ❌

### urltest
Fields: 8

- type: str ❌
- tag: str ❌
- outbounds: list ❌
- url: str ❌
- interval: str ❌
- tolerance: int ❌
- idle_timeout: str ❌
- interrupt_exist_connections: bool ❌

### vless
Fields: 2

- Encoding: Description ❌
- Supported by v2ray 5+:  ❌

### vmess
Fields: 4

- Alter ID: Description ❌
- Use legacy protocol:  ❌
- Encoding: Description ❌
- Supported by v2ray 5+:  ❌

### wireguard
Fields: 0


## Inbound Protocols

Total: 17

### anytls
Fields: 0


### direct
Fields: 0


### http
Fields: 0


### hysteria
Fields: 0


### hysteria2
Fields: 6

- Scheme: Example ❌
- -------------------------: -------------------- ❌
- As a file server: `directory` ❌
- Conflict with `masquerade.type`.

A 404 page will be returned if masquerade is not configured.

#### masquerade.type

HTTP3 server behavior (Object configuration) when authentication fails.: Type ❌
- ----------: ----------------------------- ❌
- `url`, `rewrite_host`:  ❌

### mixed
Fields: 0


### naive
Fields: 0


### redirect
Fields: 0


### shadowsocks
Fields: 11

- Method: Key Length ❌
- 32:  ❌
- none: / ❌
- /:  ❌
- xchacha20-ietf-poly1305: / ❌
- method: str ❌
- password: str ❌
- users: list ❌
- multiplex: dict ❌
- type: str ❌
- destinations: list ❌

### shadowtls
Fields: 2

- Value: Protocol Version ❌
- [ShadowTLS v2](https://github.com/ihciah/shadow-tls/blob/master/docs/protocol-en.md#v2):  ❌

### socks
Fields: 0


### tproxy
Fields: 0


### trojan
Fields: 0


### tuic
Fields: 0


### tun
Fields: 3

- Stack: Description ❌
- Perform L3 to L4 translation using [gVisor](https://github.com/google/gvisor)'s virtual network stack:  ❌
- Common user: ID ❌

### vless
Fields: 0


### vmess
Fields: 1

- Alter ID: Description ❌

